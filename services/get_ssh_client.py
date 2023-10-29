import os

import paramiko


def new_ssh_client(host):
  client = paramiko.SSHClient()
  client._policy = paramiko.WarningPolicy()
  client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

  ssh_config = paramiko.SSHConfig()
  user_config_file = os.path.expanduser("~/.ssh/config")
  if os.path.exists(user_config_file):
    with open(user_config_file) as f:
      ssh_config.parse(f)

  cfg = {'hostname': host}

  user_config = ssh_config.lookup(cfg['hostname'])
  ip = user_config['hostname']
  for k in ('hostname', 'port'):
    if k in user_config:
      cfg[k] = user_config[k]
  if 'identityfile' in user_config:
    cfg['key_filename'] = user_config['identityfile']
  if 'user' in user_config:
    cfg['username'] = user_config['user']
  if 'proxycommand' in user_config:
    cfg['sock'] = paramiko.ProxyCommand(user_config['proxycommand'])

  client.connect(**cfg)
  return client, ip
