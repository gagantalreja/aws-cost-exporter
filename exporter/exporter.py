from prometheus_client import start_http_server, Metric, REGISTRY
import time
import os
import re
import boto3
import datetime


def switch_role(role_arn, region):

    sts_connection = boto3.client(
        "sts",
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    )

    acct_cred = sts_connection.assume_role(
        RoleArn=role_arn,
        RoleSessionName="inv_master",
    )

    ACCESS_KEY = acct_cred["Credentials"]["AccessKeyId"]
    SECRET_KEY = acct_cred["Credentials"]["SecretAccessKey"]
    SESSION_TOKEN = acct_cred["Credentials"]["SessionToken"]

    boto3.setup_default_session(
        region_name=region,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        aws_session_token=SESSION_TOKEN,
    )


def getCosts():
    client = boto3.client("ce")

    end = datetime.datetime.utcnow()
    start = end - datetime.timedelta(days=1)

    start = start.strftime("%Y-%m-%d")
    end = end.strftime("%Y-%m-%d")

    print("Starting script searching by the follow time range")
    print(start + " - " + end)

    # Call AWS API to get costs
    response = client.get_cost_and_usage(
        TimePeriod={"Start": start, "End": end},
        Granularity="MONTHLY",
        Metrics=["AmortizedCost"],
        Filter={
            "Not": {
                "Dimensions": {
                    "Key": "RECORD_TYPE",
                    "Values": [
                        "Credit",
                        "Refund",
                        "Enterprise Discount Program Discount",
                    ],
                }
            }
        },
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )

    service_cost_mapping = dict()
    role_arns = []
    regions = ["us-east-1", "us-east-2", "us-west-1", "us-west-2"]

    # for arn in role_arns:
    #     service_cost_mapping[arn] = {}
    #     for region in regions:
    #         service_cost_mapping[arn][region] = {}
    #         for service in response["ResultsByTime"][0]["Groups"]:
    #             service_cost_mapping[arn][region][service] = 
                

    return service_cost_mapping


class costExporter(object):
    def collect(self):

        metric = Metric(
            "aws_project_cost", "Total amount of costs for project", "gauge"
        )
        for project, cost in getCosts().items():
            metric.add_sample(
                "aws_project_cost", value=cost, labels={"project": project}
            )

        yield metric


if __name__ == "__main__":
    start_http_server(os.getenv("PORT", "4298"))
    metrics = costExporter()
    REGISTRY.register(metrics)
    while True:
        time.sleep(1)
