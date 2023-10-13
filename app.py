import os
import time

import dotenv
import boto3
import ssl

import awswrangler as wr

from awswrangler import postgresql
from flask import Flask, request, Response, make_response, Blueprint
from flask_cors import CORS
from botocore.config import Config
from langchain import SQLDatabase

from utils.llm import get_llm_client
from utils.athena import get_athena_client, get_table_info, format_query_result
from utils.prompt import ATHENA_PROMPT, POSTGRES_PROMPT
# from utils.secretsmanager import generate_db_uri

import logging

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logging.info('Admin logged in')


app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

dotenv.load_dotenv()

athena_client = get_athena_client()

# db_uri = generate_db_uri(os.getenv("RDS_SECRETS_MANAGER_ARN"))
# db = SQLDatabase.from_uri(db_uri)
# rds_table_info = db.table_info

api_bp = Blueprint("api", __name__, url_prefix="/api")
v1_bp = Blueprint("v1", __name__, url_prefix="/v1")


@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        res = Response()
        res.headers['X-Content-Type-Options'] = '*'
        return res


@api_bp.route("/ping", methods=["GET"])
def ping():
    return "pong"


@v1_bp.route("/athena/health", methods=["GET"])
def health():
    try:
        athena_client.list_data_catalogs()
    except Exception as error:
        return make_response({"error": error}, 400)
    return make_response({"health": "ok"}, 200)


@v1_bp.route("/athena/catalog", methods=["GET"])
def get_data_catalog():
    try:
        data_catalogs = athena_client.list_data_catalogs()
        # print("athena client region: ", athena_client.get_region())
    except Exception as error:
        return make_response({"error": error}, 400)
    return make_response({
        "catalogs": [catalog["CatalogName"] for catalog in data_catalogs["DataCatalogsSummary"]]
    }, 200)


@v1_bp.route("/athena/database/<catalog_name>", methods=["GET"])
def get_databases(catalog_name):
    try:
        databases = athena_client.list_databases(CatalogName=catalog_name)
    except Exception as error:
        return make_response({"error": error}, 400)
    return make_response({
        "databases": [database["Name"] for database in databases["DatabaseList"]]
    }, 200)















@v1_bp.route("/inference/explanation", methods=["POST"])
def explanation_inference():
    req = request.get_json()

    body = {
        "catalog_name": req.get("CatalogName"),
        "database_name": req.get("DatabaseName"),
        "prompt": req.get("prompt"),
        "qid": req.get("qid")
    }

    for key, value in body.items():
        if value is None:
            return make_response({
                "error": f"{key} not provided!"
            }, 400)

    while True:
        finish_state = athena_client.get_query_execution(QueryExecutionId=body["qid"])[
            "QueryExecution"
        ]["Status"]["State"]
        if finish_state == "RUNNING" or finish_state == "QUEUED":
            time.sleep(2)
        else:
            break

    try:
        query_result = athena_client.get_query_results(
            QueryExecutionId=body["qid"]
        )
        formatted_query_result = format_query_result(query_result)
        # explainer_kwargs = {
        #     "input": body["prompt"],
        #     "result": formatted_query_result
        # }
        # explanation = llm.predict(EXPLAINER_PROMPT.format_prompt(**explainer_kwargs).to_string())
    except BaseException as error:
        return make_response({"error": error}, 400)

    return make_response({
        "explanation": None,
        "data": [row.split(",") for row in formatted_query_result.strip().split("\n")]
    })


# input: Human language ; output: SQL query.
@v1_bp.route("/inference/sql", methods=["POST"])
def sql_inference():
    req = request.get_json()

    prompt = req["prompt"]

    if not prompt:
        return make_response({
            "error": "Prompt not provided!"
        }, 400)

    data_information = {
        "catalog_name": req.get("CatalogName"),
        "database_name": req.get("DatabaseName")
    }

    table_info = get_table_info(athena_client, data_information, logging)

    sql_gen_kwargs = {
        "input": prompt,
        "table_info": table_info,
        "top_k": 10,
    }

    prompt = ATHENA_PROMPT.format_prompt(**sql_gen_kwargs).to_string()

    llm_client = get_llm_client()

    try:
        query = llm_client.generate_sql(prompt)
        logging.info("------------------------------------------\nGenerated Athena SQL: \n" + query)
        logging.info("------------------------------------------")

        query_execution = athena_client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={
                'Database': data_information["database_name"],
                'Catalog': data_information["catalog_name"]
            },
            ResultConfiguration={
                'OutputLocation': 's3://pinpoint-analytics-demo-1/demonql/'
            },
            ResultReuseConfiguration={
                "ResultReuseByAgeConfiguration": {
                    'Enabled': True,
                    'MaxAgeInMinutes': 5000
                }
            }
        )
        qid = query_execution["QueryExecutionId"]

    except BaseException as error:
        return make_response({"error": error}, 400)

    return make_response({
        "qid": qid,
        "query": query,
    }, 200)


















# # input:human language ; output: SQL query
# @v1_bp.route("/postgres/inference", methods=["POST"])
# def postgres_sql_inference():
#     req = request.get_json()

#     prompt = req["prompt"]

#     if not prompt:
#         return make_response({
#             "error": "Prompt not provided!"
#         }, 400)

#     prompt = POSTGRES_PROMPT.format_prompt(input=prompt, table_info=rds_table_info, top_k=10).to_string()

#     try:
#         llm_client = get_llm_client()
#         query = llm_client.generate_sql(prompt)
#     except BaseException as error:
#         return make_response({"error": error}, 400)

#     return make_response({
#         "query": query,
#     }, 200)


# # input: SQL query  ; output: result after exec that SQL query via Database
# @v1_bp.route("/postgres/execute", methods=["POST"])
# def postgres_sql_execution():
#     req = request.get_json()

#     body = {
#         "query": req["query"],
#     }

#     for k in body:
#         if not body[k]:
#             return make_response({
#                 "error": f"{k} not provided!"
#             }, 400)

#     session = boto3.Session(region_name="us-west-2")

#     ssl_context = ssl.create_default_context()
#     ssl_context.check_hostname = False
#     ssl_context.verify_mode = ssl.CERT_NONE

#     con_postgresql = postgresql.connect(
#         secret_id=os.getenv("RDS_SECRETS_MANAGER_ARN"),
#         boto3_session=session,
#         ssl_context=ssl_context
#     )

#     result = wr.postgresql.read_sql_query(body["query"], con=con_postgresql)

#     return make_response({
#         "data": [row.split(',') for row in result.to_csv(index=False).splitlines()]
#     }, 200)








api_bp.register_blueprint(v1_bp)
app.register_blueprint(api_bp)
