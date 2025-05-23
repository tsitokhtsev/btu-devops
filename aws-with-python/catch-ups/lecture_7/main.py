import boto3
from os import getenv

ec2_client = boto3.client(
    "ec2",
    aws_access_key_id=getenv("aws_access_key_id"),
    aws_secret_access_key=getenv("aws_secret_access_key"),
    aws_session_token=getenv("aws_session_token"),
    region_name=getenv("aws_region_name"),
)


def list_vpcs():
    result = ec2_client.describe_vpcs()
    vpcs = result.get("Vpcs")
    print(vpcs)


def create_vpc():
    result = ec2_client.create_vpc(CidrBlock="10.0.0.0/16")
    vpc = result.get("Vpc")
    print(vpc)


def add_name_tag(vpc_id):
    ec2_client.create_tags(
        Resources=[vpc_id], Tags=[{"Key": "Name", "Value": "btuVPC"}]
    )


def create_igw():
    result = ec2_client.create_internet_gateway()
    return result.get("InternetGateway").get("InternetGatewayId")


def attach_igw_to_vpc(vpc_id, igw_id):
    ec2_client.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)


def main():
    # list_vpcs()
    # create_vpc()
    # print(add_name_tag("vpc-0fba1756ddc071252"))
    igw_id = create_igw()
    attach_igw_to_vpc("vpc-0fba1756ddc071252", igw_id)


if __name__ == "__main__":
    main()
