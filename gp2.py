import boto3

# prompt for user profile
profile = input('AWS CLI profile to use, eg - "default" or "prod":\n  > ')
if len(profile) == 0:
    raise Exception('Invalid profile name')

aws_session = boto3.Session(
    profile_name=profile,
    region_name='ap-southeast-2'
)

# get ec2 client
client = aws_session.client('ec2')

# get a list of volume ids that are gp2
vols   = []

volids = client.describe_volumes()
for vol in volids['Volumes']:
    if vol['VolumeType'] == 'gp2':
        vols.append(vol['VolumeId'])
while 'NextToken' in volids.keys() and len(volids['NextToken']) > 0:
    volids = client.describe_volumes()
    for vol in volids['Volumes']:
        if vol['VolumeType'] == 'gp2':
            vols.append(vol['VolumeId'])
print(vols)

# taggyboy = input('Please enter App name\n > ')
# vol_data  = []
# volids    = client.describe_volumes()
# vol_data += volids['Volumes']
# while 'NextToken' in volids.keys() and len(volids['NextToken']) > 0:
#     volids    = client.describe_volumes()
#     vol_data += volids['Volumes']
# for vol in vol_data:
#     if vol['VolumeType'] == 'gp2' and 'Tags' in vol.keys():
#         found = False
#         for tag in vol['Tags']:
#             if tag['Key'] == 'App':
#                 App = tag['Value']
#             if tag['Key'] == 'App' and tag['Value'] == taggyboy:
#                 found = True
#         if found:
#             vols.append(vol['VolumeId'])
#         else:
#             # print('%s is hidden by the Jedi' % App)
#             pass
#     else:
#         print('%s has no tags' % vol['VolumeId'])
# print(vols)

# prompt before converting to GP3
proceed = input('Found %s GP2 Volumes to convert to GP3. Proceed - Y / N?\n  > ' % str(len(vols)))
if proceed not in ['Y','N']:
    raise Exception('Invalid option provided')

elif proceed == 'Y':

# Loop Through each VolumeId

    for gp2 in vols:

        response = client.modify_volume(
            VolumeId=gp2,
            VolumeType='gp3'
        )