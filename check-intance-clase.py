'''
The program changes for instance type. If the instance is of
class T then proceed otherwise stop the execution of the state machine.
'''
import boto3
import os
from typing import List,Dict,Any
from pprint import pprint

aws_session = None
ec2_resource = None
cw_client = None


if 'LOCAL_RUN' in os.environ and os.environ.get('LOCAL_RUN'):
    aws_session = boto3.session.Session(profile_name=os.environ.get('AWS_PROFILE'))

    ec2_resource = aws_session.resource('ec2', region_name=os.environ['AWS_REGION'])
    cw_client = aws_session.client('cloudwatch', region_name=os.environ['AWS_REGION'])
else:
    ec2_resource = boto3.resource('ec2')
    cw_client = boto3.client('cloudwatch')



def lambda_handler(event,context):
    global cw_client
    global ec2_resource

    
    try:
        if 'UPDATE' not in event:
            event['UPDATE']='False'

        instance_id:str = event['detail']['instance-id']
        state:str = event['detail']['state']
        print(f'Triggered by {state} state notification of instance {instance_id}')
        instance = ec2_resource.Instance(instance_id)
        instance_type = instance.instance_type
        first_character_of_instane_type = instance_type[0]
        if first_character_of_instane_type != 't':
            print(f'Do not create CPUCreditBalance alarm as instance {instance_id} is of type {instance_type}')
            event['T_CLASS_EC2'] = False
        else:
            event['T_CLASS_EC2'] = True
        print(f'{instance_type}')
        first_two_character_of_type:str = instance_type[0:2]
        
        print(f'Instance class: {first_two_character_of_type}')


    except Exception as err:
        print(err)
        print('Aborted because of above error')
        return {'status':'Failed'}
    else:
        print('Successfully completed')
        pprint(event,indent=4)
        return event

if __name__ == '__main__':
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
      "instance-id": "i-0af1c4f01dc872da6",
      "state": "pending"
    }
    ,"UPDATE":"False"
    }
    context = {}
    lambda_handler(event,context)

