from pathlib import Path

service_id = {v: i + 1
              for i, v in enumerate('''
naive
hysteria
tuic
xr

'''.strip().splitlines())
              }

host_id = {v: i + 1
           for i, v in enumerate('''
sf1
sf2
npc
npd
lax
npl
lav
hil

'''.strip().splitlines())
           }


def generate_local_port(host, service):
  service = Path(service).stem

  return f'5{service_id[service]}{host_id[host]:2d}'
