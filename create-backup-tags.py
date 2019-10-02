# Purpose:    Tagging of EFS, EBS, RDS and DDB resources for backup
# Deployment: Python3.7 Lambda
# Trigger:    Scheduled from Cloudwatch
# Author:     Dane Stevenson

import boto3

# default lamdbler handler
def lambda_handler(event, context):

    # tag ebs volumes
    result = tag_ebs()
    if not result:
        raise Exception('Failed to tag EBS volumes')

    # tag efs filesystems
    result = tag_efs()
    if not result:
        raise Exception('Failed to tag EFS Filesystems')

    # tag rds instances
    result = tag_rds()
    if not result:
        raise Exception('Failed to tag RDS instances')

    # tag ddb instances
    result = tag_ddb()
    if not result:
        raise Exception('Failed to tag DDB instances')

    # complete
    print('Completed successfully')
    return

# return tags based on resource_type
def tag_definition(resource_type):

    # tag mappings
    required_tags = {
        'ebs' : [
            'Backup',
            'Name'
        ],
        'efs' : [
            'Backup'
        ],
        'rds' : [
            'BackupRds'
        ],
        'ddb' : [
            'Backup'
        ]
    }

    # validate the provided resource type
    if not resource_type in required_tags.keys():
        raise Exception('%s is not defined in tag mappings' % resource_type)

    # return the data
    else:
        return required_tags[resource_type];

# check and tag ebs volumes
def tag_ebs():

    # set changed flag
    changed = False

    # get required tags
    req_tags = tag_definition('ebs')

    # get ec2 client
    client = boto3.client('ec2')

    # get a list of ebs volumes
    response = client.describe_volumes()

    # check for volumes key in return set
    if not 'Volumes' in response.keys():

        raise Exception('Unable to find volumes')

    # check for volumes in return set
    elif len(response['Volumes']) == 0:

        # Nothing to do
        return True;

    # if there are volumes to check
    else:

        # check tags on volumes
        for volume in response['Volumes']:

            # prepare volume payload
            vol_payload = []

            # loop through each required tag
            for req_tag in req_tags:

                # set tag found to false
                found = False

                # check if the volume has tags
                if 'Tags' in volume.keys():

                    # locate required tag
                    for tag in volume['Tags']:

                        # if required tag is found
                        if tag['Key'] == req_tag:
                            found = True
                            break

                # if the tag isnt found update it
                if found == False:

                    # update the backup tag
                    if req_tag == 'Backup':

                        vol_payload.append({
                            'Key'   : req_tag,
                            'Value' : 'Yes'
                        })

                    # update the name
                    elif req_tag == 'Name' and volume['State'] == 'in-use':

                        # find the instance name
                        res = client.describe_instances(
                            InstanceIds = [
                                volume['Attachments'][0]['InstanceId']
                            ]
                        )

                        # if unable to find instance raise error
                        if not 'Reservations' in res.keys() or len(res['Reservations'][0]['Instances']) == 0:

                            raise Exception('Unable to find ec2 instance %s attached to %s' % (
                                volume['Attachments'][0]['InstanceId'],
                                volume['VolumeId']
                            ))

                        # loop through the tags to find name
                        if 'Tags' in res['Reservations'][0]['Instances'][0].keys():
                            for tag in res['Reservations'][0]['Instances'][0]['Tags']:

                                # update the payload if tag found
                                if tag['Key'] == req_tag:

                                    vol_payload.append({
                                        'Key'   : req_tag,
                                        'Value' : tag['Value']
                                    })
                                    break

                    elif req_tag == 'Name':
                        continue

                    else:

                        raise Exception('Invalid tag')

            # if there are tags update them
            if len(vol_payload) > 0:

                # post the updates
                changed = True
                res = client.create_tags(
                    Resources=[
                        volume['VolumeId']
                    ],
                    Tags=vol_payload
                )
                print('EBS - Updated %s tags for: %s' % (str(len(vol_payload)), volume['VolumeId']))

    if changed:
        print('EBS - tags updated')
    else:
        print('EBS - no updates')
    return True;

# check and tag efs file systems
def tag_efs():

    # set changed flag
    changed = False

    # get required tags
    req_tags = tag_definition('efs')

    # get ec2 client
    client = boto3.client('efs')

    # get a list of efs filesystems
    response = client.describe_file_systems()

    # check for volumes key in return set
    if not 'FileSystems' in response.keys():

        raise Exception('Unable to find EFS FileSystems')

    # check for volumes in return set
    elif len(response['FileSystems']) == 0:

        # Nothing to do
        return True;

    # if there are volumes to check
    else:

        # check tags on filesystems
        for filesystem in response['FileSystems']:

            # prepare filesystems payload
            fs_payload = []

            # loop through each required tag
            for req_tag in req_tags:

                # set tag found to false
                found = False

                # check if the filesystems has tags
                if 'Tags' in filesystem.keys():

                    # locate required tag
                    for tag in filesystem['Tags']:

                        # if required tag is found
                        if tag['Key'] == req_tag:
                            found = True
                            break

                # if the tag isnt found update it
                if found == False:

                    # update the backup tag
                    if req_tag == 'Backup':
                        fs_payload.append({
                            'Key'   : req_tag,
                            'Value' : 'Yes'
                        })

            # if there are tags update them
            if len(fs_payload) > 0:

                # post the updates
                changed = True
                res = client.create_tags(
                    FileSystemId=filesystem['FileSystemId'],
                    Tags=fs_payload
                )
                print('EFS - Updated %s tags for: %s' % (str(len(fs_payload)), filesystem['FileSystemId']))

    if changed:
        print('EFS - tags updated')
    else:
        print('EFS - no updates')
    return True;

# check and tag rds instances
def tag_rds():

    # set changed flag
    changed = False

    # get required tags
    req_tags = tag_definition('rds')

    # get ec2 client
    client = boto3.client('rds')

    # get a list of rds instances
    response = client.describe_db_instances()

    # check for rds instances key in return set
    if not 'DBInstances' in response.keys():

        raise Exception('Unable to find RDS instances')

    # check for rds instances in return set
    elif len(response['DBInstances']) == 0:

        # Nothing to do
        return True;

    # if there are rds instances to check
    else:

        # check tags on each rds instances
        for db in response['DBInstances']:

            # get the tags for rds resource
            res = client.list_tags_for_resource(
                ResourceName=db['DBInstanceArn']
            )

            # prepare rds instance payload
            db_payload = []

            # loop through each required tag
            for req_tag in req_tags:

                # set tag found to false
                found = False

                # check if the volume has tags
                if 'TagList' in res.keys():

                    # locate required tag
                    for tag in res['TagList']:

                        # if required tag is found
                        if tag['Key'] == req_tag:
                            found = True
                            break

                # if the tag isnt found update it
                if found == False:

                    # update the backup tag
                    if req_tag == 'BackupRds':

                        db_payload.append({
                            'Key'   : req_tag,
                            'Value' : 'Yes'
                        })

            # if there are tags update them
            if len(db_payload) > 0:

                # post the updates
                changed = True
                res = client.add_tags_to_resource(
                    ResourceName=db['DBInstanceArn'],
                    Tags=db_payload
                )
                print('RDS - Updated %s tags for: %s' % (str(len(db_payload)), db['DBInstanceIdentifier']))

    if changed:
        print('RDS - tags updated')
    else:
        print('RDS - no updates')
    return True;

# check and tag ddb instances
def tag_ddb():

    # set changed flag
    changed = False

    if changed:
        print('DDB - tags updated')
    else:
        print('DDB - no updates')
    return True;
