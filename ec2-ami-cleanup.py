import boto3
import os
import re
from datetime import date,datetime
from dateutil.parser import parse
from botocore.exceptions import ClientError
from botocore.config import Config


config = Config(
    retries = dict(
        max_attempts = 10
    )
)

## The action variable for this script. Options:
# 'dryrun' - reporting only, outputs to CloudWatch
# 'tag' - tags identified AMI's and associated snapshots with the TAG variables
# 'delete' - deregisters identified AMI's and deletes associated snapshots, if the tag variables exist
ACTION = os.environ['ACTION']
TAG = os.environ['TAG_KEY']                          # Variable for Tag key name
TAGVALUE = os.environ['TAG_VALUE']                   # Variable for Tag value
RETENTION = int(os.environ['RETENTION'])             # Retention period in days - any snapshots older than retention will be actioned
AWS_REGION = os.environ['REGION']


def lambda_handler(event, context):

  def diff_age(date):
    get_date_obj=parse(date)
    date_obj=get_date_obj.replace(tzinfo=None)
    diff=datetime.now() - date_obj
    return diff.days


  ec2_client=boto3.client('ec2', region_name=AWS_REGION, config=config)
  # For instance AMI's
  ec2_paginator=ec2_client.get_paginator('describe_instances')
  ec2_response=ec2_paginator.paginate().build_full_result()
  
  # For associated snapshots
  snap_paginator=ec2_client.get_paginator('describe_snapshots')
  snap_resp=snap_paginator.paginate(OwnerIds=['self']).build_full_result()

  # For launch template AMI's
  launch_paginator=ec2_client.get_paginator('describe_launch_templates')
  launch_resp=launch_paginator.paginate().build_full_result()
  
  # For all and shared AMI's
  ec2 = boto3.resource('ec2')
  resp_images=ec2.images.filter(Owners=['self'])

  # For launch config AMI's
  asg_client=boto3.client('autoscaling', region_name=AWS_REGION)
  asg_paginator=asg_client.get_paginator('describe_launch_configurations')
  asg_response=asg_paginator.paginate().build_full_result()


  all_ami=[]
  for ami in resp_images:
    created=str(ami.creation_date)
    age = diff_age(created)
    try:
      if age > RETENTION:
        all_ami.append(ami.image_id)
    except ClientError as e:
      print('ERROR: {}'.format(e))


  excluded_ami=[]

  # Exclude instance AMI's
  for instances in ec2_response['Reservations']:
    inst_ami=instances['Instances'][0]['ImageId']
    int_images=ec2.images.filter(ImageIds=[inst_ami], Owners=['self'])
    for ami in int_images:
      created=str(ami.creation_date)
      age = diff_age(created)
      try:
        if age > RETENTION:
          if ACTION=='dryrun': 
            print('ImageId: {}, CreatedDate: {} is used by existing EC2 instances - excluding'.format(ami.image_id, ami.creation_date))
          excluded_ami.append(ami.image_id)
      except ClientError as e:
        print('ERROR: {}'.format(e))


  # Exclude AWS backup AMI's
  describe=ec2_client.describe_images(Filters=[{'Name': 'tag-key', 'Values': ['aws:backup:source-resource']}],Owners=['self'])
  for ami in describe['Images']:
    created=str(ami['CreationDate'])
    age = diff_age(created)
    try:
      if age > RETENTION:
        if ACTION=='dryrun':
          print('ImageId: {}, CreatedDate: {} is an AWS backup - excluding'.format(ami['ImageId'], ami['CreationDate']))   
        excluded_ami.append(ami['ImageId'])
    except ClientError as e:
      print('ERROR: {}'.format(e))


  # Exclude launch config AMI's
  for ami in asg_response['LaunchConfigurations']:
    if ACTION=='dryrun':
      print('ImageId: {} is in Launch Configurations - excluding'.format(ami['ImageId']))   
    excluded_ami.append(ami['ImageId'])
  

  # Exclude latest launch template AMI's
  for launch in launch_resp['LaunchTemplates']:
    template_id=(launch['LaunchTemplateId']) 
    describe=ec2_client.describe_launch_template_versions(LaunchTemplateId=(template_id), Versions=['$Latest'])
    for version in describe['LaunchTemplateVersions']:
      if ACTION=='dryrun':
        print('ImageId: {} is used in LaunchTemplateId: {}, LatestVersionNo: {} - excluding'.format(version['LaunchTemplateData']['ImageId'], version['LaunchTemplateId'], version['VersionNumber']))
      ami_id=version['LaunchTemplateData']['ImageId']
      excluded_ami.append(ami_id)


  # Exclude AMI's with share permissions
  for ami in resp_images:
    created=str(ami.creation_date)
    age = diff_age(created)
    try:
      if age > RETENTION:
        attrib=ami.describe_attribute(Attribute='launchPermission')
        if attrib['LaunchPermissions']!=[]:
          if ACTION=='dryrun':
            print('ImageId: {} is shared with at least AccountId: {} - excluding'.format(attrib['ImageId'], attrib['LaunchPermissions'][0]['UserId']))
          excluded_ami.append(attrib['ImageId'])
    except ClientError as e:
      print('ERROR: {}'.format(e))


  results = set(all_ami) - set(excluded_ami)


  # Exclude AMI's from results which has a DoNotDelete tag with value true; True; TRUE
  final_amis=[]
  for image in results:
    fin_ami=ec2_client.describe_images(Filters=[{'Name': 'tag-key', 'Values': ['DoNotDelete']}],ImageIds=[image],Owners=['self'])
    if fin_ami['Images']!=[]:
      for f_ami in fin_ami['Images'][0]['Tags']:
        if f_ami['Key']=='DoNotDelete' and f_ami['Value']=='true' or f_ami['Value']=='True' or f_ami['Value']=='TRUE':
          print('ImageId: {} has DoNotDelete tag and is protected - excluding'.format(image))
        # If DoNotDelete tag exists but not true; True; TRUE value - append
        if f_ami['Key']=='DoNotDelete' and f_ami['Value']!='true' and f_ami['Value']!='True' and f_ami['Value']!='TRUE':
          final_amis.append(image)
    else:
      final_amis.append(image)


  # Identify associated snapshots from final_amis
  ami_snapshots=[]
  for ami_snap in final_amis:
    desc_images=ec2_client.describe_images(ImageIds=[ami_snap],Owners=['self'])['Images'][0]['BlockDeviceMappings']
    for images in desc_images:
      if 'Ebs' in images:
        snapshots=ec2_client.describe_snapshots(SnapshotIds=[images['Ebs']['SnapshotId'],],OwnerIds=['self'])['Snapshots'][0]
        ami_snapshots.append(snapshots['SnapshotId'])


  print('########## ACTIONS ##########')

  for amis in final_amis:
    response=ec2_client.describe_images(ImageIds=[amis],Owners=['self'])
    if response['Images']!=[]:
      for ami in response['Images']:
        try:
          if ACTION=='dryrun':
            print('ImageId: {}, CreatedDate: {}, identified for deregistration'.format(ami['ImageId'], ami['CreationDate']))
          if ACTION=='tag':
            ec2_client.create_tags(Resources=([ami['ImageId']]), Tags=[{'Key': TAG, 'Value': TAGVALUE}])
            print('ImageId: {}, CreatedDate: {} is tagged for deregistration'.format(ami['ImageId'], ami['CreationDate']))
          if ACTION=='delete':
            tags=ami['Tags']
            for tag in tags:
              if tag['Key']==TAG and tag['Value']==TAGVALUE:
                try:
                  ec2_client.deregister_image(ImageId=(ami['ImageId']))
                  print('ImageId: {}, CreatedDate: {} has been deregistered'.format(ami['ImageId'], ami['CreationDate']))
                except ClientError as e:
                  print('Error when deregistering ImageId: {} with ERROR: {}'.format(ami['ImageId'], e))
        except ClientError as e:
          print('ERROR: {}'.format(e))


  # Separated from above to improve speed
  for snapshot in ami_snapshots:
    desc_snaps=ec2_client.describe_snapshots(SnapshotIds=[snapshot],OwnerIds=['self'])
    for snap in desc_snaps['Snapshots']:
      try:
        # If the AMI was created from an AWS Backup, exclude EBS snapshot
        if re.findall(r'AWS Backup service', snap['Description']):
          print('SnapshotId: {}, CreatedDate: {} is an AWS Backup - excluding'.format(snap['SnapshotId'], snap['StartTime']))
        else:
          try:
            if ACTION=='dryrun':
              print('SnapshotId: {}, VolumeSize(GB): {}, CreatedDate: {}, identified for deletion'.format(snap['SnapshotId'], snap['VolumeSize'], snap['StartTime']))
            if ACTION=='tag':
              ec2_client.create_tags(Resources=([snap['SnapshotId']]), Tags=[{'Key': TAG, 'Value': TAGVALUE}])
              print('SnapshotId: {}, CreatedDate: {} is tagged for deletion'.format(snap['SnapshotId'], snap['StartTime']))
            if ACTION=='delete':
              tags=snap['Tags']
              for tag in tags:
                if tag['Key']==TAG and tag['Value']==TAGVALUE:
                  try:
                    ec2_client.delete_snapshot(SnapshotId=(snap['SnapshotId']))
                    print('SnapshotId: {}, CreatedDate: {} has been deleted'.format(snap['SnapshotId'], snap['StartTime']))
                  except ClientError as e:
                    if e.response['Error']['Code']=='InvalidSnapshot.InUse':
                      print('SnapshotId: {} in use. {}'.format(snap['SnapshotId'], e))
                    else:
                      print('Error when deleting AMI SnapshotId: {}, CreatedDate: {} with ERROR: {}'.format(snap['SnapshotId'], snap['StartTime'], e))
          except ClientError as e:
            print('ERROR: {}'.format(e))
      except ClientError as e:
        print('ERROR: {}'.format(e))

