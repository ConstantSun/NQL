import json

import boto3
from botocore.config import Config


def generate_db_uri(secret_id: str):
    config = Config(region_name="us-west-2")
    sm_client = boto3.client("secretsmanager", config=config)
    data = json.loads(sm_client.get_secret_value(SecretId=secret_id)["SecretString"])
    return f"postgresql+psycopg2://{data['username']}:{data['password']}@{data['host']}:{data['port']}/{data['dbname']}"
