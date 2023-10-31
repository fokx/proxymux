import importlib
import os
from pathlib import Path

import paramiko
from fabric import Connection

from services.common import remote_user
from fabric import Connection


def create_user_remote(host):
  cmd = f'''
    groupadd --system {remote_user}
    useradd --system \
      --gid {remote_user} \
      --create-home \
      --home-dir /var/lib/{remote_user} \
      --shell /usr/sbin/nologin \
      --comment "{remote_user} web server" \
      {remote_user}
    '''
  if isinstance(host, str):
    result = Connection(host).run(cmd, hide=True)
    msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
    print(msg.format(result))
  else:
    assert isinstance(host, paramiko.SSHClient)
    stdin, stdout, stderr = host.exec_command(cmd)
    for line in stdout.readlines():
      print(line)


def sysctl_net_performance_tweak(conn: Connection):
  path = '/etc/sysctl.d/99-netperf.conf'
  content = '''
net.core.netdev_max_backlog = 16384
net.core.somaxconn = 8192

net.core.rmem_default = 1048576
net.core.rmem_max = 16777216
net.core.wmem_default = 1048576
net.core.wmem_max = 16777216
net.core.optmem_max = 65536
net.ipv4.tcp_rmem = 4096 1048576 2097152
net.ipv4.tcp_wmem = 4096 65536 16777216

net.ipv4.udp_rmem_min = 8192
net.ipv4.udp_wmem_min = 8192

#net.ipv4.tcp_fastopen = 3

net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.tcp_max_tw_buckets = 2000000
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 10
net.ipv4.tcp_slow_start_after_idle = 0

net.ipv4.tcp_keepalive_time = 60
net.ipv4.tcp_keepalive_intvl = 10
net.ipv4.tcp_keepalive_probes = 6

net.ipv4.tcp_mtu_probing = 1
net.ipv4.tcp_base_mss = 1024

net.core.default_qdisc = cake
net.ipv4.tcp_congestion_control = bbr

net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0

net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
'''.lstrip()

  ftp = conn.sftp()
  file = ftp.file(path, "w")
  file.write(content)
  file.flush()
  conn.run('sysctl --system')

  ftp.close()


def remove_old_config_paths(conn, local_config_dir, remote_config_dir):
  for i in 'hysteria tuic xr'.strip().split():
    os.system(f'rm -rf {local_config_dir}')
    conn.run(f'rm -rf {remote_config_dir}')

# if __name__ == '__main__':
#     create_caddy('e')
