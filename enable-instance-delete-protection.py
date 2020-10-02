s program enables terminate protection for manually launched instances. 
It is invoked by CloudWatch when an instance is launched.
Termination prtection is not enabled if an instance is tagged as
TerminationProtection=false.
'''
import json
import boto3
from botocore.exceptions import ClientError
import os


aws_session=None
ec2_resource=None 

if 'LOCAL_RUN' in os.environ and os.environ.get('LOCAL_RUN'):
    aws_session = boto3.session.Session(profile_name=os.environ.get('AWS_PROFILE'))
    ec2_resource = aws_session.resource('ec2',region_name=os.environ.get('AWS_REGION'))
    ec2_client = aws_session.client('ec2',region_name=os.environ.get('AWS_REGION'))
else:
    ec2_resource = boto3.resource('ec2')
    ec2_client = boto3.client('ec2')


def lambda_handler(event,context):
    global ec2_resource
    res:Dict[str,Any]={}
    try:
        if 'detail' not in event or event['detail']['state'] != 'pending':
            print('Do not proceed. This function has to be called when instance state changes to pending.')
        else:
            instance_id:str = event['detail']['instance-id']
            instance = ec2_resource.Instance(instance_id)
            name:str = ''
            termination_protection_tag_value: str = 'true'
            for tag in instance.tags:
                if tag['Key'] == 'Name':
                    name = tag['Value']
                if tag['Key'].lower() == 'terminationprotection':
                    termination_protection_tag_name = tag['Key']
                    termination_protection_tag_value = tag['Value']

            if termination_protection_tag_value.lower() == 'false':
                print(
                    f'Do not enable termination protection as instance {instance_id} of application {name} has a tag as {termination_protection_tag_name}={termination_protection_tag_value}')
            else:
                response = ec2_client.modify_instance_attribute(
                        InstanceId=instance_id,
                        #Attribute='disableApiTermination',
                        DisableApiTermination={
                            'Value': True
                            }
                        )
                print(f'Enabled delete protection for instance {instance_id} of application {name}')
                print(f'{response}')
                
                
            
    except (Exception,ClientError) as err:
        print(err)
        res['Response'] = json.dumps({'Error':f'Aborted because of error.{err}'})
    else:
        res['Response']=json.dumps({'Message':'Success'})
    return res


if __name__=='__main__':
    event = {
        "version": "0",
        "id": "7bf73129-1428-4cd3-a780-95db273d1602",
        "detail-type": "EC2 Instance State-change Notification",
        "source": "aws.ec2",
        "account": "123456789012",
        "time": "2015-11-11T21:29:54Z",
        "region": "us-east-1",
        "resources": [
            "arn:aws:ec2:us-east-1:123456789012:instance/i-abcd1111"
        ],
        "detail": {
            "instance-id": "i-0344d58b8136e5bce",
            "state": "pending"
        }
    }
    context = {}
    lambda_handler(event,context)

