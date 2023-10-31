import logging
import os
import random
from pathlib import Path
import secrets

import fabric
import paramiko
from validators import uuid

from services.common import masquerade_domain_pool, XR_P2, XR_P1, LEN_PASSWD_MIN, LEN_PASSWD_MAX, remote_user, \
  local_user, common_permission_job
from services.get_ssh_client import new_ssh_client
from services.rcgen import gen_key_cer, gen_xr_private_public_key_strs, gen_short_ids
from services.local_port_num_generator import generate_local_port
local_config_dir = Path('/etc/xr')
remote_config_dir = Path('/etc/xr')

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
    remote_port = random.randrange(XR_P1, XR_P2)

  assert isinstance(remote_port, int)
  if password is None:
    password_length = random.randrange(LEN_PASSWD_MIN, LEN_PASSWD_MAX)
    password = secrets.token_urlsafe(password_length)
  assert isinstance(password, str)

  target_masq_domain = random.choice(masquerade_domain_pool)
  target_masq_url = f'https://{target_masq_domain}/'
  conn.run(f'mkdir -p {remote_config_dir}')

  private, public = gen_xr_private_public_key_strs()

  u1 = uuid.uuid4()
  tmp = (len(u1))
  config_extension = '.json'
  remote_config_path = remote_config_dir / f'{remote_port}{config_extension}'
  short_ids = gen_short_ids(4)
  shor_ids = str(short_ids)
  remote_config_content = f'''
{{
"log": {{
        "loglevel": "warning"
    }},
    "routing": {{
        "domainStrategy": "IPIfNonMatch",
        "rules": [
            {{
                "type": "field",
                "ip": [
                    "geoip:cn",
                    "geoip:private"
                ],
                "outboundTag": "block"
            }}
        ]
    }},
    "inbounds": [  
        {{
            "listen": "0.0.0.0",
            "port": {remote_port},
            "protocol": "vless",
            "settings": {{
                "clients": [
                    {{
                        "id": "{u1}",  
                        "flow": "xtls-rprx-vision"  
                    }}
                ],
                "decryption": "none"
            }},
            "streamSettings": {{
                "network": "tcp",
                "security": "reality",
                "realitySettings": {{
                    "show": true,  
                    "dest": "{target_masq_domain}:443",  
                    "xver": 0,  
                    "serverNames": [  
                        "{target_masq_domain}"
                    ],
                    "privateKey": "{private}",  
                    "minClientVer": "",  
                    "maxClientVer": "",  
                    "maxTimeDiff": 0,  
                    "shortIds": {shor_ids}
                }}
            }}
        }}
    ],
    "outbounds": [
        {{
            "protocol": "freedom",
            "tag": "direct",
            "settings": {{
                    "domainStrategy": "ForceIPv4v6"
            }}
        }},
        {{
            "protocol": "blackhole",
            "tag": "block"
        }}
    ],
    "policy": {{
        "levels": {{
            "0": {{
                "handshake": 2,  
                "connIdle": 120  
            }}
        }}
    }}
  
}}
'''.lstrip()
  file = ftp.file(str(remote_config_path), "w")
  file.write(remote_config_content)
  file.flush()

  remote_bin_path = '/usr/bin/xr'
  ftp.put('/usr/bin/xray', remote_bin_path)
  local_service_name = remote_service_name = 'xr'

  remote_service_path = f'/etc/systemd/system/{remote_service_name}@.service'
  remote_service_content = f'''
[Unit]
Description=Xray Service
After=network.target nss-lookup.target

[Service]
User={remote_user}
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
NoNewPrivileges=true
ExecStart={remote_bin_path} run -config {remote_config_dir}/%i{config_extension}
Restart=on-abort

[Install]
WantedBy=multi-user.target

'''.lstrip()
  file = ftp.file(remote_service_path, "w")
  file.write(remote_service_content)
  file.flush()

  local_config_dir.mkdir(exist_ok=True, parents=True)
  local_port = generate_local_port(host, __file__)
  # mind also local_port+1000 for HTTP listen

  with open(local_config_dir / f'{host}{remote_port}{config_extension}', 'w') as f:
    # mind yaml indentation
    f.write(f'''
{{
"log": {{
        "loglevel": "warning"
    }},
"routing": {{
        "domainStrategy": "IPIfNonMatch",
        "rules": [
            {{
                "type": "field",
                "domain": [
                    "geosite:category-ads-all"
                ],
                "outboundTag": "block"
            }},
            {{
                "type": "field",
                "domain": [
                    "geosite:geolocation-!cn"
                ],
                "outboundTag": "proxy"
            }},
            {{
                "type": "field",
                "domain": [
                    "geosite:cn",
                    "geosite:private"
                ],
                "outboundTag": "direct"
            }},
            {{
                "type": "field",
                "ip": [
                    "geoip:cn",
                    "geoip:private"
                ],
                "outboundTag": "direct"
            }}
        ]
    }},
    "inbounds": [
        {{
            "listen": "127.0.0.1",  
            "port": {local_port},
            "protocol": "socks"
        }},
        {{
            "listen": "127.0.0.1",  
            "port": {local_port+1000},
            "protocol": "http"
        }}
    ],
    
    "outbounds": [  
        {{
            "protocol": "vless",
            "settings": {{
                "vnext": [
                    {{
                        "address": "{ip}",  
                        "port": 8443,
                        "users": [
                            {{
                                "id": "{u1}",  
                                "flow": "xtls-rprx-vision",  
                                "encryption": "none"
                            }}
                        ]
                    }}
                ]
            }},
            "streamSettings": {{
                "network": "tcp",
                "security": "reality",
                "realitySettings": {{
                    "show": true,  
                    "fingerprint": "chrome",  
                    "serverName": "{target_masq_domain}",  
                    "publicKey": "{public}",  
                    "shortId": "{short_ids[0]}",  
                    "spiderX": ""  
                }}
            }}
        }},
           {{
            "protocol": "freedom",
            "tag": "direct"
        }},
        {{
            "protocol": "blackhole",
            "tag": "block"
        }}
    ]
}}
  '''.lstrip())
  local_service_path = f'/etc/systemd/system/{local_service_name}@.service'
  local_bin_path = '/usr/bin/xr'
  local_service_content = f'''
[Unit]
Description=Xray Service
After=network.target nss-lookup.target

[Service]
User={local_user}
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
NoNewPrivileges=true
ExecStart=={local_bin_path} run -config {local_config_dir}/%i{config_extension}
Restart=on-abort

[Install]
WantedBy=multi-user.target
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