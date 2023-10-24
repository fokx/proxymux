# <div align=center><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/Multiplexer_4-to-1.svg/240px-Multiplexer_4-to-1.svg.png" width="40"> Proxy MUX</div>


`proxymux`: a **[multiplexer](https://en.wikipedia.org/wiki/Multiplexer)** / switch, that **select** between multiple SOCKS5 proxies listening at **different** ports and **forward** it to one **fixed** port.

It is useful when you have multiple SOCKS5 proxy provided by different tools (e.g. multiple `ssh -TND <port_number> user@host`),
and want to **fix** the port number for other application (e.g. `firefox`, `proxychains`) using SOCKS5 proxies, you can use `proxymux`. 

It works like the popular browser extension [SwitchyOmega](https://github.com/FelisCatus/SwitchyOmega), but at system level. 

## Basic Features

* simple terminal user interface (TUI) available, using [urwid](https://urwid.org/index.html)
    ```sh
    python proxymux.py
    ```
* solitary port to port forward
    ```sh
    python proxymux-map.py <src_port_number> <dst_port_number>
    ```

## Advanced Features
(under developemnt)
* health check and failover
* perform *speed / latency* test regularly to auto switch to the best route
* support multi-path **aggregation** for increased throughput and fault tolerance, using round-robin / random switch policy
* convert SOCKS5 to **HTTP(S)** proxy


