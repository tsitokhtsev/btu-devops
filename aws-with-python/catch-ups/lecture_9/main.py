import urllib
from os import getenv

import boto3

ec2_client = boto3.client(
    "ec2",
    aws_access_key_id=getenv("aws_access_key_id"),
    aws_secret_access_key=getenv("aws_secret_access_key"),
    aws_session_token=getenv("aws_session_token"),
    region_name=getenv("aws_region_name"),
)


def create_key_pair(key_name):
    response = ec2_client.create_key_pair(
        KeyName=key_name, KeyType="rsa", KeyFormat="pem"
    )
    key_id = response.get("KeyPairId")
    with open(f"{key_name}.pem", "w") as file:
        file.write(response.get("KeyMaterial"))
    print("Key pair id - ", key_id)
    return key_id


def create_security_group(name, description, VPC_ID):
    response = ec2_client.create_security_group(
        Description=description, GroupName=name, VpcId=VPC_ID
    )
    group_id = response.get("GroupId")

    print("Security Group Id - ", group_id)

    return group_id


def get_my_public_ip():
    external_ip = urllib.request.urlopen("https://ident.me").read().decode("utf8")
    print("Public ip - ", external_ip)

    return external_ip


def add_ssh_access_sg(sg_id, ip_address):
    ip_address = f"{ip_address}/32"

    response = ec2_client.authorize_security_group_ingress(
        CidrIp=ip_address,
        FromPort=22,
        GroupId=sg_id,
        IpProtocol="tcp",
        ToPort=22,
    )
    if response.get("Return"):
        print("Rule added successfully")
    else:
        print("Rule was not added")


def run_ec2(sg_id, subnet_id, instance_name):
    response = ec2_client.run_instances(
        BlockDeviceMappings=[
            {
                "DeviceName": "/dev/sda1",
                "Ebs": {
                    "DeleteOnTermination": True,
                    "VolumeSize": 8,
                    "VolumeType": "gp2",
                    "Encrypted": False,
                },
            },
        ],
        ImageId="ami-053b0d53c279acc90",
        InstanceType="t2.micro",
        KeyName="my-demo-key",
        MaxCount=1,
        MinCount=1,
        Monitoring={"Enabled": True},
        # SecurityGroupIds=[
        #     sg_id,
        # ],
        # SubnetId=subnet_id,
        UserData="""#!/bin/bash
echo "Hello I am from user data" > info.txt
""",
        InstanceInitiatedShutdownBehavior="stop",
        NetworkInterfaces=[
            {
                "AssociatePublicIpAddress": True,
                "DeleteOnTermination": True,
                "Groups": [
                    sg_id,
                ],
                "DeviceIndex": 0,
                "SubnetId": subnet_id,
            },
        ],
    )

    for instance in response.get("Instances"):
        instance_id = instance.get("InstanceId")
        print("InstanceId - ", instance_id)
    # pprint(response)

    # Create a name tag for the instance
    tag = {"Key": "Name", "Value": instance_name}

    # Assign the name tag to the instance
    ec2_client.create_tags(Resources=[instance_id], Tags=[tag])

    return None


def stop_ec2(instance_id):
    response = ec2_client.stop_instances(
        InstanceIds=[
            instance_id,
        ],
    )
    for instance in response.get("StoppingInstances"):
        print("Stopping instance - ", instance.get("InstanceId"))


def start_ec2(instance_id):
    response = ec2_client.start_instances(
        InstanceIds=[
            instance_id,
        ],
    )
    for instance in response.get("StartingInstances"):
        print("Starting instance - ", instance.get("InstanceId"))


def terminate_ec2(instance_id):
    response = ec2_client.terminate_instances(
        InstanceIds=[
            instance_id,
        ],
    )
    for instance in response.get("TerminatingInstances"):
        print("Terminating instance - ", instance.get("InstanceId"))


def main():
    # chmod 400 my-demo-key.pem
    create_key_pair("my-demo-key")

    #  # VPC AND SECURITY_GROUP
    # vpc_id = "vpc-04ea3928999702acc"
    # subnet_id = "subnet-0c3792077ac1e7a11"
    # my_ip = get_my_public_ip()
    # security_group_id = create_security_group(
    #   "ec2-sg", "Security group to enable access on ec2", vpc_id)

    # only concrete ip rule
    # add_ssh_access_sg(security_group_id, my_ip)

    #  # EC2
    # run_ec2(security_group_id, subnet_id, 'btu-custom-instance')

    # stop_ec2('i-0494e0d49bf8a5b43')
    # start_ec2('i-0494e0d49bf8a5b43')
    # terminate_ec2("i-0d291c92367b5ca33")


if __name__ == "__main__":
    main()
