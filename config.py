# service name to port mapping
name_to_port_dict = {



    # hy: 3
    'hy@sf1': 5305,
    'hy@sf2': 5306,
    'hy@lav': 5307,
    'hy@hil': 5308,


    # np: 4 
    'np@n': 5407,
    'np@nn': 5408,
    
    'sshsfC': 10001,

    'ssh@v': 5110,
    'ssh@vv': 5120,
    'ssh@e': 5130,
    'ssh@ee': 5140,
    'ssh@s': 5150,  # 7T
    'ssh@i': 5160,  # 2T
   
    #'auto': 0,
    # 'geph public 9909': 9909,
}

# default_choice = 'xr@nreal'
init_selected_name = list(name_to_port_dict.keys())[0]
assert init_selected_name in name_to_port_dict.keys(), f'{init_selected_name} not in {name_to_port_dict.keys()}'

timeout_sec = 5

init_forwarded_to_port_num = 3999
assert isinstance(init_forwarded_to_port_num, int)

# connectivity_test_url = 'https://www.oracle.com/'
connectivity_test_url = 'https://1.1.1.1/'



if __name__ == '__main__':
    print(' '.join(name_to_port_dict.keys()))
