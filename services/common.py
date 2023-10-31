import os

masquerade_domain_pool = '''
www.oracle.com
yandex.ru
live.com
docomo.ne.jp
office.com
microsoftonline.com
bing.com
zoom.us
fandom.com
stackoverflow.com
nginx.org
nginx.org
www.cloudflare.com

'''.strip().splitlines()

# potentially occupied ports:
# ANY_P1 - ANY_P2
# HY_P3 - HY_P5

HY_P1 = 360
HY_P2 = 442
HY_P3 = 444
HY_P4 = 514
HY_P5 = 650

TUIC_P1 = HY_P5 + 1
TUIC_P2 = 733

NAIVE_P1 = TUIC_P2  + 1
NAIVE_P2 = 811

XR_P1 = NAIVE_P2 + 1
XR_P2 = 900


LEN_PASSWD_MIN = 18
LEN_PASSWD_MAX = 22


remote_user = 'caddy'
local_user = 'tr'


def common_permission_job(conn, remote_bin_path, remote_config_dir, local_bin_path, local_config_dir, remote_service_name, remote_systemd_service_name, local_service_name, local_systemd_service_name):
    conn.run(f'chown -R root:root {remote_bin_path}')
    conn.run(f'chmod 755 {remote_bin_path}')
    conn.run(f'chown -R {remote_user}:{remote_user} {remote_config_dir}')
    conn.run(f'chmod 700 {remote_config_dir}')
    conn.run(f'setcap cap_net_bind_service=+ep {remote_bin_path}')

    os.system(f'chown -R root:root {local_bin_path}')
    os.system(f'chmod 755 {local_bin_path}')
    os.system(f'chown -R liu:{local_user} {local_config_dir}')
    os.system(f'chmod 770 {local_config_dir}')
    os.system(f'setcap cap_net_bind_service=+ep {local_bin_path}')

    conn.run(f'systemctl enable --now {remote_service_name}@{remote_systemd_service_name}.service')
    os.system(f'systemctl enable --now {local_service_name}@{local_systemd_service_name}.service')