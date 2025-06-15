import argparse
import ipaddress
import math
import os
import secrets
import string

import boto3
import requests
from dotenv import load_dotenv


def init_client(service="ec2"):
    """Initializes and returns an AWS client for specified service."""
    load_dotenv()

    credentials = {
        "aws_access_key_id": os.getenv("aws_access_key_id"),
        "aws_secret_access_key": os.getenv("aws_secret_access_key"),
        "aws_session_token": os.getenv("aws_session_token"),
        "region_name": os.getenv("aws_region_name"),
    }

    return boto3.client(service, **credentials)


def get_my_public_ip():
    """Get the current machine's public IP address"""
    try:
        response = requests.get("https://httpbin.org/ip", timeout=10)
        return response.json()["origin"]
    except Exception as e:
        print(f"Error getting public IP: {e}")
        return None


def get_available_azs(client, max_azs=None):
    """Get available Availability Zones in the current region"""
    try:
        response = client.describe_availability_zones(
            Filters=[{"Name": "state", "Values": ["available"]}]
        )

        azs = [az["ZoneName"] for az in response["AvailabilityZones"]]

        if max_azs:
            azs = azs[:max_azs]

        print(f"Available Availability Zones: {', '.join(azs)}")
        return azs
    except Exception as e:
        print(f"Error getting availability zones: {e}")
        return []


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
            print("Error: Failed to create VPC")
            exit(1)

        print(f"VPC created with ID: {vpc_id} and CIDR: {vpc_cidr}")

        waiter = client.get_waiter("vpc_available")
        waiter.wait(VpcIds=[vpc_id])
        print(f"VPC {vpc_id} is now available.")

        try:
            client.modify_vpc_attribute(
                VpcId=vpc_id,
                EnableDnsHostnames={"Value": True},
            )
            client.modify_vpc_attribute(
                VpcId=vpc_id,
                EnableDnsSupport={"Value": True},
            )
            print("Enabled DNS hostnames and DNS support for VPC")
        except Exception as e:
            print(f"Warning: Could not enable DNS settings: {e}")

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
            print("Error: Failed to create Internet Gateway")
            exit(1)

        print(f"Internet Gateway created with ID: {igw_id}")

        add_name_tag(client, igw_id, f"{vpc_name}-IGW")

        client.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
        print(f"Attached Internet Gateway {igw_id} to VPC {vpc_id}")

        return igw_id
    except Exception as e:
        print(f"Error creating or attaching Internet Gateway: {e}")
        exit(1)


def create_subnet(client, vpc_id, subnet_cidr, subnet_name_tag, availability_zone=None):
    """Creates a subnet within the VPC and tags it."""
    try:
        subnet_params = {"VpcId": vpc_id, "CidrBlock": subnet_cidr}

        if availability_zone:
            subnet_params["AvailabilityZone"] = availability_zone

        result = client.create_subnet(**subnet_params)
        subnet_id = result.get("Subnet", {}).get("SubnetId")

        if not subnet_id:
            print("Error: Failed to create subnet")
            exit(1)

        actual_az = result.get("Subnet", {}).get("AvailabilityZone", "unknown")
        print(
            f"Subnet created with ID: {subnet_id} and CIDR: {subnet_cidr} in VPC {vpc_id} (AZ: {actual_az})"
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
            print("Error: Failed to create route table")
            exit(1)

        print(f"Route Table created with ID: {rt_id} for VPC {vpc_id}")

        add_name_tag(client, rt_id, route_table_name_tag)

        if is_public:
            client.create_route(
                RouteTableId=rt_id,
                DestinationCidrBlock="0.0.0.0/0",
                GatewayId=igw_id,
            )
            print(f"Added route to IGW {igw_id} in route table {rt_id}")

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


def create_security_group(client, vpc_id, group_name="btu-security-group"):
    """Create a security group with HTTP and SSH access"""
    try:
        my_ip = get_my_public_ip()

        if not my_ip:
            print("Error: Could not determine public IP")
            exit(1)

        ssh_cidr = f"{my_ip}/32"
        print(f"Configuring SSH access for IP: {my_ip}")

        response = client.create_security_group(
            GroupName=group_name,
            Description="Security group for EC2 instance with HTTP and SSH access",
            VpcId=vpc_id,
        )

        security_group_id = response["GroupId"]
        print(f"Created security group: {security_group_id}")

        add_name_tag(client, security_group_id, group_name)

        client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    "IpProtocol": "tcp",
                    "FromPort": 80,
                    "ToPort": 80,
                    "IpRanges": [
                        {
                            "CidrIp": "0.0.0.0/0",
                            "Description": "HTTP access from anywhere",
                        }
                    ],
                }
            ],
        )
        print("Added HTTP (port 80) access for all IPs")

        client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    "IpProtocol": "tcp",
                    "FromPort": 22,
                    "ToPort": 22,
                    "IpRanges": [
                        {
                            "CidrIp": ssh_cidr,
                            "Description": "SSH access from current machine",
                        }
                    ],
                }
            ],
        )
        print(f"Added SSH (port 22) access for {ssh_cidr}")

        return security_group_id
    except Exception as e:
        print(f"Error creating security group: {e}")
        return None


def create_rds_security_group(client, vpc_id, group_name="btu-rds-security-group"):
    """Create a security group for RDS with MySQL access from anywhere"""
    try:
        response = client.create_security_group(
            GroupName=group_name,
            Description="Security group for RDS MySQL instance with access from anywhere",
            VpcId=vpc_id,
        )

        security_group_id = response["GroupId"]
        print(f"Created RDS security group: {security_group_id}")

        add_name_tag(client, security_group_id, group_name)

        client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    "IpProtocol": "tcp",
                    "FromPort": 3306,
                    "ToPort": 3306,
                    "IpRanges": [
                        {
                            "CidrIp": "0.0.0.0/0",
                            "Description": "MySQL access from anywhere",
                        }
                    ],
                }
            ],
        )
        print("Added MySQL (port 3306) access for all IPs")

        return security_group_id
    except Exception as e:
        print(f"Error creating RDS security group: {e}")
        return None


def create_key_pair(client, key_name="btu-ec2-key"):
    """Create a key pair for EC2 instance"""
    try:
        response = client.create_key_pair(KeyName=key_name)
        private_key = response["KeyMaterial"]
        key_file_path = f"{key_name}.pem"

        with open(key_file_path, "w") as key_file:
            key_file.write(private_key)

        os.chmod(key_file_path, 0o400)

        print(f"Created key pair: {key_name}")
        print(f"Private key saved to: {key_file_path}")

        return key_name, key_file_path
    except Exception as e:
        if "InvalidKeyPair.Duplicate" in str(e):
            print(f"Key pair {key_name} already exists, using existing key")
            return key_name, f"{key_name}.pem"
        else:
            print(f"Error creating key pair: {e}")
            return None, None


def get_latest_amazon_linux_ami(client):
    """Get the latest Amazon Linux 2 AMI ID"""
    try:
        images = client.describe_images(
            Owners=["amazon"],
            Filters=[
                {"Name": "name", "Values": ["amzn2-ami-hvm-*-x86_64-gp2"]},
                {"Name": "state", "Values": ["available"]},
                {"Name": "architecture", "Values": ["x86_64"]},
            ],
        )

        if images["Images"]:
            latest_image = max(images["Images"], key=lambda x: x["CreationDate"])
            return latest_image["ImageId"]
        else:
            print("No Amazon Linux 2 AMI found")
            return None
    except Exception as e:
        print(f"Error finding latest AMI: {e}")
        return None


def launch_ec2_instance(
    client,
    vpc_id,
    subnet_id,
    security_group_id,
    key_name,
    instance_name="btu-ec2-instance",
):
    """Launch EC2 instance with specified parameters"""
    try:
        ami_id = get_latest_amazon_linux_ami(client)

        if not ami_id:
            print("Error: Could not find suitable AMI")
            exit(1)

        print(f"Using AMI: {ami_id}")

        try:
            client.modify_subnet_attribute(
                SubnetId=subnet_id, MapPublicIpOnLaunch={"Value": True}
            )
            print(f"Enabled auto-assign public IP for subnet {subnet_id}")
        except Exception as e:
            print(f"Warning: Could not enable auto-assign public IP: {e}")

        response = client.run_instances(
            BlockDeviceMappings=[
                {
                    "DeviceName": "/dev/xvda",
                    "Ebs": {
                        "VolumeSize": 10,
                        "VolumeType": "gp2",
                        "DeleteOnTermination": True,
                    },
                }
            ],
            ImageId=ami_id,
            InstanceType="t2.micro",
            KeyName=key_name,
            MinCount=1,
            MaxCount=1,
            SecurityGroupIds=[security_group_id],
            SubnetId=subnet_id,
            UserData="""#!/bin/bash
yum update -y
yum install -y httpd
systemctl start httpd
systemctl enable httpd
echo "<h1>Hello from EC2 Instance</h1>" > /var/www/html/index.html
""",
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [{"Key": "Name", "Value": instance_name}],
                }
            ],
        )

        instance_id = response["Instances"][0]["InstanceId"]
        print(f"Launched EC2 instance: {instance_id}")

        print("Waiting for instance to be running...")
        waiter = client.get_waiter("instance_running")
        waiter.wait(InstanceIds=[instance_id])

        instance_details = client.describe_instances(InstanceIds=[instance_id])
        instance = instance_details["Reservations"][0]["Instances"][0]
        public_ip = instance.get("PublicIpAddress")
        private_ip = instance.get("PrivateIpAddress")

        print(f"Instance is running!")
        print(f"Public IP: {public_ip}")
        print(f"Private IP: {private_ip}")

        return instance_id, public_ip, private_ip
    except Exception as e:
        print(f"Error launching EC2 instance: {e}")
        return None, None, None


def generate_password(length=16):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = "".join(secrets.choice(alphabet) for i in range(length))
    return password


def create_db_subnet_group(rds_client, subnet_group_name, subnet_ids, description):
    """Create a DB subnet group for RDS"""
    try:
        response = rds_client.create_db_subnet_group(
            DBSubnetGroupName=subnet_group_name,
            DBSubnetGroupDescription=description,
            SubnetIds=subnet_ids,
            Tags=[{"Key": "Name", "Value": subnet_group_name}],
        )

        print(f"Created DB subnet group: {subnet_group_name}")
        return subnet_group_name
    except Exception as e:
        if "DBSubnetGroupAlreadyExistsFault" in str(e):
            print(f"DB subnet group {subnet_group_name} already exists, using existing")
            return subnet_group_name
        else:
            print(f"Error creating DB subnet group: {e}")
            return None


def create_rds_instance(
    vpc_id,
    subnet_ids,
    security_group_id,
    db_name="btudb",
    db_instance_identifier="btu-rds-mysql",
    username="admin",
    allocated_storage=60,
):
    """Create RDS MySQL instance with specified parameters"""
    try:
        rds_client = init_client("rds")
        password = generate_password(16)

        subnet_group_name = f"{db_instance_identifier}-subnet-group"
        subnet_group = create_db_subnet_group(
            rds_client,
            subnet_group_name,
            subnet_ids,
            f"Subnet group for {db_instance_identifier}",
        )

        if not subnet_group:
            print("Error: Failed to create DB subnet group")
            exit(1)

        print(f"Creating RDS MySQL instance: {db_instance_identifier}")
        print(f"Database name: {db_name}")
        print(f"Username: {username}")
        print(f"Allocated storage: {allocated_storage} GB")

        response = rds_client.create_db_instance(
            DBName=db_name,
            DBInstanceIdentifier=db_instance_identifier,
            AllocatedStorage=allocated_storage,
            DBInstanceClass="db.t3.micro",
            Engine="mysql",
            MasterUsername=username,
            MasterUserPassword=password,
            VpcSecurityGroupIds=[security_group_id],
            DBSubnetGroupName=subnet_group,
            BackupRetentionPeriod=7,
            MultiAZ=False,
            EngineVersion="8.0.41",
            AutoMinorVersionUpgrade=True,
            PubliclyAccessible=True,
            Tags=[{"Key": "Name", "Value": db_instance_identifier}],
            StorageType="gp2",
            DeletionProtection=False,
        )

        print(f"RDS instance creation initiated: {db_instance_identifier}")
        print("Waiting for RDS instance to be available...")
        waiter = rds_client.get_waiter("db_instance_available")
        waiter.wait(
            DBInstanceIdentifier=db_instance_identifier,
            WaiterConfig={"Delay": 30, "MaxAttempts": 40},
        )

        response = rds_client.describe_db_instances(
            DBInstanceIdentifier=db_instance_identifier
        )

        db_instance = response["DBInstances"][0]
        endpoint = db_instance["Endpoint"]["Address"]
        port = db_instance["Endpoint"]["Port"]

        print(f"RDS instance is now available!")
        print(f"Endpoint: {endpoint}")
        print(f"Port: {port}")

        return db_instance_identifier, endpoint, port, username, password
    except Exception as e:
        print(f"Error creating RDS instance: {e}")
        return None, None, None, None, None


def scale_rds_storage(args):
    """Increase RDS instance storage by 25%"""
    try:
        rds_client = init_client("rds")

        print(f"Scaling RDS Storage for instance: {args.db_instance_identifier}")
        print("=" * 50)

        response = rds_client.describe_db_instances(
            DBInstanceIdentifier=args.db_instance_identifier
        )

        if not response["DBInstances"]:
            print(f"❌ RDS instance {args.db_instance_identifier} not found")
            return

        db_instance = response["DBInstances"][0]
        current_storage = db_instance["AllocatedStorage"]
        new_storage = int(current_storage * 1.25)

        print(f"Current allocated storage: {current_storage} GB")
        print(f"New allocated storage: {new_storage} GB")
        print(
            f"Increase: {new_storage - current_storage} GB ({((new_storage - current_storage) / current_storage) * 100:.1f}%)"
        )

        rds_client.modify_db_instance(
            DBInstanceIdentifier=args.db_instance_identifier,
            AllocatedStorage=new_storage,
            ApplyImmediately=True,
        )

        print(f"✅ Storage scaling initiated for {args.db_instance_identifier}")
        print("Note: The scaling operation may take some time to complete.")
    except Exception as e:
        print(f"❌ Error scaling RDS storage: {e}")


def list_dynamodb_tables(args):
    """List all DynamoDB tables in the region"""
    try:
        dynamodb_client = init_client("dynamodb")

        print("DynamoDB Tables in Region")
        print("=" * 40)

        response = dynamodb_client.list_tables()
        table_names = response.get("TableNames", [])

        if not table_names:
            print("No DynamoDB tables found in the region.")
            return

        print(f"Found {len(table_names)} table(s):")
        print("-" * 40)

        for i, table_name in enumerate(table_names, 1):
            print(f"{i}. {table_name}")

        print("=" * 40)
    except Exception as e:
        print(f"❌ Error listing DynamoDB tables: {e}")


def create_rds_snapshot(args):
    """Create a manual snapshot of RDS instance"""
    try:
        rds_client = init_client("rds")

        print(
            f"Creating manual snapshot for RDS instance: {args.db_instance_identifier}"
        )
        print("=" * 60)

        try:
            response = rds_client.describe_db_instances(
                DBInstanceIdentifier=args.db_instance_identifier
            )

            if not response["DBInstances"]:
                print(f"❌ RDS instance {args.db_instance_identifier} not found")
                return

            db_instance = response["DBInstances"][0]
            db_status = db_instance["DBInstanceStatus"]

            if db_status != "available":
                print(
                    f"❌ RDS instance is not in 'available' state. Current status: {db_status}"
                )
                return

        except Exception as e:
            print(f"❌ Error checking RDS instance: {e}")
            return

        print(f"Snapshot identifier: {args.snapshot_identifier}")
        print(f"Instance status: {db_status}")

        snapshot_response = rds_client.create_db_snapshot(
            DBSnapshotIdentifier=args.snapshot_identifier,
            DBInstanceIdentifier=args.db_instance_identifier,
            Tags=[{"Key": "Name", "Value": args.snapshot_identifier}],
        )

        snapshot_info = snapshot_response["DBSnapshot"]
        print(f"✅ Snapshot creation initiated!")
        print(f"Snapshot ARN: {snapshot_info['DBSnapshotArn']}")
        print(f"Status: {snapshot_info['Status']}")

        print("\nWaiting for snapshot to complete...")
        waiter = rds_client.get_waiter("db_snapshot_completed")
        waiter.wait(
            DBSnapshotIdentifier=args.snapshot_identifier,
            WaiterConfig={"Delay": 30, "MaxAttempts": 120},
        )

        final_response = rds_client.describe_db_snapshots(
            DBSnapshotIdentifier=args.snapshot_identifier
        )

        final_snapshot = final_response["DBSnapshots"][0]
        print(f"✅ Snapshot completed!")
        print(f"Final status: {final_snapshot['Status']}")
        print(f"Snapshot created at: {final_snapshot['SnapshotCreateTime']}")
        print(f"Allocated storage: {final_snapshot['AllocatedStorage']} GB")
    except Exception as e:
        print(f"❌ Error creating RDS snapshot: {e}")


def manage_rds_infrastructure(args):
    """Manage RDS infrastructure: create RDS instance with security group"""
    ec2_client = init_client("ec2")

    print("RDS MySQL Instance Creation Tool")
    print("=" * 50)
    print(f"VPC ID: {args.vpc_id}")
    print(f"Subnet IDs: {', '.join(args.subnet_ids)}")
    print(f"DB Instance Identifier: {args.db_instance_identifier}")
    print(f"Database Name: {args.db_name}")
    print(f"Username: {args.username}")
    print(f"Allocated Storage: {args.allocated_storage} GB")
    print("=" * 50)

    print("\n1. Creating RDS security group...")
    security_group_id = create_rds_security_group(
        ec2_client,
        args.vpc_id,
        f"{args.db_instance_identifier}-sg",
    )

    if not security_group_id:
        print("❌ Failed to create RDS security group. Exiting.")
        return

    print("\n2. Creating RDS MySQL instance...")
    db_identifier, endpoint, port, username, password = create_rds_instance(
        args.vpc_id,
        args.subnet_ids,
        security_group_id,
        args.db_name,
        args.db_instance_identifier,
        args.username,
        args.allocated_storage,
    )

    if not db_identifier:
        print("❌ Failed to create RDS instance. Exiting.")
        return

    print("\n" + "=" * 60)
    print("✅ RDS MYSQL INSTANCE CREATION COMPLETED")
    print("=" * 60)
    print(f"DB Instance Identifier: {db_identifier}")
    print(f"Database Name: {args.db_name}")
    print(f"Username: {username}")
    print(f"Password: {password}")
    print(f"Endpoint: {endpoint}")
    print(f"Port: {port}")
    print(f"Security Group: {security_group_id}")

    if endpoint and port:
        print("\n📋 Connection Information:")
        print(f"Host: {endpoint}")
        print(f"Port: {port}")
        print(f"Database: {args.db_name}")
        print(f"Username: {username}")
        print(f"Password: {password}")


def manage_ec2_infrastructure(args):
    """Manage EC2 infrastructure: create security group, key pair, and launch instance"""
    client = init_client()

    print("EC2 Instance Creation Tool")
    print("=" * 40)
    print(f"VPC ID: {args.vpc_id}")
    print(f"Subnet ID: {args.subnet_id}")
    print(f"Security Group Name: {args.security_group_name}")
    print(f"Key Pair Name: {args.key_name}")
    print(f"Instance Name: {args.instance_name}")
    print("=" * 40)

    print("\n1. Creating security group...")
    security_group_id = create_security_group(
        client,
        args.vpc_id,
        args.security_group_name,
    )

    if not security_group_id:
        print("❌ Failed to create security group. Exiting.")
        return

    print("\n2. Creating key pair...")
    key_name, key_file_path = create_key_pair(client, args.key_name)

    if not key_name:
        print("❌ Failed to create key pair. Exiting.")
        return

    print("\n3. Launching EC2 instance...")
    instance_id, public_ip, private_ip = launch_ec2_instance(
        client,
        args.vpc_id,
        args.subnet_id,
        security_group_id,
        key_name,
        args.instance_name,
    )

    if not instance_id:
        print("❌ Failed to launch EC2 instance. Exiting.")
        return

    print("\n" + "=" * 50)
    print("✅ EC2 INSTANCE CREATION COMPLETED")
    print("=" * 50)
    print(f"Instance ID: {instance_id}")
    print(f"Public IP: {public_ip}")
    print(f"Private IP: {private_ip}")
    print(f"Security Group: {security_group_id}")
    print(f"Key Pair: {key_name}")
    print(f"Private Key File: {key_file_path}")

    if public_ip:
        print("\n📋 Connection Information:")
        print(f"Web URL: http://{public_ip}")
        print(f"SSH Command: ssh -i {key_file_path} ec2-user@{public_ip}")


def manage_vpc_infrastructure(args):
    """Manage VPC infrastructure: create VPC, subnets, route tables, etc."""
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

    available_azs = get_available_azs(client)
    if len(available_azs) < 2:
        print("Error: At least 2 Availability Zones are required for RDS compatibility")
        exit(1)

    vpc_id = create_vpc(client, args.vpc_cidr, args.vpc_name)
    igw_id = create_and_attach_igw(client, vpc_id, args.vpc_name)

    public_subnet_ids = []
    private_subnet_ids = []
    public_rt_ids = []
    private_rt_ids = []

    for i in range(args.num_subnets):
        az_index = i % len(available_azs)
        current_az = available_azs[az_index]

        public_subnet_name = f"{args.vpc_name}-public-subnet-{i+1}"
        public_subnet_cidr = calculate_subnet_cidr(
            args.vpc_cidr, i, True, args.num_subnets
        )
        public_subnet_id = create_subnet(
            client, vpc_id, public_subnet_cidr, public_subnet_name, current_az
        )
        public_subnet_ids.append(public_subnet_id)

        private_subnet_name = f"{args.vpc_name}-private-subnet-{i+1}"
        private_subnet_cidr = calculate_subnet_cidr(
            args.vpc_cidr, i, False, args.num_subnets
        )
        private_subnet_id = create_subnet(
            client, vpc_id, private_subnet_cidr, private_subnet_name, current_az
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
        print(f"Public Subnet {i+1}: {public_subnet_ids[i]} (RT: {public_rt_ids[i]})")
        print(
            f"Private Subnet {i+1}: {private_subnet_ids[i]} (RT: {private_rt_ids[i]})"
        )

    print("---------------------------------------")
    print("\n🔍 RDS Usage Tips:")
    print("For RDS creation, use subnets from different AZs. For example:")
    if len(public_subnet_ids) >= 2:
        print(f"Public subnets: {public_subnet_ids[0]} {public_subnet_ids[1]}")
    if len(private_subnet_ids) >= 2:
        print(f"Private subnets: {private_subnet_ids[0]} {private_subnet_ids[1]}")
    print("---------------------------------------")


def main():
    parser = argparse.ArgumentParser(
        description="AWS VPC, EC2, RDS, and DynamoDB Management CLI Tool"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    vpc_parser = subparsers.add_parser(
        "create-vpc",
        help="Create VPC with subnets and networking",
    )
    vpc_parser.add_argument(
        "--vpc-name",
        required=True,
        help="Name tag for the VPC (e.g., my-vpc)",
    )
    vpc_parser.add_argument(
        "--vpc-cidr",
        required=True,
        help="CIDR block for the VPC (e.g., 10.0.0.0/16)",
    )
    vpc_parser.add_argument(
        "--num-subnets",
        type=int,
        required=True,
        help="Number of public/private subnet pairs to create (max 200)",
    )

    ec2_parser = subparsers.add_parser(
        "create-ec2",
        help="Create EC2 instance with security group and key pair",
    )
    ec2_parser.add_argument(
        "vpc_id",
        help="VPC ID where the instance will be created",
    )
    ec2_parser.add_argument(
        "subnet_id",
        help="Subnet ID where the instance will be placed",
    )
    ec2_parser.add_argument(
        "--security-group-name",
        default="btu-security-group",
        help="Name for the security group (default: btu-security-group)",
    )
    ec2_parser.add_argument(
        "--key-name",
        default="btu-ec2-key",
        help="Name for the key pair (default: btu-ec2-key)",
    )
    ec2_parser.add_argument(
        "--instance-name",
        default="btu-ec2-instance",
        help="Name for the EC2 instance (default: btu-ec2-instance)",
    )

    rds_parser = subparsers.add_parser(
        "create-rds",
        help="Create RDS MySQL instance with security group",
    )
    rds_parser.add_argument(
        "vpc_id",
        help="VPC ID where the RDS instance will be created",
    )
    rds_parser.add_argument(
        "subnet_ids",
        nargs="+",
        help="List of subnet IDs for the DB subnet group (minimum 2 subnets in different AZs)",
    )
    rds_parser.add_argument(
        "--db-instance-identifier",
        default="btu-rds-mysql",
        help="Identifier for the RDS instance (default: btu-rds-mysql)",
    )
    rds_parser.add_argument(
        "--db-name",
        default="btudb",
        help="Name of the database to create (default: btudb)",
    )
    rds_parser.add_argument(
        "--username",
        default="admin",
        help="Master username for the database (default: admin)",
    )
    rds_parser.add_argument(
        "--allocated-storage",
        type=int,
        default=60,
        help="Allocated storage in GB (default: 60)",
    )

    scale_parser = subparsers.add_parser(
        "scale-rds-storage",
        help="Increase RDS instance storage by 25%%",
    )
    scale_parser.add_argument(
        "db_instance_identifier",
        help="RDS instance identifier to scale",
    )

    dynamodb_parser = subparsers.add_parser(
        "list-dynamodb-tables",
        help="List all DynamoDB tables in the current region",
    )

    snapshot_parser = subparsers.add_parser(
        "create-rds-snapshot",
        help="Create a manual snapshot of RDS instance",
    )
    snapshot_parser.add_argument(
        "db_instance_identifier",
        help="RDS instance identifier to snapshot",
    )
    snapshot_parser.add_argument(
        "snapshot_identifier",
        help="Identifier for the new snapshot",
    )

    args = parser.parse_args()

    if args.command == "create-vpc":
        manage_vpc_infrastructure(args)
    elif args.command == "create-ec2":
        manage_ec2_infrastructure(args)
    elif args.command == "create-rds":
        manage_rds_infrastructure(args)
    elif args.command == "scale-rds-storage":
        scale_rds_storage(args)
    elif args.command == "list-dynamodb-tables":
        list_dynamodb_tables(args)
    elif args.command == "create-rds-snapshot":
        create_rds_snapshot(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
