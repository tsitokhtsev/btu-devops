from cfnlint.rules import CloudFormationLintRule
from cfnlint.rules import RuleMatch

INSTANCE_TYPE = "AWS::EC2::Instance"
VOLUME_TYPE = "AWS::EC2::Volume"
BUCKET_TYPE = "AWS::S3::Bucket"

class CustomTagRules(CloudFormationLintRule):
    id = "W9001"
    shortdesc = "Custom rules for resource tags and configurations"
    description = "Enforces custom tagging policies based on resource properties."
    RESOURCES = [INSTANCE_TYPE, VOLUME_TYPE, BUCKET_TYPE]

    def match(self, cfn):
        matches = []
        resources = cfn.get_resources(self.RESOURCES)

        for resource_name, resource in resources.items():
            resource_type = resource.get("Type")
            properties = resource.get("Properties", {})

            if not properties:
                continue

            tags = properties.get("Tags", [])
            tag_map = {tag["Key"]: tag["Value"] for tag in tags if isinstance(tag, dict)}

            if resource_type == INSTANCE_TYPE:
                instance_type = properties.get("InstanceType")

                if instance_type == "t2.micro":
                    if tag_map.get("FreeTierEligible") != "true":
                        message = f"EC2 Instance "{resource_name}" is t2.micro, but is missing Tag FreeTierEligible with value "true"."
                        matches.append(RuleMatch(["Resources", resource_name, "Properties", "InstanceType"], message))

                elif instance_type == "m5.large":
                    critical_tag = tag_map.get("PerformanceCritical")
                    if critical_tag not in ["true", "false"]:
                        message = f"EC2 Instance "{resource_name}" is m5.large, but is missing Tag PerformanceCritical with value "true" or "false"."
                        matches.append(RuleMatch(["Resources", resource_name, "Properties", "InstanceType"], message))

            if resource_type == VOLUME_TYPE:
                volume_type = properties.get("VolumeType")

                if volume_type == "gp3":
                    priority_value = tag_map.get("Priority")
                    is_valid = False

                    if priority_value is not None:
                        try:
                            priority_int = int(priority_value)
                            if 3000 <= priority_int <= 16000:
                                is_valid = True
                        except ValueError:
                            pass

                    if not is_valid:
                        message = f"Volume "{resource_name}" is gp3, but Tag Priority is missing or its value ({priority_value}) is not between 3000 and 16000."
                        matches.append(RuleMatch(["Resources", resource_name, "Properties", "VolumeType"], message))

            if resource_type == BUCKET_TYPE:
                public_access_block = properties.get("PublicAccessBlockConfiguration", {})

                is_public_allowed_in_config = any(
                    public_access_block.get(prop) is False
                    for prop in ["BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy", "RestrictPublicBuckets"]
                )

                if is_public_allowed_in_config:
                    if tag_map.get("PublicAccessAllowed") != "true":
                        message = f"S3 Bucket "{resource_name}" has public access block disabled, but is missing Tag PublicAccessAllowed with value "true"."
                        matches.append(RuleMatch(["Resources", resource_name, "Properties", "PublicAccessBlockConfiguration"], message))

        return matches
