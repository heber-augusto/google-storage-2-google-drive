
gdfuse_config_path = os.environ['GDFUSE_CONFIG_PATH']
team_drive_id = os.environ['TEAM_DRIVER_ID']


with open(gdfuse_config_path, 'r') as fd:
    config_content = fd.readlines()

with open(gdfuse_config_path, 'w') as fd2:
    for content in config_content:
        if content.find('team_drive_id=') >= 0:
            fd2.write(f'team_drive_id={team_drive_id}\n')
        else:
            fd2.write(content)
