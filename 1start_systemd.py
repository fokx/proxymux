#!/bin/python
import os
from collections import defaultdict
from pathlib import Path

from config import name_to_port_dict

# start proxy service
for k in name_to_port_dict.keys():
    if '@' in k and 'ssh' not in k:
        # os.system(f'systemctl start {k}')
        os.system(f'systemctl enable {k}')
print()

# start ssh tunnel
fname = '/i/bin/sshall'
with open(fname, 'w') as f:  # /i/bin/sshall is executed by liu since we need to read config in liu/.ssh
    f.write(f'#!/bin/zsh\n')

    for k, v in name_to_port_dict.items():
        if 'ssh@' in k:
            name = k.split('@')[1]
            f.write(
                f'autossh -M 0 -o "ServerAliveInterval 45" -o "ServerAliveCountMax 2" -D {v} -q -C -N -f {name} -v\n')
os.system(f'chmod 755 {fname}')
print()

# start graftcp @ port
for k, v in name_to_port_dict.items():
    if k != 'auto':
        os.system(f'systemctl start gl@{v}')
        os.system(f'systemctl enable gl@{v}')
print()

proxychains_template = '''
strict_chain
{proxy_dns}
remote_dns_subnet 224
tcp_read_time_out 15000
tcp_connect_time_out 8000
localnet 127.0.0.0/255.0.0.0
localnet ::1/128
[ProxyList]
socks5  127.0.0.1 {proxy_port}
'''
proxychains_chain_template = '''
round_robin_chain
{proxy_dns}
remote_dns_subnet 224
tcp_read_time_out 15000
tcp_connect_time_out 8000
localnet 127.0.0.0/255.0.0.0
localnet ::1/128
[ProxyList]
socks5  127.0.0.1 {proxy_port}
'''
pcdir = Path('/etc/pc/')

if not pcdir.is_dir():
    pcdir.mkdir()


def write_both(name, port):
    def write_one(content, name):
        with open(f'/etc/pc/{name}.conf', 'w') as f:
            f.write(content)

    if isinstance(port, list):  # chain
        assert len(port) > 0
        write_one(proxychains_chain_template.format(proxy_dns='proxy_dns', proxy_port=port[0]) + '\n'.join(
            [f'socks5  127.0.0.1 {i}' for i in port[1:]]) + '\n',
                  f'{name}S')  # suffix `S` means proxy dns, inspired by http(s)
        write_one(proxychains_chain_template.format(proxy_dns='', proxy_port=port[0]) + '\n'.join(
            [f'socks5  127.0.0.1 {i}' for i in port[1:]]) + '\n', f'{name}')
    else:
        write_one(proxychains_template.format(proxy_dns='proxy_dns', proxy_port=port),
                  f'{name}S')  # suffix `S` means proxy dns, inspired by http(s)
        write_one(proxychains_template.format(proxy_dns='', proxy_port=port), f'{name}')


server_ipvX_concat = {}
ssh_ports = []
proxy_ports = []
for k, v in name_to_port_dict.items():
    if k != 'auto':

        write_both(v, v)
        if 'ssh@' in k:
            i = k.split('@')[1]
            write_both(i, v)
            ssh_ports.append(v)
        elif '@' in k:
            write_both(k.replace('@', ''), v)
            server_id = k.split('@')[1]
            proxy_ports.append(v)
            if server_ipvX_concat.get(server_id):
                server_ipvX_concat[server_id].append(v)
            else:
                server_ipvX_concat[server_id] = [v]
        else:  # ignore name without @
            pass
for k, v in server_ipvX_concat.items():
    write_both(k, v)
server_concat = defaultdict(list)
for k, v in server_ipvX_concat.items():
    server_concat[k.lower()] += v
for k, v in server_concat.items():
    write_both(k + 'A', v)  # 'A' means ipv4+v6 all

write_both('1', proxy_ports)
write_both('0', ssh_ports)

os.system(f'chmod 644 /etc/pc/*')
os.system(f'chmod 755 /etc/pc/')
os.system(f'chown -R root:root /etc/pc/')

zsh_alias_write_path = '/etc/zsh/pc'
with open(zsh_alias_write_path, 'w') as zsh_alias_write_f:
    for name in pcdir.glob('*'):
        name = name.name.split('.')[0]
        zsh_alias_write_f.write(f'alias pc{name}="proxychains -f /etc/pc/{name}.conf "\n')
        zsh_alias_write_f.write(
            f'alias wg{name}="proxychains -f /etc/pc/{name}.conf wget -c --header=\'Accept: text/html\' --user-agent=\'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36\'" \n')
        zsh_alias_write_f.write(
            f'alias yp{name}="noglob proxychains -f /etc/pc/{name}.conf yt-dlp --write-auto-sub "\n')
        zsh_alias_write_f.write(
            f'alias ag{name}="proxychains -f /etc/pc/{name}.conf aria2c --conf-path ~/.aria2/mag.conf "\n')

os.system(f'chmod 644 /etc/zsh/*')
os.system(f'chmod 755 /etc/zsh/')
os.system(f'chown -R root:root /etc/zsh/')
