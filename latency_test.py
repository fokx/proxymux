import importlib
import logging
import multiprocessing
import os
import random
import socket
from time import sleep

import requests

import proxymux_map # proxymux_map = importlib.import_module("proxymux-map")

from config import name_to_port_dict, timeout_sec, connectivity_test_url

all_proxys_name_to_port = name_to_port_dict.copy()
for k in name_to_port_dict.keys():
    if 'ssh@' in k:
        all_proxys_name_to_port.pop(k)
    if '@' not in k:
        all_proxys_name_to_port.pop(k)


def auto_redir():
    process_list = []
    port = 0
    while True:
        if len(process_list) == 0:
            if port == 0:
                port = random.choice(list(all_proxys_name_to_port.values()))
                logging.warning(f'auto_redir initially use {port}')
            p = multiprocessing.Process(target=proxymux_map.redirect_remote_to_local, args=(3999, port))
            process_list.append(p)
            p.start()
        else:
            sleep(5)
            if not is_available(3999):
                good_port = latency_test()
                # if good_port != port:
                port = good_port
                logging.warning(f'previous not available, change to {port}')
                p = process_list.pop()
                p.terminate()
            else:
                print('.', end='')


def is_available(port):
    session = requests.Session()
    socks5 = f'socks5://127.0.0.1:{port}'
    try:
        session.get(connectivity_test_url, proxies={'http': socks5, 'https': socks5}, timeout=timeout_sec)
    except:
        return False
    return True


def latency_test():
    session = requests.Session()
    times = []
    TIMEOUT_BIG_NUM = 9999

    for name, port in all_proxys_name_to_port.items():
        socks5 = f'socks5://127.0.0.1:{port}'
        try:
            got = session.get(connectivity_test_url, proxies={'http': socks5, 'https': socks5}, timeout=timeout_sec)
            times.append(got.elapsed.total_seconds())
        except:
            logging.info(f'Proxy via port {port} unreachable')
            # os.system(f'systemctl restart {name}')
            times.append(TIMEOUT_BIG_NUM)
    results = [(i, j) for i, j in zip(all_proxys_name_to_port, times)]
    results = sorted(results, key=lambda tup: tup[1])
    print(results)
    good_name = results[0][0]
    proxys_to_restart = []
    for i, j in results:
        if int(j) == TIMEOUT_BIG_NUM:
            proxys_to_restart.append(i)
    if len(proxys_to_restart) > 0:
        print(f'systemctl restart {" ".join(proxys_to_restart)}')
        os.system(f'systemctl restart {" ".join(proxys_to_restart)}')
        if all([i[1] == TIMEOUT_BIG_NUM for i in results]):
            logging.error('All proxies are unreachable')
            os.system('systemctl restart tuicc@j tuicc@n np@nn np@j  xr@nreal')
            sleep(4)
            return latency_test()

    return all_proxys_name_to_port[good_name]


if __name__ == '__main__':
    socket.setdefaulttimeout(5)
    auto_redir()
