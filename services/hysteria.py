import logging
import os
import random
from pathlib import Path
import secrets

import fabric
import paramiko

from services.common import masquerade_domain_pool, HY_P2, HY_P1, HY_P3, HY_P4, HY_P5
from services.get_ssh_client import new_ssh_client
from services.rcgen import gen_key_cer
from services.local_port_num_generator import generate_local_port

bandwidth = '48'

def deploy(host: str, ip: str, client: paramiko.SSHClient = None, conn: fabric.Connection = None, remote_port=None,
           password=None,
           should_close_client=False):
  if client is None:
    client = new_ssh_client(host)
    should_close_client = True
  if conn is None:
    conn = fabric.Connection(host)
  ftp = client.open_sftp()

  # use privileged ports to prevent conflict with outgoing services
  if remote_port is None:
    remote_port = random.randrange(HY_P1, HY_P2)

  # port hop is error-prone
  # aux_port_range = []
  # aux_port_range.append(random.randrange(HY_P3, HY_P4))
  # aux_port_range.append(random.randrange(aux_port_range[-1] + 80, HY_P5))
  # aux_port_range = [str(i) for i in aux_port_range]
  # aux_port_range_yaml = ',' + '-'.join(aux_port_range[-2:])
  aux_port_range_yaml = ''
  # aux_port_range_iptables = ':'.join(aux_port_range[-2:])
  # for suf in ['', '6']:
  #   conn.run(
  #     f'iptables{suf} -t nat -A PREROUTING -i eth0 -p udp --dport {aux_port_range_iptables} -j DNAT --to-destination :{port}')

  assert isinstance(remote_port, int)
  if password is None:
    password_length = random.randrange(22, 31)
    password = secrets.token_urlsafe(password_length)
  assert isinstance(password, str)

  target_masq_domain = random.choice(masquerade_domain_pool)
  target_masq_url = f'https://{target_masq_domain}/'
  remote_config_dir = Path('/etc/hys')
  conn.run(f'mkdir -p {remote_config_dir}')

  cer, key = gen_key_cer(target_masq_domain)

  cer_path = f'/etc/hys/{remote_port}.cer.pem'
  file = ftp.file(cer_path, "w")
  file.write(cer)
  file.flush()

  key_path = f'/etc/hys/{remote_port}.key.pem'
  file = ftp.file(key_path, "w")
  file.write(key)
  file.flush()

  config_extension = '.yaml'
  remote_config_path = remote_config_dir / f'{remote_port}{config_extension}'
  remote_config_content = f'''
listen: :{remote_port}

tls:
  cert: {cer_path}
  key: {key_path}

auth:
  type: password
  password: {password}
masquerade: 
  type: proxy
  proxy:
    url: {target_masq_url} 
    rewriteHost: true
'''.lstrip()
  file = ftp.file(str(remote_config_path), "w")
  file.write(remote_config_content)
  file.flush()

  remote_bin_path = '/usr/bin/hy'
  ftp.put('/usr/bin/hysteria', remote_bin_path)

  remote_service_path = '/etc/systemd/system/hys@.service'
  remote_service_content = f'''
[Unit]
Description=hys
After=network.target

[Service]
Type=simple
User=caddy
Group=caddy
ExecStart={remote_bin_path} server --config {remote_config_dir}/%i{config_extension} --disable-update-check
WorkingDirectory=~
User=caddy
Group=caddy
Environment=HYSTERIA_LOG_LEVEL=info
Environment=HYSTERIA_ACME_DIR=/var/lib/hysteria/acme
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE CAP_NET_RAW
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE CAP_NET_RAW
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
'''.lstrip()
  file = ftp.file(remote_service_path, "w")
  file.write(remote_service_content)
  file.flush()

  local_config_dir = Path('/etc/hyc')
  local_port = generate_local_port(host, __file__)
  local_cert_path = local_config_dir / f'{host}{remote_port}.cer.pem'
  with open(local_cert_path, 'w') as f:
    f.write(cer)

  with open(local_config_dir / f'{host}{remote_port}{config_extension}', 'w') as f:
    # mind yaml indentation
    f.write(f'''
server: {ip}:{remote_port}{aux_port_range_yaml}

auth: {password}

bandwidth:
  up: {bandwidth} mbps
  down: {bandwidth} mbps

socks5:
  listen: 127.0.0.1:{local_port}

tls:
  sni: localhost
  insecure: false
  ca: {local_cert_path}

transport:
  udp:
    hopInterval: 25s 
  '''.lstrip())

  local_service_path = '/etc/systemd/system/hyc@.service'
  local_bin_path = '/usr/bin/hysteria'
  local_service_content = f'''
[Unit]
Description=Hysteria Client Service
Documentation=hysteria.network/
After=network.target

[Service]
Type=simple
User=tr
Group=tr
ExecStart={local_bin_path} client --config {local_config_dir}/%i{config_extension} --disable-update-check
WorkingDirectory=~
User=caddy
Group=caddy
Environment=HYSTERIA_LOG_LEVEL=info
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE CAP_NET_RAW
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE CAP_NET_RAW
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
'''.lstrip()
  with open(local_service_path, 'w') as f:
    f.write(local_service_content)
  remote_systemd_service_name = f'{remote_port}'

  local_systemd_service_name = f'{host}{remote_port}'
  conn.run(f'systemctl enable --now {remote_systemd_service_name}.service')
  os.system(f'systemctl enable --now {local_systemd_service_name}.service')

  ftp.close()
  if should_close_client:
    client.close()