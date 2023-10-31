import logging
import os
import random
import uuid
from pathlib import Path
import secrets

import fabric
import paramiko

from services.common import masquerade_domain_pool, NAIVE_P1, NAIVE_P2, LEN_PASSWD_MIN, LEN_PASSWD_MAX, local_user, \
  common_permission_job
from services.get_ssh_client import new_ssh_client
from services.local_port_num_generator import generate_local_port


def deploy(host: str, ip: str, client: paramiko.SSHClient = None, conn: fabric.Connection = None, port=None,
           password=None,
           should_close_client=False):
  if client is None:
    client = new_ssh_client(host)
    should_close_client = True
  if conn is None:
    conn = fabric.Connection(host)
  ftp = client.open_sftp()

  # use privileged ports to prevent conflict with outgoing services
  if port is None:
    port = random.randrange(NAIVE_P1, NAIVE_P2)

  assert isinstance(port, int)
  if password is None:
    password_length = random.randrange(LEN_PASSWD_MIN, LEN_PASSWD_MAX)
    password = secrets.token_urlsafe(password_length)
  assert isinstance(password, str)

  target_masq_domain = random.choice(masquerade_domain_pool)
  target_masq_url = f'https://{target_masq_domain}/'
  remote_config_dir = Path('/etc/caddy')
  conn.run(f'mkdir -p {remote_config_dir}')

  remote_config_path = remote_config_dir / f'forwardp'
  u1 = uuid.uuid4()

  remote_config_content = f'''
forward_proxy {{
          basic_auth {u1} {password}
          hide_ip
          hide_via
          probe_resistance
}}
'''.lstrip()
  file = ftp.file(str(remote_config_path), "w")
  file.write(remote_config_content)
  file.flush()

  remote_bin_path = '/usr/bin/caddy'
  ftp.put('/usr/bin/caddy', remote_bin_path)
  remote_service_name = 'cd'
  remote_service_path = f'/etc/systemd/system/{remote_service_name}@.service'
  remote_service_content = f'''
[Unit]
Description=Caddy
After=network.target network-online.target
Requires=network-online.target

[Service]
User=caddy
Group=caddy
Environment="ASSUME_NO_MOVING_GC_UNSAFE_RISK_IT_WITH=go1.20"
ExecStart=/usr/bin/caddy run --environ --config /etc/caddy/Caddyfile
ExecReload=/usr/bin/caddy reload --config /etc/caddy/Caddyfile
TimeoutStopSec=5s
LimitNOFILE=1048576
LimitNPROC=512
PrivateTmp=true
ProtectSystem=full
AmbientCapabilities=CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
'''.lstrip()
  file = ftp.file(remote_service_path, "w")
  file.write(remote_service_content)
  file.flush()

  local_config_dir = Path('/etc/np')
  local_config_dir.mkdir(exist_ok=True, parents=True)

  local_port = generate_local_port(host, __file__)
  config_extension = '.json'
  domain_name = 'x.com'  # MANUAL domain edit
  with open(local_config_dir / f'{host}{port}{config_extension}', 'w') as f:
    f.write(f'''
{{
  "listen": "socks://127.0.0.1:{local_port}",
  "proxy": "https://{u1}:{password}@{domain_name}",
  "host-resolver-rules": "MAP {domain_name} {ip}",
  "log-net-log": "",
  "log": ""
}}

  '''.lstrip())
  local_service_name = 'np'
  local_service_path = f'/etc/systemd/system/{local_service_name}@.service'
  local_bin_path = '/usr/bin/naive'
  local_service_content = f'''
[Unit]
Description=NaiveProxy Server Service
After=network-online.target

[Service]
Type=simple
User={local_user}
Restart=on-failure
RestartSec=5s
ExecStart={local_bin_path} {local_config_dir}/%i{config_extension}
# Proc filesystem
ProcSubset=pid
ProtectProc=invisible
# Capabilities
CapabilityBoundingSet=
# Security
NoNewPrivileges=true
# Sandboxing
ProtectSystem=strict
PrivateTmp=true
PrivateDevices=true
PrivateUsers=true
ProtectHostname=true
ProtectKernelLogs=true
ProtectKernelModules=true
ProtectKernelTunables=true
ProtectControlGroups=true
ProtectHome=true
RestrictAddressFamilies=AF_INET
RestrictAddressFamilies=AF_INET6
RestrictAddressFamilies=AF_NETLINK
RestrictAddressFamilies=AF_UNIX
RestrictNamespaces=true
LockPersonality=true
RestrictRealtime=true
RestrictSUIDSGID=true
RemoveIPC=true
PrivateMounts=true
ProtectClock=true
# System Call Filtering
SystemCallArchitectures=native
SystemCallFilter=~@cpu-emulation @debug @keyring @ipc @mount @obsolete @privileged @setuid
SystemCallFilter=pipe
SystemCallFilter=pipe2

[Install]
WantedBy=default.target
'''.lstrip()
  with open(local_service_path, 'w') as f:
    f.write(local_service_content)
  remote_systemd_service_name = 'cd'
  local_systemd_service_name = f'{host}{port}'
  common_permission_job(conn, remote_bin_path, remote_config_dir, local_bin_path, local_config_dir, remote_service_name, remote_systemd_service_name, local_service_name, local_systemd_service_name)

  ftp.close()
  if should_close_client:
    client.close()
