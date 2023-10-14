import os
import logging
import boto3
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


def get_bedrock_client() -> boto3:
    sts_envs = {
        "STS_ROLE_ARN": os.getenv("STS_ROLE_ARN"),
        "EXTERNAL_ACCOUNT_ID": os.getenv("EXTERNAL_ACCOUNT_ID"),
    }

    boto3_kwargs = {
        "region_name": os.getenv("BEDROCK_REGION")
    }

    use_sts = all([ len(sts_envs[env]) > 0 for env in sts_envs])
    logging.info("----------------- use_sts :")
    logging.info(use_sts)
    logging.info("-----------------...")


    if use_sts:
        session = boto3.Session()
        sts_client = session.client("sts")
        response = sts_client.assume_role(
            RoleArn=os.getenv("STS_ROLE_ARN"),
            RoleSessionName="testSessionName",
            ExternalId=os.getenv("EXTERNAL_ACCOUNT_ID")
        )
        boto3_kwargs["aws_access_key_id"] = response["Credentials"]["AccessKeyId"]
        boto3_kwargs["aws_secret_access_key"] = response["Credentials"]["SecretAccessKey"]
        boto3_kwargs["aws_session_token"] = response["Credentials"]["SessionToken"]

    bedrock_region = os.getenv("BEDROCK_REGION")
    bedrock_client = boto3.client(
        "bedrock",
        **boto3_kwargs,
        endpoint_url=f"https://bedrock-runtime.{bedrock_region}.amazonaws.com"
    )

    return bedrock_client
