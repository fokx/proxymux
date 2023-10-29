import os

import paramiko
from fabric import Connection

from services import basic_server_config
from services import hysteria
from services import tuic
from services import xray
from services.get_ssh_client import new_ssh_client


# TODO: naive behind caddy is more tricky because of existing web service
# from services import naive

def deploy_all(host):
  client, ip = new_ssh_client(host)
  conn = Connection(host)

  # basic_server_config.create_caddy(ssh)
  hysteria.deploy(host, ip, client, conn)
  tuic.deploy()
  xray.deploy()
  # naive.deploy()
  client.close()


if __name__ == '__main__':
  host = 'npl'
  deploy_all(host)
