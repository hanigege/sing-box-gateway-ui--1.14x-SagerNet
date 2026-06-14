#!/usr/bin/env python3
import json
import shutil
import sys
import time
from pathlib import Path


CONFIG_PATH = Path("/etc/sing-box/config.json")
RULE_DIR = Path("/etc/sing-box/custom-rules")
TAGS = {
    "whitelist": "custom-whitelist",
    "blacklist": "custom-blacklist",
    "greylist": "custom-greylist",
    "ddns": "custom-ddns",
}
LOCAL_DNS_SERVER = {
    "tag": "local-dns",
    "type": "udp",
    "server": "119.29.29.29",
    "server_port": 53,
    # 国内直连域名优先使用 DNSPod UDP，当前 sing-box 版本没有 DNS 上游并发/自动备用组；223.5.5.5 只作为手动回退参考，不能伪装成自动备份。
}
DDNS_REMOTE_DNS_SERVER = {
    "tag": "ddns-remote-dns",
    "type": "udp",
    "server": "1.1.1.1",
    "server_port": 53,
    "detour": "Proxy",
    # DDNS 代理解析独立于通用 remote-dns，避免 DoH 旧连接拖慢直连 DDNS 域名解析。
}


def stamp():
    return time.strftime("%Y%m%d-%H%M%S")


def load_config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(config):
    backup = CONFIG_PATH.with_name(f"config.json.bak-rule-ui-{stamp()}")
    shutil.copy2(CONFIG_PATH, backup)
    CONFIG_PATH.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return backup


def empty_rule_set():
    return {"version": 3, "rules": []}


def ensure_rule_files():
    RULE_DIR.mkdir(parents=True, exist_ok=True)
    for name in TAGS:
        path = RULE_DIR / f"{name}.json"
        if not path.exists():
            path.write_text(json.dumps(empty_rule_set(), indent=2) + "\n", encoding="utf-8")


def ensure_route_rule_set(config):
    route = config.setdefault("route", {})
    rule_sets = route.setdefault("rule_set", [])
    existing = {item.get("tag") for item in rule_sets if isinstance(item, dict)}
    for name, tag in TAGS.items():
        if tag in existing:
            continue
        rule_sets.append(
            {
                "type": "local",
                "tag": tag,
                "format": "source",
                "path": str(RULE_DIR / f"{name}.json"),
            }
        )


def has_rule(rules, tag, outbound=None, server=None):
    for rule in rules:
        if rule.get("rule_set") != tag:
            continue
        if outbound and rule.get("outbound") != outbound:
            continue
        if server and rule.get("server") != server:
            continue
        return True
    return False


def insert_after_sniff(route_rules, new_rules):
    insert_at = 0
    for idx, rule in enumerate(route_rules):
        if rule.get("action") in ("hijack-dns", "sniff"):
            insert_at = idx + 1
    for rule in reversed(new_rules):
        route_rules.insert(insert_at, rule)


def ensure_route_rules(config):
    route_rules = config.setdefault("route", {}).setdefault("rules", [])
    new_rules = []
    if not has_rule(route_rules, TAGS["blacklist"], outbound="block"):
        new_rules.append({"rule_set": TAGS["blacklist"], "outbound": "block"})
    if not has_rule(route_rules, TAGS["whitelist"], outbound="direct"):
        new_rules.append({"rule_set": TAGS["whitelist"], "outbound": "direct"})
    if not has_rule(route_rules, TAGS["ddns"], outbound="direct"):
        new_rules.append({"rule_set": TAGS["ddns"], "outbound": "direct"})
    if not has_rule(route_rules, TAGS["greylist"], outbound="Proxy"):
        new_rules.append({"rule_set": TAGS["greylist"], "outbound": "Proxy"})
    if new_rules:
        insert_after_sniff(route_rules, new_rules)


def ensure_dns_rules(config):
    dns_rules = config.setdefault("dns", {}).setdefault("rules", [])
    blacklist_rule = {
        "rule_set": TAGS["blacklist"],
        "action": "reject",
    }
    whitelist_rule = {
        "rule_set": TAGS["whitelist"],
        "action": "route",
        "server": "local-dns",
        "rewrite_ttl": 60,
    }
    inbound_rule = {
        "inbound": ["dns-in", "dns-in-v6"],
        "rule_set": TAGS["ddns"],
        "action": "route",
        "server": "local-dns",
        "rewrite_ttl": 60,
    }
    global_rule = {
        "rule_set": TAGS["ddns"],
        "action": "route",
        "server": "local-dns",
        "rewrite_ttl": 60,
    }
    dns_rules[:] = [
        rule
        for rule in dns_rules
        if not (
            (rule.get("rule_set") == TAGS["blacklist"] and rule.get("action") == "reject")
            or (rule.get("rule_set") == TAGS["whitelist"] and rule.get("server") == "local-dns")
        )
    ]
    dns_rules.insert(0, blacklist_rule)
    # 白名单在 DNS 层也要直连解析；否则 LAN 入站 FakeIP 兜底会先把域名解析成代理用 FakeIP。
    dns_rules.insert(1, whitelist_rule)
    if not has_rule(dns_rules, TAGS["ddns"], server="local-dns"):
        dns_rules.insert(2, global_rule)
    has_inbound = any(
        rule.get("rule_set") == TAGS["ddns"]
        and rule.get("server") == "local-dns"
        and rule.get("inbound")
        for rule in dns_rules
    )
    if not has_inbound:
        dns_rules.insert(3, inbound_rule)


def ensure_local_dns_server(config):
    servers = config.setdefault("dns", {}).setdefault("servers", [])
    target = None
    for server in servers:
        if isinstance(server, dict) and server.get("tag") == "local-dns":
            target = server
            break
    if target is None:
        servers.append(json.loads(json.dumps(LOCAL_DNS_SERVER)))
        return
    target.clear()
    # 旧安装可能仍是 223.5.5.5 或不可用 DoH；集成时收敛到实测可用的 DNSPod UDP，避免本地规则继续走错误上游。
    target.update(json.loads(json.dumps(LOCAL_DNS_SERVER)))


def ensure_ddns_remote_dns_server(config):
    servers = config.setdefault("dns", {}).setdefault("servers", [])
    target = None
    for server in servers:
        if isinstance(server, dict) and server.get("tag") == DDNS_REMOTE_DNS_SERVER["tag"]:
            target = server
            break
    if target is None:
        servers.append(json.loads(json.dumps(DDNS_REMOTE_DNS_SERVER)))
        return
    target.clear()
    # 安装集成时同步修正 DDNS 专用代理解析上游，保证 UI 后续切到代理解析不会复用 remote-dns。
    target.update(json.loads(json.dumps(DDNS_REMOTE_DNS_SERVER)))


def main():
    ensure_rule_files()
    config = load_config()
    before = json.dumps(config, sort_keys=True)
    ensure_route_rule_set(config)
    ensure_route_rules(config)
    ensure_local_dns_server(config)
    ensure_ddns_remote_dns_server(config)
    ensure_dns_rules(config)
    after = json.dumps(config, sort_keys=True)
    if before == after:
        print("Config already integrated.")
        return
    backup = save_config(config)
    print(f"Updated {CONFIG_PATH}")
    print(f"Backup: {backup}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"install failed: {exc}", file=sys.stderr)
        sys.exit(1)
