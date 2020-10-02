import boto3
import os
import re
from datetime import date,datetime
from dateutil.parser import parse
from botocore.exceptions import ClientError


## The action variable for this script. Options:
# 'dryrun' - reporting only, outputs to CloudWatch
# 'tag' - tags identified snapshots with TAG variable
# 'delete' - deletes identified snapshots, if tag value is true
ACTION = os.environ['ACTION']
TAG = os.environ['TAG_KEY']                          # Variable for Tag key name
RETENTION = int(os.environ['RETENTION'])             # Retention period in days - any snapshots older than retention will be actioned
AWS_REGION = os.environ['REGION']


def lambda_handler(event, context):

  def diff_age(date):
    get_date_obj=parse(date)
    date_obj=get_date_obj.replace(tzinfo=None)
    diff=datetime.now() - date_obj
    return diff.days


  ec2_client=boto3.client('ec2', region_name=AWS_REGION)
  ec2_paginator=ec2_client.get_paginator('describe_snapshots')
  response=ec2_paginator.paginate(OwnerIds=['self']).build_full_result()


  all_snapshots=[]
  for snap in response['Snapshots']:
    created=str(snap['StartTime'])
    age = diff_age(created)
    try:
      if age > RETENTION:
        all_snapshots.append(snap['SnapshotId'])
    except ClientError as e:
      print('ERROR: {}'.format(e))


  print('########## EXCLUDED SNAPSHOTS ##########')

  excluded_snapshots=[]
  describe=ec2_client.describe_snapshots(Filters=[{'Name': 'tag-key', 'Values': ['aws:backup:source-resource']}],OwnerIds=['self'])
  for snapshotid in describe['Snapshots']:
    created=str(snapshotid['StartTime'])
    age = diff_age(created)
    try:
      if age > RETENTION:
        print('SnapshotId: {}, CreatedDate: {} is an AWS backup - excluding'.format(snapshotid['SnapshotId'], snapshotid['StartTime']))
        excluded_snapshots.append(snapshotid['SnapshotId'])
    except ClientError as e:
      print('ERROR: {}'.format(e))
  for snap in response['Snapshots']:
    created=str(snap['StartTime'])
    age = diff_age(created)
    try:
      if age > RETENTION:
        if re.match(r'Created by CreateImage*', snap['Description']):
          print('SnapshotID: {}, CreatedDate: {} was created by an AMI - excluding'.format(snap['SnapshotId'], snap['StartTime']))
          excluded_snapshots.append(snap['SnapshotId'])
        if re.match(r'Copied for DestinationAmi*', snap['Description']):
          print('SnapshotID: {}, CreatedDate: {} was created by a copied AMI - excluding'.format(snap['SnapshotId'], snap['StartTime']))
          excluded_snapshots.append(snap['SnapshotId'])
    except ClientError as e:
      print('ERROR: {}'.format(e))


  results = set(all_snapshots) - set(excluded_snapshots)


  print('########## ACTIONS ##########')

  for snapshots in results:
    describe=ec2_client.describe_snapshots(SnapshotIds=[snapshots],OwnerIds=['self'])
    for snaps in describe['Snapshots']:
      try:
        if ACTION=='dryrun':
          print('SnapshotId: {},VolumeSize(GB): {},State: {},CreatedDate: {}, identified for deletion'.format(snaps['SnapshotId'], snaps['VolumeSize'], snaps['State'], snaps['StartTime']))
        if ACTION=='tag':
          ec2_client.create_tags(Resources=([snaps['SnapshotId']]), Tags=[{'Key': TAG, 'Value': 'true'}])
          print('SnapshotId: {}, CreatedDate: {} is tagged for deletion'.format(snaps['SnapshotId'], snaps['StartTime']))
        if ACTION=='delete':
          tags=snaps['Tags']
          for tag in tags:
            if tag['Key']==TAG and tag['Value']=='true':
              try:
                ec2_client.delete_snapshot(SnapshotId=(snaps['SnapshotId']))
                print('SnapshotId: {}, CreatedDate: {} has been deleted'.format(snaps['SnapshotId'], snaps['StartTime']))
              except ClientError as e:
                if e.response['Error']['Code']=='InvalidSnapshot.InUse':
                  print('SnapshotId: {} in use. {}'.format(snaps['SnapshotId'], e))
                else:
                  print('Error when deleting SnapshotId: {}, CreatedDate: {} with ERROR: {}'.format(snaps['SnapshotId'], snaps['StartTime'], e))
      except ClientError as e:
        print('ERROR: {}'.format(e))

