import boto3
​session = boto3.Session(profile_name='uon-nonprod', region_name='ap-southeast-2')
launchconf = session.client('autoscaling')

launch_configs   = launchconf.describe_launch_configurations()
tmplaunchconfigs = launch_configs['LaunchConfigurations']

auto_configs   = launchconf.describe_auto_scaling_groups()
tmpautoconfigs = auto_configs['AutoScalingGroups']

launchconfigsall   = []
launchconfigsinuse = []
launchconfigsfinal = []

while 'NextToken' in launch_configs.keys():
    launch_configs    = launchconf.describe_launch_configurations(NextToken=launch_configs['NextToken'])
    tmplaunchconfigs += launch_configs['LaunchConfigurations']

while 'NextToken' in auto_configs.keys():
    auto_configs    = launchconf.describe_auto_scaling_groups(NextToken=auto_configs['NextToken'])
    tmpautoconfigs += auto_configs['AutoScalingGroups']

for config in tmplaunchconfigs:
    launchconfigsall.append(config['LaunchConfigurationName'])

for config in tmpautoconfigs:
    if 'LaunchConfigurationName' in config.keys():
        launchconfigsinuse.append(config['LaunchConfigurationName'])

for config in launchconfigsall:
    if not config in launchconfigsinuse:
        launchconfigsfinal.append(config)

for config in launchconfigsfinal:
    launchconf.delete_launch_configuration(LaunchConfigurationName=config)