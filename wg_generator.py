#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

from functools import cached_property
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Interface

from wireguard_tools.wireguard_config import WireguardConfig, WireguardPeer
from wireguard_tools.wireguard_key import WireguardKey


class WGServer:
    def __init__(self, domain: str, listen_port: int, address: str):
        key = WireguardKey.generate()
        internal_interface = IPv4Interface(address)
        self.domain = domain
        self.config = WireguardConfig(
            private_key=key, listen_port=listen_port, addresses=[internal_interface]
        )
        self.public_key = key.public_key()
        self.subnets: list[IPv4Interface | IPv6Interface] = [internal_interface]

    def add_subnet(self, subnet: IPv4Network) -> None:
        self.subnets.append(IPv4Interface(subnet))

    @cached_property
    def peer(self) -> WireguardPeer:
        return WireguardPeer(
            self.public_key,
            endpoint_host=self.domain,
            endpoint_port=self.config.listen_port,
            persistent_keepalive=5,
            allowed_ips=self.subnets,
        )


class WGClient:
    def __init__(self, server: WGServer, name: str, address: IPv4Address):
        key = WireguardKey.generate()
        interface = IPv4Interface(address)
        self.name = name
        self.config = WireguardConfig(private_key=key, addresses=[interface])
        self.config.add_peer(server.peer)
        server.config.add_peer(
            WireguardPeer(public_key=key.public_key(), allowed_ips=[interface])
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Wireguard configuration files"
    )

    parser.add_argument(
        "--server",
        type=str,
        metavar="example.com",
        help="Server public address",
        required=True,
    )
    parser.add_argument(
        "--server-port",
        type=int,
        metavar="N",
        default=51820,
        help="Wireguard listen port (default 51820)",
    )
    parser.add_argument(
        "--subnet",
        type=str,
        metavar="0.0.0.0/0",
        default="10.0.0.0/8",
        help="VPN subnet. (Defaults to 10.0.0.0/8)",
    )
    parser.add_argument(
        "--router-ip",
        type=str,
        metavar="0.0.0.0",
        default="10.255.255.254",
        help="Router ip address. (Defaults to 10.255.255.254)",
    )
    parser.add_argument(
        "--count",
        type=int,
        metavar="N",
        default="50",
        help="Profile count. (Defaults to 50)",
    )
    parser.add_argument(
        "--output-dir", type=str, help="A path to dump configs to", required=True
    )
    parser.add_argument(
        "--extra-routes",
        type=str,
        nargs="*",
        help="List of extra routes to route through vpn.",
        metavar="10.0.0.0/24 192.168.0.0/16",
    )

    args = parser.parse_args()
    client_network = IPv4Network(args.subnet)
    client_count = args.count

    server = WGServer(args.server, args.server_port, args.router_ip)
    server.add_subnet(client_network)

    if args.extra_routes is not None:
        for route in args.extra_routes:
            server.add_subnet(IPv4Network(route))

    clients = [
        WGClient(server, f"client{i}", client_network[i])
        for i in range(1, client_count + 1)
    ]

    out_dir = Path(args.output_dir)
    if not out_dir.exists():
        Path.mkdir(out_dir)
    if not out_dir.is_dir():
        print(f"Error! {out_dir} is not a directory")
        sys.exit(1)

    if next(out_dir.iterdir(), None):
        print(f"Error! {out_dir} is not empty")
        sys.exit(1)

    server_config_path = out_dir / "server.conf"
    with server_config_path.open("w") as f:
        f.write(server.config.to_wgconfig(wgquick_format=True))

    clients_path = out_dir / "client"
    clients_path.mkdir()
    for client in clients:
        client_path = clients_path / f"{client.name}.conf"
        with client_path.open("w") as conf:
            conf.write(client.config.to_wgconfig(wgquick_format=True))
