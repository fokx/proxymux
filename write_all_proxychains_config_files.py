for i in range(1, 65536):
    with open(f'/etc/pc/{i}.conf', 'w') as f:
        f.write(f'''strict_chain
proxy_dns
remote_dns_subnet 224
tcp_read_time_out 15000
tcp_connect_time_out 8000
localnet 127.0.0.0/255.0.0.0
localnet ::1/128
[ProxyList]
socks5  127.0.0.1 {i}
''')


# round-robin for link aggregation
'''
round_robin_chain
remote_dns_subnet 224
tcp_read_time_out 15000
tcp_connect_time_out 8000
localnet 127.0.0.0/255.0.0.0
localnet ::1/128
[ProxyList]
socks5  127.0.0.1 5110
socks5  127.0.0.1 5120
socks5  127.0.0.1 5130
socks5  127.0.0.1 5140
socks5  127.0.0.1 5150
'''