from os import getenv

import boto3
import requests


def create_db_instance(rds_client):
    """Creates a new RDS instance that is associated with the given security group."""
    response = rds_client.create_db_instance(
        DBName="postgres",
        DBInstanceIdentifier="demo-pg-db-1",
        AllocatedStorage=50,
        DBInstanceClass="db.t4g.micro",
        Engine="postgres",
        MasterUsername="postgres",
        MasterUserPassword="strongrandompassword",
        # VpcSecurityGroupIds=[security_group_id],
        BackupRetentionPeriod=7,
        Port=5432,
        MultiAZ=False,
        EngineVersion="13.5",
        AutoMinorVersionUpgrade=True,
        # Iops=123, # Necessary when StorageType is 'io1'
        PubliclyAccessible=True,
        Tags=[
            {"Key": "Name", "Value": "First RDS"},
        ],
        StorageType="gp2",
        EnablePerformanceInsights=True,
        PerformanceInsightsRetentionPeriod=7,
        DeletionProtection=False,
    )

    _id = response.get("DBInstance").get("DBInstanceIdentifier")
    print(f"Instance {_id} was created")

    return response


def print_connection_params(rds_client, identifier):
    response = rds_client.describe_db_instances(DBInstanceIdentifier=identifier)
    instance = response.get("DBInstances")[0]
    endpoint = instance.get("Endpoint")
    host = endpoint.get("Address")
    port = endpoint.get("Port")
    username = instance.get("MasterUsername")
    db_name = instance.get("DBName")
    print("DB Host:", host)
    print("DB port:", port)
    print("DB user:", username)
    print("DB database:", db_name)


def reboot_rds(rds_client, identifier):
    rds_client.reboot_db_instance(DBInstanceIdentifier=identifier)
    print(f"RDS - {identifier} rebooted successfully")


def stop_rds(rds_client, identifier):
    response = rds_client.stop_db_instance(
        DBInstanceIdentifier=identifier, DBSnapshotIdentifier="stop-snapshot001"
    )

    print(response)


def start_rds(rds_client, identifier):
    response = rds_client.start_db_instance(DBInstanceIdentifier=identifier)

    print(response)


def update_rds_pass(rds_cient, identifer):
    response = rds_cient.modify_db_instance(
        DBInstanceIdentifier=identifer, MasterUserPassword="new-pa$$word"
    )

    print(response)


def main():
    """The main function."""

    rds_client = boto3.client(
        "rds",
        aws_access_key_id=getenv("aws_access_key_id"),
        aws_secret_access_key=getenv("aws_secret_access_key"),
        aws_session_token=getenv("aws_session_token"),
        region_name=getenv("aws_region_name"),
    )

    db_instance = create_db_instance(rds_client)
    db_identifier = "demo-pg-db-1"
    # reboot_rds(rds_client, db_identifier)
    # print_connection_params(rds_client, 'demo-pg-db-1')


if __name__ == "__main__":
    main()
