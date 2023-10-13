import os

import boto3


def get_athena_client() -> boto3:
    sts_envs = {
        "ATHENA_STS_ROLE_ARN": os.getenv("ATHENA_STS_ROLE_ARN"),
        "ATHENA_EXTERNAL_ACCOUNT_ID": os.getenv("ATHENA_EXTERNAL_ACCOUNT_ID"),
    }

    boto3_kwargs = {
        "region_name": os.getenv("ATHENA_REGION")
    }

    use_sts = all([sts_envs[env] is not None for env in sts_envs])

    if use_sts:
        session = boto3.Session()
        sts_client = session.client("sts")
        response = sts_client.assume_role(
            RoleArn=os.getenv("ATHENA_STS_ROLE_ARN"),
            RoleSessionName="testSessionName",
            ExternalId=os.getenv("ATHENA_EXTERNAL_ACCOUNT_ID")
        )
        boto3_kwargs["aws_access_key_id"] = response["Credentials"]["AccessKeyId"]
        boto3_kwargs["aws_secret_access_key"] = response["Credentials"]["SecretAccessKey"]
        boto3_kwargs["aws_session_token"] = response["Credentials"]["SessionToken"]

    athena_client = boto3.client(
        "athena",
        **boto3_kwargs
    )

    return athena_client


def format_query_result(query_result):
    result = ""
    for row in query_result["ResultSet"]["Rows"]:
        data = row["Data"]
        data_row = ",".join([d["VarCharValue"] if "VarCharValue" in d else " " for d in data])
        result += data_row + "\n"
    return result


def get_table_info(athena_client, data_information, logging):
    for key, value in data_information.items():
        if value is None:
            raise Exception(f"{value} not provided!")

    metadata = athena_client.list_table_metadata(
        CatalogName=data_information["catalog_name"],
        DatabaseName=data_information["database_name"]
    )

    new_line = '\n'
    table_info = ""
    for table in metadata["TableMetadataList"]:
        if (table_name := table["Name"]) in [
            "vw_test",
            "dim_category_tree_identifier",
            "dim_category_tree_product"
        ]:
            continue
        columns = table["Columns"]
        create_table_sql = f"""CREATE EXTERNAL TABLE `{table_name}`(
{new_line.join([f"`{col['Name']}`   {col['Type']}" for col in columns])}
)"""
        table_info += f"{create_table_sql}{new_line}"

    return table_info

