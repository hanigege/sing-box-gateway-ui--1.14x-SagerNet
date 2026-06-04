#!/usr/bin/env python3
import json
import ipaddress
import subprocess
from pathlib import Path


CONFIG_PATH = Path("/etc/sing-box/config.json")
RESOLV_PATH = Path("/etc/resolv.conf")


def default_lan_ip():
    out = subprocess.check_output(["ip", "-o", "-4", "route", "get", "1.1.1.1"], text=True)
    parts = out.split()
    if "src" not in parts:
        raise RuntimeError("cannot detect LAN IPv4 address")
    return parts[parts.index("src") + 1]


def assigned_ipv6_addresses():
    try:
        out = subprocess.check_output(["ip", "-o", "-6", "addr", "show", "scope", "global"], text=True)
    except Exception:
        return []
    addresses = []
    for line in out.splitlines():
        parts = line.split()
        if "inet6" not in parts:
            continue
        value = parts[parts.index("inet6") + 1].split("/", 1)[0]
        try:
            addresses.append(ipaddress.IPv6Address(value))
        except ValueError:
            continue
    return addresses


def preferred_ipv6_listener(lan_ip):
    addresses = assigned_ipv6_addresses()
    if not addresses:
        return ""
    expected_candidates = []
    try:
        last_octet = int(ipaddress.IPv4Address(lan_ip).packed[-1])
        suffix = str(last_octet)
        expected_candidates = [
            ipaddress.IPv6Address(f"fd88::{suffix}{suffix}"),
            ipaddress.IPv6Address(f"fd88::{suffix * 4}") if len(suffix) == 1 else None,
        ]
    except Exception:
        expected_candidates = []
    for expected in expected_candidates:
        if expected and expected in addresses:
            return str(expected)

    def score(address):
        text = str(address)
        if address.is_private and "ff:fe" not in text:
            return 0
        if address.is_private:
            return 1
        return 2

    return str(sorted(addresses, key=score)[0])


def remove_inbound_tag(config, tag):
    for section in ("dns", "route"):
        for rule in config.get(section, {}).get("rules", []) or []:
            if not isinstance(rule, dict):
                continue
            inbound = rule.get("inbound")
            if isinstance(inbound, list) and tag in inbound:
                inbound[:] = [item for item in inbound if item != tag]
                if len(inbound) == 1:
                    rule["inbound"] = inbound[0]
            elif inbound == tag:
                rule.pop("inbound", None)


def main():
    if not CONFIG_PATH.exists():
        return 0
    lan_ip = default_lan_ip()
    ipv6_listen = preferred_ipv6_listener(lan_ip)
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    changed = False

    inbounds = config.get("inbounds", []) or []
    kept_inbounds = []
    for inbound in inbounds:
        if not isinstance(inbound, dict):
            kept_inbounds.append(inbound)
            continue
        if inbound.get("tag") == "dns-in" and inbound.get("listen") != lan_ip:
            inbound["listen"] = lan_ip
            changed = True
        if inbound.get("tag") == "dns-in-v6":
            if ipv6_listen:
                if inbound.get("listen") != ipv6_listen:
                    inbound["listen"] = ipv6_listen
                    changed = True
            else:
                remove_inbound_tag(config, "dns-in-v6")
                changed = True
                continue
        kept_inbounds.append(inbound)
    if kept_inbounds != inbounds:
        config["inbounds"] = kept_inbounds

    clash = config.setdefault("experimental", {}).setdefault("clash_api", {})
    controller = f"{lan_ip}:9090"
    if clash.get("external_controller") != controller:
        clash["external_controller"] = controller
        changed = True

    if changed:
        CONFIG_PATH.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Updated sing-box listeners for {lan_ip}.")
    else:
        print(f"sing-box listeners already match {lan_ip}.")

    RESOLV_PATH.unlink(missing_ok=True)
    RESOLV_PATH.write_text(
        f"nameserver {lan_ip}\n"
        "nameserver 223.5.5.5\n"
        "nameserver 1.1.1.1\n"
        "options timeout:2 attempts:2\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
