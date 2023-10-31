import logging
import os
import random
import uuid
from pathlib import Path
import secrets

import fabric
import paramiko

from services.common import masquerade_domain_pool, TUIC_P1, TUIC_P2, LEN_PASSWD_MIN, LEN_PASSWD_MAX, remote_user, \
  local_user, common_permission_job
from services.get_ssh_client import new_ssh_client
from services.rcgen import gen_key_cer
from services.local_port_num_generator import generate_local_port
local_config_dir = Path('/etc/tuicc')
remote_config_dir = Path('/etc/tuics')


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
    remote_port = random.randrange(TUIC_P1, TUIC_P2)

  assert isinstance(remote_port, int)
  if password is None:
    password_length = random.randrange(LEN_PASSWD_MIN, LEN_PASSWD_MAX)
    password = secrets.token_urlsafe(password_length)
  assert isinstance(password, str)

  target_masq_domain = random.choice(masquerade_domain_pool)
  conn.run(f'mkdir -p {remote_config_dir}')

  cer, key = gen_key_cer(target_masq_domain)

  cer_path = f'/etc/tuics/{remote_port}.cer.pem'
  file = ftp.file(cer_path, "w")
  file.write(cer)
  file.flush()

  key_path = f'/etc/tuics/{remote_port}.key.pem'
  file = ftp.file(key_path, "w")
  file.write(key)
  file.flush()

  config_extension = '.json'
  remote_config_path = remote_config_dir / f'{remote_port}{config_extension}'
  u1 = uuid.uuid4()
  u2 = uuid.uuid4()
  # warning: Almost the same password is use!
  remote_config_content = f'''
{{
    "server": "[::]:{remote_port}",
    "users": {{
        "{u1}": "{password}",
        "{u2}": "{password}JUu1290"
    }},
    "alpn": ["h3"],
    "congestion_control": "bbr",
    "certificate": "{cer_path}",
    "private_key": "{key_path}",
    "udp_relay_ipv6": true,
    "zero_rtt_handshake": false,
    "auth_timeout": "9s",
    "dual_stack": true,
    "max_idle_time": "10s",
    "task_negotiation_timeout": "9s",
    "max_external_packet_size": 1500,
    "gc_interval": "9s",
    "receive_window": 8388608,
    "send_window": 16777216,
    "gc_lifetime": "15s",
    "log_level": "info"
}}
'''.lstrip()
  file = ftp.file(str(remote_config_path), "w")
  file.write(remote_config_content)
  file.flush()

  remote_bin_path = '/usr/bin/tuics'
  ftp.put('/f/tuic/target/x86_64-unknown-linux-musl/release/tuic-server', remote_bin_path)
  remote_service_name = 'tuics'
  remote_service_path = f'/etc/systemd/system/{remote_service_name}@.service'
  remote_service_content = f'''
  [Unit]
Description=TUICserver
Documentation=https://github.com/EAimTY/tuic/
After=network.target network-online.target
Requires=network-online.target

[Service]
User={remote_user}
Group={remote_user}
ExecStart={remote_bin_path} -c {remote_config_dir}/%i{config_extension}
ExecReload={remote_bin_path} -c {remote_config_dir}/%i{config_extension}
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

  local_port = generate_local_port(host, __file__)
  local_cert_path = local_config_dir / f'{host}{remote_port}.cer.pem'
  local_config_dir.mkdir(exist_ok=True, parents=True)
  with open(local_cert_path, 'w') as f:
    f.write(cer)

  with open(local_config_dir / f'{host}{remote_port}{config_extension}', 'w') as f:
    # mind yaml indentation
    f.write(f''' 
{{
    "relay": {{
        "server": "{target_masq_domain}:{remote_port}",
        "uuid": "{u1}",
        "password": "{password}",
        "ip": "{ip}",
        "certificates": ["{local_cert_path}"],
        "udp_relay_mode": "native",
        "congestion_control": "bbr",
    "alpn": ["h3", "spdy/3.1"],
        "zero_rtt_handshake": false,
        "disable_sni": false,
        "timeout": "8s",
        "heartbeat": "3s",
        "disable_native_certs": false,
        "gc_interval": "3s",
        "gc_lifetime": "15s"
    }},
    "local": {{
        "server": "127.0.0.1:{local_port}",
        "max_packet_size": 1500
    }},
    "log_level": "debug"
}}
'''.lstrip())
  local_service_name = 'tuicc'
  local_service_path = f'/etc/systemd/system/{local_service_name}@.service'
  local_bin_path = '/usr/bin/tuicc'
  local_service_content = f'''
[Unit]
Description=tuic 0.8.x client
After=network-online.target

[Service]
Type=simple
User={local_user}
Restart=on-failure
RestartSec=5s
ExecStart={local_bin_path} -c {local_config_dir}/%i{config_extension}
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
  remote_systemd_service_name = f'{remote_port}'

  local_systemd_service_name = f'{host}{remote_port}'

  common_permission_job(conn, remote_bin_path, remote_config_dir, local_bin_path, local_config_dir, remote_service_name, remote_systemd_service_name, local_service_name, local_systemd_service_name)

  conn.run(f'systemctl enable --now {remote_systemd_service_name}.service')
  os.system(f'systemctl enable --now {local_systemd_service_name}.service')

  ftp.close()
  if should_close_client:
    client.close()