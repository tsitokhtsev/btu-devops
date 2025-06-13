import boto3
from os import getenv
from pprint import pprint

ec2_client = boto3.client(
    "ec2",
    aws_access_key_id=getenv("aws_access_key_id"),
    aws_secret_access_key=getenv("aws_secret_access_key"),
    aws_session_token=getenv("aws_session_token"),
    region_name=getenv("aws_region_name"),
)


### part 1/2 ###
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


def attach_igw_to_vpc(vpc_id, igw_id):
    ec2_client.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)


### part 2/2 ###


def create_subnet(vpc_id, cidr_block, subnet_name):
    response = ec2_client.create_subnet(VpcId=vpc_id, CidrBlock=cidr_block)
    subnet = response.get("Subnet")
    pprint(subnet)
    subnet_id = subnet.get("SubnetId")
    ec2_client.create_tags(
        Resources=[subnet_id],
        Tags=[
            {"Key": "Name", "Value": subnet_name},
        ],
    )
    return subnet_id


def create_or_get_igw(vpc_id):
    igw_id = None
    igw_response = ec2_client.describe_internet_gateways(
        Filters=[{"Name": "attachment.vpc-id", "Values": [vpc_id]}]
    )

    if "InternetGateways" in igw_response and igw_response["InternetGateways"]:
        igw = igw_response["InternetGateways"][0]
        igw_id = igw["InternetGatewayId"]
    else:
        response = ec2_client.create_internet_gateway()
        pprint(response)
        igw = response.get("InternetGateway")
        igw_id = igw.get("InternetGatewayId")
        response = ec2_client.attach_internet_gateway(
            InternetGatewayId=igw_id, VpcId=vpc_id
        )
        print("attached")
        pprint(response)
    return igw_id


def create_route_table_with_route(vpc_id, route_table_name, igw_id):
    response = ec2_client.create_route_table(VpcId=vpc_id)
    route_table = response.get("RouteTable")
    pprint(route_table)
    route_table_id = route_table.get("RouteTableId")
    print("Route table id", route_table_id)
    ec2_client.create_tags(
        Resources=[route_table_id],
        Tags=[
            {"Key": "Name", "Value": route_table_name},
        ],
    )
    response = ec2_client.create_route(
        DestinationCidrBlock="0.0.0.0/0",
        GatewayId=igw_id,
        RouteTableId=route_table_id,
    )
    return route_table_id


def associate_route_table_to_subnet(route_table_id, subnet_id):
    response = ec2_client.associate_route_table(
        RouteTableId=route_table_id, SubnetId=subnet_id
    )
    print("Route table associated")
    pprint(response)


def enable_auto_public_ips(subnet_id, action):
    new_state = True if action == "enable" else False
    response = ec2_client.modify_subnet_attribute(
        MapPublicIpOnLaunch={"Value": new_state}, SubnetId=subnet_id
    )
    print("Public IP association state changed to", new_state)


def create_route_table_without_route(vpc_id):
    response = ec2_client.create_route_table(VpcId=vpc_id)
    route_table = response.get("RouteTable")
    pprint(route_table)
    route_table_id = route_table.get("RouteTableId")
    print("Route table id", route_table_id)
    ec2_client.create_tags(
        Resources=[route_table_id],
        Tags=[
            {"Key": "Name", "Value": "private-route-table"},
        ],
    )
    return route_table_id


def main():
    vpc_id = "vpc-006c81f627b0c8cb2"
    # create private subnet
    # subnet_id = create_subnet(vpc_id, '10.22.9.0/24', 'private_sub_10')
    # rtb_id = create_route_table_without_route(vpc_id)
    # associate_route_table_to_subnet(rtb_id, subnet_id)

    # create public subnet
    # subnet_id = create_subnet(vpc_id, '10.22.14.0/24', 'public_sub_14')
    # rtb_id = create_route_table_with_route(vpc_id, 'my_route_name',
    #                                        create_or_get_igw(vpc_id))
    # associate_route_table_to_subnet(rtb_id, subnet_id)
    # enable_auto_public_ips(subnet_id, 'enable')


if __name__ == "__main__":
    main()
