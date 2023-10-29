# from https://gist.github.com/SteveHere/f702ed857a529c87a5914725c6e52e64
from asyncio import StreamReader, StreamWriter, StreamReaderProtocol, get_event_loop, ensure_future, start_server
from datetime import datetime

import socks  # use pysocks
from aiologger import Logger

logger = Logger.with_default_handlers(name=__name__, level=20)  # level=INFO
socks_address, socks_port, socks_username, socks_password = '127.2.0.0', 9050, None, None
proxy_address, proxy_port = '127.1.0.0', 9051


async def dial(client_read, client_write, server_read, server_write):
    async def io_copy(reader: StreamReader, writer: StreamWriter):
        try:
            while True:
                data = await reader.read(8192)
                if not data:
                    break
                writer.write(data)
            writer.close()
        except (OSError, ConnectionResetError) as e:
            await logger.error(f"{datetime.now().time()} - {e}")

    ensure_future(io_copy(client_read, server_write))
    ensure_future(io_copy(server_read, client_write))


async def open_socks5(host: str, port: int, limit=2 ** 16, aio_loop=None):
    s = None
    while s is None:
        try:
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, socks_address, socks_port, username=socks_username, password=socks_password)
            s.connect((host, port))
        except (socks.GeneralProxyError, OSError):
            await logger.error(f"{datetime.now().time()} - Encountered connection error - Retrying");
            s = None
    if not aio_loop:
        aio_loop = get_event_loop()
    reader = StreamReader(limit=limit, loop=aio_loop)
    protocol = StreamReaderProtocol(reader, loop=aio_loop)
    transport, _ = await aio_loop.create_connection(lambda: protocol, sock=s)
    return reader, StreamWriter(transport, protocol, reader, aio_loop)


def get_connection_properties(headers: list) -> (str, int, bool):
    method, url, version = headers[0].decode().split(' ', 2)
    if is_connect := (method.upper() == 'CONNECT'):
        host, port = url.split(':', 1)
    else:
        host_text = [hl[5:].lstrip() for header in headers[1:] if (hl := header.decode())[:5].lower() == 'host:']
        if not host_text:  # If empty
            raise ValueError("No http host line")
        host, port = (host_text, "80") if ':' not in (host_text := host_text[0].strip("\r\n")) else host_text.split(':',
                                                                                                                    1)
    return host, int(port), is_connect


async def handle_connection(client_read: StreamReader, client_write: StreamWriter):
    try:
        http_header_list = []
        while (line := await client_read.readline()) != b'\r\n':
            http_header_list.append(line)
        http_header_list.append(line)
        host, port, is_connect = get_connection_properties(http_header_list)
    except (IOError, ValueError) as e:
        await logger.error(f"{datetime.now().time()} - {e}");
        client_write.close();
        return

    server_read, server_write = await open_socks5(host=host, port=port)
    if is_connect:
        client_write.write(b'HTTP/1.0 200 Connection Established\r\n\r\n')
    else:
        server_write.write(b''.join(http_header_list))
    ensure_future(dial(client_read, client_write, server_read, server_write))


if __name__ == '__main__':
    loop, server = get_event_loop(), start_server(handle_connection, host=proxy_address, port=proxy_port)
    try:
        server = loop.run_until_complete(server)
        print("Socks proxy open: ", proxy_address, proxy_port)
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
