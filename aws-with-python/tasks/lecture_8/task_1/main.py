import argparse
import ipaddress
import os
import math

import boto3
from dotenv import load_dotenv


def init_client():
    """Initializes and returns an AWS client."""
    load_dotenv()

    credentials = {
        "aws_access_key_id": os.getenv("aws_access_key_id"),
        "aws_secret_access_key": os.getenv("aws_secret_access_key"),
        "aws_session_token": os.getenv("aws_session_token"),
        "region_name": os.getenv("aws_region_name"),
    }

    return boto3.client("ec2", **credentials)


def is_valid_cidr(cidr):
    """Checks if a CIDR is valid."""
    try:
        ipaddress.ip_network(cidr)
        return True
    except ValueError:
        return False


def add_name_tag(client, resource_id, name_value):
    """Adds a 'Name' tag to an AWS resource."""
    try:
        client.create_tags(
            Resources=[resource_id],
            Tags=[{"Key": "Name", "Value": name_value}],
        )
        print(f"Successfully tagged resource {resource_id} with Name: {name_value}")
    except Exception as e:
        print(f"Error tagging resource {resource_id}: {e}")


def create_vpc(client, vpc_cidr, vpc_name):
    """Creates a VPC and tags it."""
    try:
        result = client.create_vpc(CidrBlock=vpc_cidr)
        vpc_id = result.get("Vpc", {}).get("VpcId")

        if not vpc_id:
            print("Error: Could not retrieve VPC ID after creation.")
            exit(1)
        print(f"VPC created with ID: {vpc_id} and CIDR: {vpc_cidr}")

        waiter = client.get_waiter("vpc_available")
        waiter.wait(VpcIds=[vpc_id])
        print(f"VPC {vpc_id} is now available.")

        add_name_tag(client, vpc_id, vpc_name)

        return vpc_id
    except Exception as e:
        print(f"Error creating VPC: {e}")
        exit(1)


def create_and_attach_igw(client, vpc_id, vpc_name):
    """Creates an Internet Gateway, tags it, and attaches it to the VPC."""
    try:
        result = client.create_internet_gateway()
        igw_id = result.get("InternetGateway", {}).get("InternetGatewayId")

        if not igw_id:
            print("Error: Could not retrieve Internet Gateway ID after creation.")
            exit(1)
        print(f"Internet Gateway created with ID: {igw_id}")

        add_name_tag(client, igw_id, f"{vpc_name}-IGW")

        client.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
        print(f"Attached Internet Gateway {igw_id} to VPC {vpc_id}")

        return igw_id
    except Exception as e:
        print(f"Error creating or attaching Internet Gateway: {e}")
        exit(1)


def create_subnet(client, vpc_id, subnet_cidr, subnet_name_tag):
    """Creates a subnet within the VPC and tags it."""
    try:
        result = client.create_subnet(VpcId=vpc_id, CidrBlock=subnet_cidr)
        subnet_id = result.get("Subnet", {}).get("SubnetId")

        if not subnet_id:
            print("Error: Could not retrieve Subnet ID after creation.")
            exit(1)
        print(
            f"Subnet created with ID: {subnet_id} and CIDR: {subnet_cidr} in VPC {vpc_id}"
        )

        waiter = client.get_waiter("subnet_available")
        waiter.wait(SubnetIds=[subnet_id])
        print(f"Subnet {subnet_id} is now available.")

        add_name_tag(client, subnet_id, subnet_name_tag)

        return subnet_id
    except Exception as e:
        print(f"Error creating subnet {subnet_name_tag} with CIDR {subnet_cidr}: {e}")
        exit(1)


def create_route_table(client, vpc_id, route_table_name_tag, is_public, igw_id=None):
    """Creates a route table. If public, adds a route to the IGW."""
    try:
        result = client.create_route_table(VpcId=vpc_id)
        rt_id = result.get("RouteTable", {}).get("RouteTableId")

        if not rt_id:
            print("Error: Could not retrieve Route Table ID after creation.")
            exit(1)
        print(f"Route Table created with ID: {rt_id} for VPC {vpc_id}")

        add_name_tag(client, rt_id, route_table_name_tag)

        if is_public:
            if not igw_id:
                print(
                    "Error: Internet Gateway ID is required for a public route table."
                )
                exit(1)

            client.create_route(
                RouteTableId=rt_id, DestinationCidrBlock="0.0.0.0/0", GatewayId=igw_id
            )
            print(f"Added route to IGW {igw_id} in Route Table {rt_id}")

        return rt_id
    except Exception as e:
        print(f"Error creating route table {route_table_name_tag}: {e}")
        exit(1)


def associate_route_table_to_subnet(client, route_table_id, subnet_id):
    """Associates a route table with a subnet."""
    try:
        client.associate_route_table(RouteTableId=route_table_id, SubnetId=subnet_id)
        print(f"Associated Route Table {route_table_id} with Subnet {subnet_id}")
    except Exception as e:
        print(
            f"Error associating Route Table {route_table_id} with Subnet {subnet_id}: {e}"
        )
        exit(1)


def calculate_subnet_cidr(vpc_cidr, subnet_index, is_public, num_subnets):
    """Calculate CIDR block for a subnet based on its index."""
    vpc_network = ipaddress.ip_network(vpc_cidr)
    subnet_bits = math.ceil(math.log2(num_subnets))
    new_prefix_length = vpc_network.prefixlen + subnet_bits + 1

    if is_public:
        base_address = vpc_network.network_address
    else:
        half_way = vpc_network.network_address + (2 ** (32 - vpc_network.prefixlen - 1))
        base_address = half_way

    network_address = base_address + (subnet_index * (2 ** (32 - new_prefix_length)))

    return str(
        ipaddress.ip_network(f"{network_address}/{new_prefix_length}", strict=False)
    )


def main():
    parser = argparse.ArgumentParser(description="AWS VPC Management CLI Tool")
    parser.add_argument(
        "--vpc-name",
        required=True,
        help="Name tag for the VPC (e.g., my-vpc)",
    )
    parser.add_argument(
        "--vpc-cidr",
        required=True,
        help="CIDR block for the VPC (e.g., 10.0.0.0/16)",
    )
    parser.add_argument(
        "--num-subnets",
        type=int,
        required=True,
        help="Number of public/private subnet pairs to create (max 200)",
    )

    args = parser.parse_args()

    if args.num_subnets < 1 or args.num_subnets > 200:
        print("Error: Number of subnets must be between 1 and 200")
        exit(1)

    if not is_valid_cidr(args.vpc_cidr):
        print("Error: Invalid VPC CIDR")
        exit(1)

    vpc_network = ipaddress.ip_network(args.vpc_cidr)
    required_prefix_length = (
        math.ceil(math.log2(args.num_subnets * 2)) + vpc_network.prefixlen
    )
    if required_prefix_length > 28:
        print(
            f"Error: VPC CIDR {args.vpc_cidr} is too small for {args.num_subnets} subnet pairs"
        )
        exit(1)

    client = init_client()
    vpc_id = create_vpc(client, args.vpc_cidr, args.vpc_name)
    igw_id = create_and_attach_igw(client, vpc_id, args.vpc_name)

    public_subnet_ids = []
    private_subnet_ids = []
    public_rt_ids = []
    private_rt_ids = []

    for i in range(args.num_subnets):
        public_subnet_name = f"{args.vpc_name}-public-subnet-{i+1}"
        public_subnet_cidr = calculate_subnet_cidr(
            args.vpc_cidr, i, True, args.num_subnets
        )
        public_subnet_id = create_subnet(
            client, vpc_id, public_subnet_cidr, public_subnet_name
        )
        public_subnet_ids.append(public_subnet_id)

        private_subnet_name = f"{args.vpc_name}-private-subnet-{i+1}"
        private_subnet_cidr = calculate_subnet_cidr(
            args.vpc_cidr, i, False, args.num_subnets
        )
        private_subnet_id = create_subnet(
            client, vpc_id, private_subnet_cidr, private_subnet_name
        )
        private_subnet_ids.append(private_subnet_id)

        public_rt_name = f"{args.vpc_name}-public-rt-{i+1}"
        public_rt_id = create_route_table(
            client, vpc_id, public_rt_name, is_public=True, igw_id=igw_id
        )
        associate_route_table_to_subnet(client, public_rt_id, public_subnet_id)
        public_rt_ids.append(public_rt_id)

        private_rt_name = f"{args.vpc_name}-private-rt-{i+1}"
        private_rt_id = create_route_table(
            client, vpc_id, private_rt_name, is_public=False
        )
        associate_route_table_to_subnet(client, private_rt_id, private_subnet_id)
        private_rt_ids.append(private_rt_id)

    print("\n--- AWS Infrastructure Setup Complete ---")
    print(f"VPC ID: {vpc_id} (Name: {args.vpc_name})")
    print(f"Internet Gateway ID: {igw_id}")

    for i in range(args.num_subnets):
        print(f"\nSubnet Pair {i+1}:")
        print(
            f"Public Subnet ID: {public_subnet_ids[i]} (Name: {args.vpc_name}-public-subnet-{i+1})"
        )
        print(
            f"Private Subnet ID: {private_subnet_ids[i]} (Name: {args.vpc_name}-private-subnet-{i+1})"
        )
        print(
            f"Public Route Table ID: {public_rt_ids[i]} (Name: {args.vpc_name}-public-rt-{i+1})"
        )
        print(
            f"Private Route Table ID: {private_rt_ids[i]} (Name: {args.vpc_name}-private-rt-{i+1})"
        )

    print("---------------------------------------")


if __name__ == "__main__":
    main()
