import boto3
from datetime import datetime, timedelta

# prompt for user profile
profile = input('AWS CLI profile to use, eg - uon-nonprod:\n  > ')
if len(profile) == 0:
    raise Exception('Invalid profile name')

aws_session = boto3.Session(
    profile_name=profile,
    region_name='ap-southeast-2'
)

# get backup client
client = aws_session.client('backup')

# prompt for timedelta
tdelta = input('How many days of backups do you want to retain? eg - 60:\n  > ')
try:
    tdelta = datetime.today() - timedelta(days=float(tdelta))
except:
    raise Exception('Invalid time delta provided')

# get a list of vaults
vaults = client.list_backup_vaults()

# loop through each vault
backupjobs = []
for vault in vaults['BackupVaultList']:

    response  = client.list_recovery_points_by_backup_vault(
                    BackupVaultName=vault['BackupVaultName'],
                    ByCreatedBefore=tdelta
                )
    backupjobs += response['RecoveryPoints']
    while 'NextToken' in response.keys():
        response  = client.list_recovery_points_by_backup_vault(
                        BackupVaultName=vault['BackupVaultName'],
                        ByCreatedBefore=tdelta,
                        NextToken=response['NextToken']
                    )
        backupjobs += response['RecoveryPoints']

# prompt before deleting
proceed = input('Found %s backup restore points to delete. Proceed - Y / N?\n  > ' % str(len(backupjobs)))
if proceed not in ['Y','N']:
    raise Exception('Invalid option provided')

elif proceed == 'Y':

    for point in backupjobs:

        response = client.delete_recovery_point(
            BackupVaultName=point['BackupVaultName'],
            RecoveryPointArn=point['RecoveryPointArn']
        )
        print('Deleted - BackupPoint: %s, Vault:%s, Resource:%s, Type: %s' % (
            point['RecoveryPointArn'],
            point['BackupVaultName'],
            point['ResourceArn'],
            point['ResourceType']
        ))
