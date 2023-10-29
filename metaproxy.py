#!/usr/bin/env python
'''

510x
9: h(monovm)
8: l(monovm)
7: n(ny buyvm)

ensure /etc/hosts have records for all

ls -l|grep -v _|awk '{print $9}'| rev | cut -c6- | rev|sed '1d;s/.*/sudo systemctl $1 tr@&/' > _ctl
ls -l|grep -v _|awk '{print $9}'| rev | cut -c6- | rev|sed '1d;s/.*/alias pc&="proxychains -f \/etc\/pc\/&.conf"/' > /opt/liu/assets/zsh-proxyalias
echo '' >> /opt/liu/assets/zsh-proxyalias
ls -l|grep -v _|awk '{print $9}'| rev | cut -c6- | rev|sed '1d;s/.*/alias ag&="proxychains -f \/etc\/pc\/&.conf aria2c --conf-path ~\/.aria2\/mag.conf "/' >> /opt/liu/assets/zsh-proxyalias



echo 'Executing' $1:
cat ./_ctl
sh ./_ctl $1
rm ./_ctl

echo ''
echo 'Appending to /opt/liu/assets/zsh-proxyalias:'
cat

'''
import glob
import os.path
from pathlib import Path

use_gui_3999_selector = True
template_common = '''
password:
    - {password}
ssl:
    sni: {sni}
tcp:
    prefer-ipv4: false
    no-delay: true
    keep-alive: true
mux:
    enabled: false
router:
    enabled: {router_enabled}
    bypass: ['geoip:cn', 'geoip:private', 'geosite:cn', 'geosite:private']
    block: ['geosite:category-ads']
    proxy: ['geosite:geolocation-!cn']
    default-policy: proxy
    geoip: /usr/share/trojan-go/geoip.dat
    geosite: /usr/share/trojan-go/geosite.dat
'''
template_head_client = '''
run-type: client
local-addr: 127.0.0.1
local-port: {local_port}
remote-addr: {remote_addr}
remote-port: {remote_port}
'''
template_head_forward = '''
run-type: forward
local-addr: 127.0.0.1
local-port: {local_port}
remote-addr: {remote_addr}
remote-port: {remote_port}
target-addr: {target_addr}
target-port: 443
'''

port_prefix = 51
# l and n uses load balance
passwords = dict()
for k in 'n nx t tx'.split():
    passwords[k] = '1u983rhueiwfdsvnjAOIJEGHRUDBSFHV128932hqe(@!*HQwu9j0iods'

passwords['h'] = 'j3q28ew4hruigfdnjioeqwi930q2ut48wheu(#U@)TEWH*IUGBDsjnqwases'
passwords['hx'] = passwords['h']
passwords['v'] = 'dasdgP(*@HJORQhasdui(2r3u89jFEAoishjahADKS1230'
passwords['x'] = passwords['v']

remotes = {
    'h': 9,
    'n': 7,
    't': 8,
}
relays = {
    'v': 1,
    'x': 3,
}
relays_hostname = {
    'x': 'xz.x87.org',  # xd: '10.184.17.19',
    'v': 'lv.x87.org',  # 202.117.43.254
}
relays_port = {
    'x': 17341,
    'v': 443,
}
relays_snis = {
    'x': 'x.x87.org',
    'v': 'lv.x87.org'
}
assert relays.keys().isdisjoint(remotes.keys())

for i in glob.glob('/etc/trg/*.yaml'):
    if 'as' in i:
        continue
    os.system(f'rm {i}')
# write /etc/trg/X.yaml
tr_variants = []
for remote in remotes.keys():
    # direct ipv4
    name = f'{remote}'
    port = f'{port_prefix}0{remotes[remote]}'
    tr_variants.append((name, port))
    with open(f'/etc/trg/{name}.yaml', 'w') as f:
        f.write(template_head_client.format(local_port=port,
                                            remote_addr=f'{remote}.x87.org',
                                            remote_port=443))
        f.write('\n')
        f.write(template_common.format(password=passwords[remote],
                                       sni=f'{remote}.x87.org',
                                       router_enabled='false'))
        f.write('\n')
    # direct ipv6
    name = f'{remote}x'
    port = f'{port_prefix}0{remotes[remote]}{remotes[remote]}'
    tr_variants.append((name, port))
    with open(f'/etc/trg/{name}.yaml', 'w') as f:
        f.write(template_head_client.format(local_port=port,
                                            remote_addr=f'{remote}x.x87.org',
                                            remote_port=443))
        f.write('\n')
        f.write(template_common.format(password=passwords[remote + "x"],
                                       sni=f'{remote}x.x87.org',
                                       router_enabled='false'))
        f.write('\n')
    for relay in ['x', 'v']:
        name = f'{relay}{remote}-forward'
        port = f'{port_prefix}{relays[relay] + 1}{remotes[remote]}'
        tr_variants.append((name, port))
        with open(f'/etc/trg/{name}.yaml', 'w') as f:
            if remote == 'n':
                f.write(template_head_forward.format(local_port=port,
                                                     remote_addr=relays_hostname[relay],
                                                     remote_port=relays_port[relay],
                                                     target_addr='n.x87.org'))
                f.write('\n')
                f.write(template_common.format(password=passwords[relay],
                                               sni=relays_snis[relay],
                                               router_enabled='false'))
                f.write('\n')

            else:
                f.write(template_head_forward.format(local_port=port,
                                                     remote_addr=relays_hostname[relay],
                                                     remote_port=relays_port[relay],
                                                     target_addr=f'{remote}.x87.org'))
                f.write('\n')
                f.write(template_common.format(password=passwords[relay],
                                               sni=relays_snis[relay],
                                               router_enabled='false'))
                f.write('\n')
        name = f'{relay}{remote}'
        port = f'{port_prefix}{relays[relay]}{remotes[remote]}'
        tr_variants.append((name, port))
        with open(f'/etc/trg/{name}.yaml', 'w') as f:

            f.write(template_head_client.format(local_port=port,
                                                remote_addr='127.0.0.1',
                                                remote_port=f'{port_prefix}{relays[relay] + 1}{remotes[remote]}'))
            f.write('\n')

            f.write(template_common.format(password=passwords[remote],
                                           sni=f'{remote}.x87.org',
                                           router_enabled='false'))
            f.write('\n')
# connect to relays directly
for relay in ['x', 'v']:
    name = f'{relay}'
    port = f'{port_prefix}{relays[relay]}0'
    tr_variants.append((name, port))
    with open(f'/etc/trg/{name}.yaml', 'w') as f:
        f.write(template_head_client.format(local_port=port,
                                            remote_addr=relays_hostname[relay],
                                            remote_port=relays_port[relay]))
        f.write('\n')
        f.write(template_common.format(password=passwords[relay],
                                       sni=relays_snis[relay],
                                       router_enabled='false'))
        f.write('\n')

# TODO symlink 3999, 3998, 3997
generic_num = 3999
generic_num_auto = 3998
# 3999 ipv6
with open(f'/etc/trg/_{generic_num}-nx.yaml', 'w') as f:
    f.write(template_head_client.format(local_port=generic_num,
                                        remote_addr='nx.x87.org',
                                        remote_port=443))
    f.write('\n')
    f.write(template_common.format(password=passwords['nx'],
                                   sni=f'nx.x87.org',
                                   router_enabled='false'))
    f.write('\n')
# 3999 ipv4
with open(f'/etc/trg/_{generic_num}-n.yaml', 'w') as f:
    f.write(template_head_client.format(local_port=generic_num,
                                        remote_addr='n.x87.org',
                                        remote_port=443))
    f.write('\n')
    f.write(template_common.format(password=passwords['n'],
                                   sni=f'n.x87.org',
                                   router_enabled='false'))
    f.write('\n')

# 3998 auto ipv6
with open(f'/etc/trg/_{generic_num_auto}-hx.yaml', 'w') as f:
    f.write(template_head_client.format(local_port=generic_num_auto,
                                        remote_addr='hx.x87.org',
                                        remote_port=443))
    f.write('\n')
    f.write(template_common.format(password=passwords['hx'],
                                   sni=f'hx.x87.org',
                                   router_enabled='true'))
    f.write('\n')
# actual default server:
os.system(f'ln -sf /etc/trg/_{generic_num}-nx.yaml /etc/trg/{generic_num}.yaml')
os.system(f'ln -sf /etc/trg/_{generic_num_auto}-hx.yaml /etc/trg/{generic_num_auto}.yaml')
if not use_gui_3999_selector:
    tr_variants.extend([(generic_num, generic_num), (generic_num_auto, generic_num_auto)])

print(f'port_mapping: {tr_variants}')
for i, j in tr_variants:
    print(f'    "{i}": {j},')

os.system('chown -R tr:tr /etc/trg/*')
os.system('chmod 600 /etc/trg/*')

for variant in tr_variants:
    print(f'systemctl stop trg@{variant[0]}')
    os.system(f'systemctl stop trg@{variant[0]}')
print()
for variant in tr_variants:
    print(f'systemctl disable trg@{variant[0]}')
    os.system(f'systemctl disable trg@{variant[0]}')
print()
for variant in tr_variants:
    print(f'systemctl status trg@{variant[0]}')
for variant in tr_variants:
    print(f'systemctl disable trg@{variant[0]}')
for v in 'h hx n nx t tx'.split():
    os.system(f'systemctl start trg@{v}')
    os.system(f'systemctl enable trg@{v}')
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
zsh_alias_write_path = '/opt/liu/assets/zsh-proxyalias'
pcdir = Path('/etc/pc/')
with open(zsh_alias_write_path, 'w') as zsh_alias_write_f:
    if not pcdir.is_dir():
        pcdir.mkdir()
    for variant in pcdir.glob('*'):
        # pc
        # suffix P means proxy DNS
        with open(f'/etc/pc/{name}P.conf', 'w') as f:
            f.write(proxychains_template.format(proxy_dns='proxy_dns',
                                                proxy_port=port))
        with open(f'/etc/pc/{name}.conf', 'w') as f:
            f.write(proxychains_template.format(proxy_dns='',
                                                proxy_port=port))
        # alias
        for suffix in ['', 'P']:
            name = name + suffix
            zsh_alias_write_f.write(f'alias pc{name}="proxychains -f /etc/pc/{name}.conf "\n')
            zsh_alias_write_f.write(
                f'alias wg{name}="proxychains -f /etc/pc/{name}.conf wget -c --header=\'Accept: text/html\' --user-agent=\'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36\'" \n')
            zsh_alias_write_f.write(f'alias yt{name}="noglob proxychains -f /etc/pc/{name}.conf yt-dlp "\n')
            zsh_alias_write_f.write(
                f'alias ag{name}="proxychains -f /etc/pc/{name}.conf aria2c --conf-path ~/.aria2/mag.conf "\n')
