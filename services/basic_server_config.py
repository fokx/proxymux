import paramiko
from fabric import Connection

def create_user_caddy(host):
    cmd = '''
    groupadd --system caddy
    useradd --system \
      --gid caddy \
      --create-home \
      --home-dir /var/lib/caddy \
      --shell /usr/sbin/nologin \
      --comment "Caddy web server" \
      caddy
    '''
    if isinstance(host, str):
        result = Connection(host).run(cmd, hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        print(msg.format(result))
    else:
        assert isinstance(host, paramiko.SSHClient)
        stdin, stdout, stderr = host.exec_command(cmd)
        for line in stdout.readlines():
            print(line)

def enable_bbr(host):
    pass
# if __name__ == '__main__':
#     create_caddy('e')