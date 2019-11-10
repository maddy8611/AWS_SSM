import boto3
import botocore
import sys, json


def ec2_list_of_instances(ec2_conn_obj, tagname):
    """
    :param ec2_conn_obj:
    :return:
    """
    try:
        ec2_describe_response = ec2_conn_obj.describe_instances()
    except botocore.exceptions.EndpointConnectionError as err:
        print("Error:- Couldn't connect to the internet Please check the network setting")
        sys.exit(1)
    all_inst_dict_tolist = []
    for reservation in ec2_describe_response["Reservations"]:
        for instance in reservation["Instances"]:
            each_inst_dict = dict()
            each_inst_dict["InstanceId"] = instance["InstanceId"]
            if instance.get("Platform") == "windows":
                tag_value = "WINDOWSTAGGOESHERE"
            else:
                tag_value = "LINUXTAGGOESHERE"
            each_inst_dict["to_be_added_tag"] = {tagname: tag_value}
            all_tags = {}
            for each_tag in instance.get("Tags", {}):
                all_tags[each_tag["Key"]] = each_tag["Value"]
            each_inst_dict["existing_tags"] = all_tags

            all_inst_dict_tolist.append(each_inst_dict)
    return all_inst_dict_tolist

def add_tags(ec2_conn_obj,tag_info):
    tags = []
    for each_item in tag_info["to_be_added_tag"]:
        item1 = {"Key": each_item, "Value": tag_info["to_be_added_tag"][each_item]}
        tags.append(item1)
    response = ec2_conn_obj.create_tags(
        Resources=[
            tag_info["InstanceId"]
        ],
        Tags=tags,
    )
    return response


def lambda_handler(event,context):
    tagname = "Patch Group"
    try:
        ec2_conn_obj = boto3.client('ec2')
    except botocore.exceptions.NoCredentialsError:
        print("Unable to locate default credentials. Configure credentials")
        ec2_conn_obj = boto3.client(
            'ec2',
            aws_access_key_id="",
            aws_secret_access_key=""
        )
    tags_info = ec2_list_of_instances(ec2_conn_obj,tagname)
    response = []
    for each_item in tags_info:
        # Change the text from "AutoScaling" to ignore the value for the tag
        if each_item["existing_tags"].get(tagname) != "AutoScaling":
            if each_item["to_be_added_tag"].items() <= each_item["existing_tags"].items():
                response.append("Tags Exists for " + each_item["InstanceId"])
            else:
                response.append("Tags doesn't Exists for " + each_item["InstanceId"])
                response.append(add_tags(ec2_conn_obj, each_item))
    return {
        'statusCode': 200,
        'body': json.dumps(str(response))
    }


if __name__ == "__main__":
    print(lambda_handler({}, {}))
