import os

import paramiko
from fabric import Connection

from services import basic_server_config, hysteria, tuic, xr, naive
from services.basic_server_config import sysctl_net_performance_tweak, remove_old_config_paths
from services.get_ssh_client import new_ssh_client


# TODO: naive behind caddy is more tricky because of existing web service
# from services import naive



def deploy_all_proxy_services_on_host(host):
  client, ip = new_ssh_client(host)
  conn = Connection(host)

  basic_server_config.create_user_remote(client)
  # remove_old_config_paths(conn, local_config_dir, remote_config_dir)
  sysctl_net_performance_tweak(conn)
  hysteria.deploy(host, ip, client, conn)
  tuic.deploy(host, ip, client, conn)
  naive_port  = None if host in 'npd lav'.strip().split() else 443
  naive.deploy(host, ip, client, conn, naive_port) # semi-auto
  xr.deploy(host, ip, client, conn)
  client.close()


if __name__ == '__main__':
  host = 'npl'
  deploy_all_proxy_services_on_host(host)
