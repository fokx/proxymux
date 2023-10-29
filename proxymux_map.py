#!/usr/bin/env python
# adapted from:
# TCP Port Forwarding (Reverse Proxy)
# Author : WangYihang <wangyihanger@gmail.com>
# Requires Python 3.6 or above.

# use Cython to speed up?
# cython: language_level=3
# cython port_forward.py --embed && gcc -Os -I /usr/include/python3.9/ -o port_forward port_forward.c -lpython3.9 -lpthread -lm -lutil -ldl
import gc
import itertools
import logging
import argparse


import socket
import threading


def handle(buffer):
    return buffer


def transfer(src, dst, direction):
    src_name = src.getsockname()
    src_address = src_name[0]
    src_port = src_name[1]
    dst_name = dst.getsockname()
    dst_address = dst_name[0]
    dst_port = dst_name[1]
    while True:
        try:
            buffer = src.recv(1024)
        except KeyboardInterrupt:
            break
        if len(buffer) == 0:
            logging.info("[-] No data received! Breaking...")
            break
        # if direction:
        #    logging.info(f"[+] {src_address}:{src_port} >>> {dst_address}:{dst_port} [{len(buffer)}]")
        # else:
        #    logging.info(f"[+] {dst_address}:{dst_port} <<< {src_address}:{src_port} [{len(buffer)}]")
        try:
            dst.send(handle(buffer))
        except Exception as e:
            logging.info(e)
    try:
        logging.info(f"[+] Closing connections! [{src_address}:{src_port}]")
        src.shutdown(socket.SHUT_RDWR)
        src.close()
        logging.info(f"[+] Closing connections! [{dst_address}:{dst_port}]")
        dst.shutdown(socket.SHUT_RDWR)
        dst.close()
    except Exception as e:
        logging.info(e)


def server(local_host, local_port, remote_host, max_connection, remote_port, round_robin_ports=[]):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((local_host, local_port))
    server_socket.listen(max_connection)
    logging.info(f"[+] Server started [{local_host}:{local_port}]")
    # logging.info(f"[+] Connected to [{local_host}:{local_port}] to get the content of [{remote_host}:{remote_port}]")
    if len(round_robin_ports) != 0:
        use_round = True
        round_robin_ports = itertools.cycle(round_robin_ports)
    else:
        use_round = False
    # ports = itertools.cycle( [5110,  5160])
    # ports = itertools.cycle( [5110, 5120, 5130, 5150])
    # ports = [5107, 6107]
    while True:
        try:
            if use_round:
                # remote_port = random.choice(ports)
                remote_port = next(round_robin_ports)
                # print(remote_port,end=' ')
            local_socket, local_address = server_socket.accept()
            logging.info(f"[+] Detect connection from [{local_address[0]}:{local_address[1]}]")
            logging.info(f"[+] Connecting to the REMOTE server [{remote_host}:{remote_port}]")
            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.connect((remote_host, remote_port))
            logging.info("[+] Tunnel connected! Transferring data...")
            # threads = []
            s = threading.Thread(target=transfer, args=(
                remote_socket, local_socket, False))
            r = threading.Thread(target=transfer, args=(
                local_socket, remote_socket, True))
            # threads.append(s)
            # threads.append(r)
            s.start()
            r.start()
        except KeyboardInterrupt:
            break
        except Exception as e:
            logging.info(e)
    logging.info("[+] Releasing resources...")
    remote_socket.shutdown(socket.SHUT_RDWR)
    remote_socket.close()
    local_socket.shutdown(socket.SHUT_RDWR)
    local_socket.close()
    logging.info("[+] Closing the server...")
    server_socket.shutdown(socket.SHUT_RDWR)
    server_socket.close()
    logging.info("[+] Shutting down the server!")


def redirect_remote_to_local(forward_to, forward_from=None):
    try:
        LOCAL_HOST = '127.0.0.1'
        # LOCAL_HOST = '0.0.0.0'
        REMOTE_HOST = '127.0.0.1'
        MAX_CONNECTION = 0x10
        server(LOCAL_HOST, forward_to, REMOTE_HOST, MAX_CONNECTION, forward_from, round_robin_ports=[])
        # server(LOCAL_HOST, local_port, REMOTE_HOST, MAX_CONNECTION, remote_port, round_robin_ports=[5110, 5120, 5130, 5150, 5115, 5125, 5135])
    except Exception as e:
        logging.error(e)
    finally:
        gc.collect()


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    parser = argparse.ArgumentParser()
    parser.add_argument("src_port_number", type=int, help="source port number")
    parser.add_argument("dst_port_number", type=int, help="destination port number")
    args = parser.parse_args()
    redirect_remote_to_local(forward_to=args.dst_port_number, forward_from=args.src_port_number)
