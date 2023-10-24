# service name to port mapping
name_to_port_dict = {
    'ssh@server1': 40001,
    'ssh@server2': 40002,
}

init_selected_name = list(name_to_port_dict.keys())[0]
assert init_selected_name in name_to_port_dict.keys(), f'{init_selected_name} not in {name_to_port_dict.keys()}'

timeout_sec = 5

init_forwarded_to_port_num = 50000
assert isinstance(init_forwarded_to_port_num, int)

# connectivity_test_url = 'https://www.oracle.com/'
connectivity_test_url = 'https://1.1.1.1/'
