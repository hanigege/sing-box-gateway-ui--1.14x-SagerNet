#!/usr/bin/env python3
import ipaddress
import json
import os
import secrets
import subprocess
from pathlib import Path


CONFIG_DIR = Path("/etc/sing-box")
MANAGER_DIR = CONFIG_DIR / "manager"
RULE_DIR = CONFIG_DIR / "custom-rules"
CONFIG_PATH = CONFIG_DIR / "config.json"
BASE_CONFIG_PATH = MANAGER_DIR / "base.json"
NODES_PATH = MANAGER_DIR / "nodes.json"
GROUPS_PATH = MANAGER_DIR / "groups.json"
INITIAL_NODES_FILE = os.environ.get("SING_BOX_INITIAL_NODES_FILE", "")
DEFAULT_FAKE4 = "28.0.0.0/8"
DEFAULT_FAKE6 = "2001:2::/64"


def ask(prompt, default=""):
    suffix = f" [{default}]" if default else ""
    try:
        value = input(f"{prompt}{suffix}: ").strip()
    except EOFError:
        print()
        value = ""
    return value or default


def ask_int(prompt, default):
    while True:
        value = ask(prompt, str(default))
        try:
            number = int(value)
            if 1 <= number <= 65535:
                return number
        except ValueError:
            pass
        print("Please enter a valid port.")


def ask_yes_no(prompt, default=True):
    default_text = "yes" if default else "no"
    value = ask(prompt, default_text).lower()
    return value in {"y", "yes", "1", "true"}


def default_lan_ip():
    try:
        out = subprocess.check_output(["ip", "-o", "-4", "route", "get", "1.1.1.1"], text=True)
        parts = out.split()
        if "src" in parts:
            return parts[parts.index("src") + 1]
    except Exception:
        pass
    return "0.0.0.0"


def empty_rule_set():
    return {"version": 3, "rules": []}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def node_from_prompt(index, default_type):
    node_type = ask(f"Node {index} type: hysteria2 or vless", default_type)
    if node_type not in {"hysteria2", "vless"}:
        raise ValueError("Unsupported node type")
    tag = ask("Node tag", f"{node_type}-{index}")
    server = ask("Node server IP/domain")
    port = ask_int("Node port", 443)
    sni = ask("TLS server_name", server)
    insecure = ask("Allow insecure TLS? yes/no", "yes").lower() in {"y", "yes", "1", "true"}
    outbound = {
        "type": node_type,
        "tag": tag,
        "server": server,
        "server_port": port,
        "tls": {"enabled": True, "server_name": sni, "insecure": insecure},
    }
    if node_type == "hysteria2":
        outbound["password"] = ask("Hysteria2 password")
        obfs = ask("Obfs password, empty to disable", "")
        if obfs:
            outbound["obfs"] = {"type": "salamander", "password": obfs}
        up = ask("Up Mbps, empty to skip", "")
        down = ask("Down Mbps, empty to skip", "")
        if up:
            outbound["up_mbps"] = int(up)
        if down:
            outbound["down_mbps"] = int(down)
    else:
        outbound["uuid"] = ask("VLESS UUID")
        outbound["packet_encoding"] = "xudp"
        outbound["tcp_fast_open"] = True
        outbound["tls"]["utls"] = {"enabled": True, "fingerprint": "chrome"}
        public_key = ask("Reality public_key, empty to disable Reality", "")
        if public_key:
            outbound["tls"]["reality"] = {"enabled": True, "public_key": public_key}
            short_id = ask("Reality short_id, empty to skip", "")
            if short_id:
                outbound["tls"]["reality"]["short_id"] = short_id
    return {"enabled": True, "outbound": outbound}


def template_nodes():
    return [
        {
            "enabled": True,
            "outbound": {
                "type": "hysteria2",
                "tag": "TEMPLATE-HY2",
                "server": "198.51.100.10",
                "server_port": 443,
                "password": "change-me-hysteria2-password",
                "tls": {"enabled": True, "server_name": "example.com", "insecure": True},
                "obfs": {"type": "salamander", "password": "change-me-obfs-password"},
                "up_mbps": 20,
                "down_mbps": 100,
            },
        },
        {
            "enabled": True,
            "outbound": {
                "type": "vless",
                "tag": "TEMPLATE-VLESS",
                "server": "203.0.113.10",
                "server_port": 443,
                "uuid": "00000000-0000-4000-8000-000000000001",
                "packet_encoding": "xudp",
                "tcp_fast_open": True,
                "tls": {
                    "enabled": True,
                    "server_name": "example.com",
                    "insecure": True,
                    "utls": {"enabled": True, "fingerprint": "chrome"},
                },
            },
        },
    ]


def initial_nodes_from_file():
    if not INITIAL_NODES_FILE:
        return None
    path = Path(INITIAL_NODES_FILE)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("SING_BOX_INITIAL_NODES_FILE must contain a non-empty node list")
    for index, node in enumerate(data, 1):
        if not isinstance(node, dict) or not isinstance(node.get("outbound"), dict):
            raise ValueError(f"Node {index} is missing outbound")
        outbound = node["outbound"]
        if not outbound.get("tag") or outbound.get("type") not in {"hysteria2", "vless"}:
            raise ValueError(f"Node {index} must have a supported outbound type and tag")
        node.setdefault("enabled", True)
    return data


def local_rule_set(tag, path, format_="source"):
    return {"type": "local", "tag": tag, "format": format_, "path": path}


def base_config(lan_ip, ui_secret, fake4, fake6, ipv6_dns_listen):
    dns_inbounds = ["dns-in"]
    inbounds = [
        {"type": "tproxy", "tag": "tproxy-in", "listen": "::", "listen_port": 9888, "sniff": False},
        {"type": "direct", "tag": "dns-in", "listen": lan_ip, "listen_port": 53},
    ]
    if ipv6_dns_listen:
        dns_inbounds.append("dns-in-v6")
        inbounds.append({"type": "direct", "tag": "dns-in-v6", "listen": ipv6_dns_listen, "listen_port": 53})
    return {
        "log": {"level": "warning"},
        "dns": {
            "servers": [
                {
                    "tag": "remote-dns",
                    "type": "https",
                    "server": "1.1.1.1",
                    "server_port": 443,
                    "path": "/dns-query",
                    "tls": {"server_name": "cloudflare-dns.com"},
                    "detour": "Proxy",
                },
                {"tag": "local-dns", "type": "udp", "server": "223.5.5.5", "server_port": 53},
                {"tag": "fakeip-dns", "type": "fakeip", "inet4_range": fake4, "inet6_range": fake6},
            ],
            "rules": [
                {"rule_set": "custom-blacklist", "action": "reject"},
                {"rule_set": "custom-greylist", "action": "route", "server": "fakeip-dns", "rewrite_ttl": 60, "query_type": ["A", "AAAA"]},
                {"rule_set": "custom-ddns", "action": "route", "server": "local-dns", "rewrite_ttl": 60},
                {"inbound": dns_inbounds, "rule_set": "custom-ddns", "action": "route", "server": "local-dns", "rewrite_ttl": 60},
                {"inbound": dns_inbounds, "rule_set": ["geosite-cn", "geosite-geolocation-cn", "geosite-icloud@cn", "geosite-apple@cn"], "action": "route", "server": "local-dns", "rewrite_ttl": 60},
                {"inbound": dns_inbounds, "rule_set": ["geosite-geolocation-!cn"], "action": "route", "server": "fakeip-dns", "rewrite_ttl": 60, "query_type": ["A", "AAAA"]},
                {"inbound": dns_inbounds, "query_type": ["A", "AAAA"], "action": "route", "server": "fakeip-dns", "rewrite_ttl": 60},
                {"rule_set": ["geosite-cn", "geosite-geolocation-cn", "geosite-icloud@cn", "geosite-apple@cn"], "action": "route", "server": "local-dns", "rewrite_ttl": 60},
                {"rule_set": ["geosite-geolocation-!cn"], "action": "route", "server": "remote-dns", "rewrite_ttl": 60},
            ],
        },
        "inbounds": inbounds,
        "outbounds": [],
        "route": {
            "auto_detect_interface": True,
            "default_domain_resolver": "remote-dns",
            "rule_set": [
                local_rule_set("geosite-geolocation-!cn", "/etc/sing-box/rules/geosite/geolocation-!cn.srs", "binary"),
                local_rule_set("geosite-cn", "/etc/sing-box/rules/geosite/cn.srs", "binary"),
                local_rule_set("geosite-geolocation-cn", "/etc/sing-box/rules/geosite/geolocation-cn.srs", "binary"),
                local_rule_set("geosite-icloud@cn", "/etc/sing-box/rules/geosite/icloud@cn.srs", "binary"),
                local_rule_set("geosite-apple@cn", "/etc/sing-box/rules/geosite/apple@cn.srs", "binary"),
                local_rule_set("geoip-cn", "/etc/sing-box/rules/geoip/cn.srs", "binary"),
                local_rule_set("custom-whitelist", "/etc/sing-box/custom-rules/whitelist.json"),
                local_rule_set("custom-blacklist", "/etc/sing-box/custom-rules/blacklist.json"),
                local_rule_set("custom-greylist", "/etc/sing-box/custom-rules/greylist.json"),
                local_rule_set("custom-ddns", "/etc/sing-box/custom-rules/ddns.json"),
            ],
            "rules": [
                {"inbound": dns_inbounds, "action": "hijack-dns"},
                {"inbound": "tproxy-in", "action": "sniff", "sniffer": ["tls", "http"], "timeout": "300ms"},
                {"rule_set": "custom-blacklist", "outbound": "block"},
                {"rule_set": "custom-whitelist", "outbound": "direct"},
                {"rule_set": "custom-ddns", "outbound": "direct"},
                {"rule_set": "custom-greylist", "outbound": "Proxy"},
                {"ip_cidr": [fake4, fake6], "outbound": "Proxy"},
                {"ip_is_private": True, "outbound": "direct"},
                {"rule_set": ["geosite-geolocation-!cn"], "outbound": "Proxy"},
                {"rule_set": ["geosite-cn", "geosite-geolocation-cn", "geosite-icloud@cn", "geosite-apple@cn", "geoip-cn"], "outbound": "direct"},
            ],
            "final": "direct",
        },
        "experimental": {
            "cache_file": {"enabled": True, "store_fakeip": True},
            "clash_api": {
                "external_controller": f"{lan_ip}:9090",
                "external_ui": "/etc/sing-box/ui",
                "secret": ui_secret,
                "default_mode": "rule",
            },
        },
    }


def main():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    MANAGER_DIR.mkdir(parents=True, exist_ok=True)
    RULE_DIR.mkdir(parents=True, exist_ok=True)
    simple_mode = ask_yes_no("Use simple mode? Start first, edit nodes and advanced options later in UI.", True)
    lan_ip = ask("LAN IPv4 address for sing-box/UI", default_lan_ip())
    if simple_mode:
        fake4 = DEFAULT_FAKE4
        fake6 = DEFAULT_FAKE6
        ipv6_dns = ""
    else:
        fake4 = ask("FakeIP IPv4 range", DEFAULT_FAKE4)
        fake6 = ask("FakeIP IPv6 range", DEFAULT_FAKE6)
        ipv6_dns = ask("IPv6 DNS listen address, empty to disable", "")
        if ipv6_dns:
            ipaddress.ip_address(ipv6_dns)
    ipaddress.ip_network(fake4, strict=False)
    ipaddress.ip_network(fake6, strict=False)
    nodes = initial_nodes_from_file()
    if nodes is None:
        if simple_mode or ask_yes_no("Use two placeholder template nodes and edit them later in UI?", True):
            nodes = template_nodes()
        else:
            node_count = ask_int("Initial node count", 2)
            nodes = []
            for index in range(1, node_count + 1):
                default_type = "hysteria2" if index == 1 else "vless"
                nodes.append(node_from_prompt(index, default_type))
    secret = secrets.token_urlsafe(24)
    base = base_config(lan_ip, secret, fake4, fake6, ipv6_dns)
    default_node = nodes[0]["outbound"]["tag"]
    groups = {
        "proxy": {"default": default_node, "interrupt_exist_connections": True},
        "auto": {"url": "https://www.gstatic.com/generate_204", "interval": "2m", "tolerance": 50},
        "direct": {"type": "direct", "tag": "direct"},
        "block": {"type": "block", "tag": "block"},
        "fakeip": {"tag": "fakeip-dns", "inet4_range": fake4, "inet6_range": fake6},
        "ddns": {"dns": "local"},
    }
    for name in ("whitelist", "blacklist", "greylist", "ddns"):
        write_json(RULE_DIR / f"{name}.json", empty_rule_set())
    write_json(BASE_CONFIG_PATH, base)
    write_json(NODES_PATH, nodes)
    write_json(GROUPS_PATH, groups)
    token_path = CONFIG_DIR / "rule-ui" / "token"
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(secrets.token_urlsafe(32) + "\n", encoding="utf-8")
    token_path.chmod(0o600)
    import sys
    sys.path.insert(0, "/opt/singbox-rule-ui")
    from app import render_config
    write_json(CONFIG_PATH, render_config(nodes=nodes, groups=groups, rule_dir=RULE_DIR))


if __name__ == "__main__":
    main()
