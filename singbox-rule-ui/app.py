#!/usr/bin/env python3
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import ipaddress
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlencode, unquote, urlparse
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
RULE_DIR = Path(os.environ.get("RULE_UI_RULE_DIR", "/etc/sing-box/custom-rules"))
CONFIG_PATH = Path(os.environ.get("RULE_UI_SING_BOX_CONFIG", "/etc/sing-box/config.json"))
TOKEN_FILE = Path(os.environ.get("RULE_UI_TOKEN_FILE", "/etc/sing-box/rule-ui/token"))
MANAGER_DIR = Path(os.environ.get("RULE_UI_MANAGER_DIR", "/etc/sing-box/manager"))
CLASH_API_URL = os.environ.get("RULE_UI_CLASH_API_URL", "").rstrip("/")
CLASH_API_SECRET = os.environ.get("RULE_UI_CLASH_API_SECRET", "")
BASE_CONFIG_PATH = MANAGER_DIR / "base.json"
NODES_PATH = MANAGER_DIR / "nodes.json"
GROUPS_PATH = MANAGER_DIR / "groups.json"
BACKUP_DIR = MANAGER_DIR / "backups"
RULE_UPDATE_LAST_PATH = MANAGER_DIR / "rule-update-last.json"
RULE_UPDATE_SCRIPT = Path(os.environ.get("RULE_UI_RULE_UPDATE_SCRIPT", "/usr/local/sbin/update-sing-box-rules-jsdelivr"))
RULE_UPDATE_TIMER = os.environ.get("RULE_UI_RULE_UPDATE_TIMER", "update-sing-box-rules-jsdelivr.timer")
RULE_UPDATE_SERVICE = os.environ.get("RULE_UI_RULE_UPDATE_SERVICE", "update-sing-box-rules-jsdelivr.service")
TPROXY_SERVICE = os.environ.get("RULE_UI_TPROXY_SERVICE", "sing-box-tproxy.service")
RULE_UI_SERVICE = os.environ.get("RULE_UI_SERVICE", "singbox-rule-ui.service")
TPROXY_SCRIPT = Path(os.environ.get("RULE_UI_TPROXY_SCRIPT", "/usr/local/sbin/sing-box-tproxy-setup"))
TPROXY_SYSCTL = Path(os.environ.get("RULE_UI_TPROXY_SYSCTL", "/etc/sysctl.d/99-sing-box-tproxy.conf"))
RADVD_CONF = Path(os.environ.get("RULE_UI_RADVD_CONF", "/etc/radvd.conf"))
RADVD_SERVICE = os.environ.get("RULE_UI_RADVD_SERVICE", "radvd.service")
ENABLE_RADVD = os.environ.get("SING_BOX_GATEWAY_ENABLE_RADVD", os.environ.get("RULE_UI_ENABLE_RADVD", "0")).lower() in ("1", "true", "yes", "on")
TPROXY_PORT = int(os.environ.get("RULE_UI_TPROXY_PORT", "9888"))
TPROXY_MARK = int(os.environ.get("RULE_UI_TPROXY_MARK", "1"))
TPROXY_TABLE = int(os.environ.get("RULE_UI_TPROXY_TABLE", "100"))
LISTS = {
    "whitelist": {"title": "White List", "outbound": "direct"},
    "blacklist": {"title": "Black List", "outbound": "block"},
    "greylist": {"title": "Grey List", "outbound": "Proxy"},
    "ddns": {"title": "Local DDNS", "outbound": "direct"},
}
CUSTOM_TAGS = {
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
    # 国内直连域名只会路由到一个 local-dns；当前 sing-box 没有 DNS 并发/备用组，UI 只能明确选择单个上游。
}
LOCAL_DNS_CHOICES = {
    "dnspod": {"label": "DNSPod", "server": "119.29.29.29", "server_port": 53},
    "alidns": {"label": "AliDNS", "server": "223.5.5.5", "server_port": 53},
    "114dns": {"label": "114 DNS", "server": "114.114.114.114", "server_port": 53},
}
DEFAULT_LOCAL_DNS_CHOICE = "dnspod"
LOCAL_DNS_BY_SERVER = {item["server"]: key for key, item in LOCAL_DNS_CHOICES.items()}
ENTRY_TYPES = ("domain", "domain_suffix", "domain_keyword", "domain_regex", "ip_cidr")
LIST_ENTRY_TYPES = {
    "whitelist": ENTRY_TYPES,
    "blacklist": ENTRY_TYPES,
    "greylist": ENTRY_TYPES,
    "ddns": ("domain_suffix", "domain"),
}
DOMAIN_RE = re.compile(r"^[A-Za-z0-9_*.-]+$")
SPECIAL_OUTBOUNDS = {"Proxy", "Auto", "direct", "block"}
SUPPORTED_NODE_TYPES = {"hysteria2", "vless"}
BACKUP_VERSION = 1
LOG_LEVELS = {"trace", "debug", "info", "warn", "warning", "error", "fatal", "panic"}
LEGACY_APP_RULE_SETS = {
    "geosite-ai",
    "geosite-youtube",
    "geosite-google",
    "geosite-github",
    "geosite-cloudflare",
    "geosite-netflix",
    "geosite-facebook",
    "geosite-instagram",
    "geosite-tiktok",
    "geosite-jetbrains",
    "geosite-spotify",
    "geosite-disney",
    "geosite-hbo",
    "geosite-amazon",
    "geosite-adobe",
    "geosite-steam",
    "geosite-category-pt@!cn",
    "geosite-category-cryptocurrency",
    "geoip-netflix",
    "geoip-facebook",
}


def now_stamp():
    return time.strftime("%Y%m%d-%H%M%S")


def ensure_dirs():
    RULE_DIR.mkdir(parents=True, exist_ok=True)
    MANAGER_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)


def get_token():
    ensure_dirs()
    if TOKEN_FILE.exists():
        token = TOKEN_FILE.read_text(encoding="utf-8").strip()
        if token:
            return token
    token = secrets.token_urlsafe(32)
    TOKEN_FILE.write_text(token + "\n", encoding="utf-8")
    TOKEN_FILE.chmod(0o600)
    return token


def empty_rule_set():
    return {"version": 3, "rules": []}


def rule_path(name):
    if name not in LISTS:
        raise ValueError("unknown list")
    return RULE_DIR / f"{name}.json"


def backup_file(path):
    if not path.exists():
        return None
    backup_dir = RULE_DIR / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / f"{path.name}.bak-{now_stamp()}"
    shutil.copy2(path, target)
    return str(target)


def backup_manager_file(path):
    if not path.exists():
        return None
    target = BACKUP_DIR / f"{path.name}.bak-{now_stamp()}"
    shutil.copy2(path, target)
    return str(target)


def load_json(path, fallback):
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def restore_file(path, backup):
    if backup and Path(backup).exists():
        shutil.copy2(backup, path)


def read_text_if_exists(path):
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def clash_api_settings():
    url = CLASH_API_URL
    secret = CLASH_API_SECRET
    if (not url or not secret) and CONFIG_PATH.exists():
        try:
            clash = load_json(CONFIG_PATH, {}).get("experimental", {}).get("clash_api", {})
            if not url:
                controller = str(clash.get("external_controller", "")).strip()
                if controller:
                    url = controller if controller.startswith(("http://", "https://")) else f"http://{controller}"
            if not secret:
                secret = str(clash.get("secret", "")).strip()
        except Exception:
            pass
    return (url or "http://127.0.0.1:9090").rstrip("/"), secret


def normalize_entry(entry):
    kind = str(entry.get("type", "domain_suffix")).strip()
    value = str(entry.get("value", "")).strip().lower().rstrip(".")
    if kind not in ENTRY_TYPES:
        raise ValueError(f"Unsupported type: {kind}")
    if not value:
        raise ValueError("Empty value is not allowed")
    if kind == "ip_cidr":
        try:
            # IP/CIDR 规则会直接影响 route 命中顺序，必须规范成真实网段，避免主机地址伪装成网段被保存。
            return {"type": kind, "value": str(ipaddress.ip_network(value, strict=True))}
        except Exception as exc:
            raise ValueError(f"Invalid IP/CIDR value: {value}") from exc
    if kind != "domain_regex" and not DOMAIN_RE.match(value):
        raise ValueError(f"Invalid domain value: {value}")
    return {"type": kind, "value": value}


def normalize_entries(entries):
    seen = set()
    normalized = []
    for raw in entries:
        item = normalize_entry(raw)
        key = (item["type"], item["value"])
        if key in seen:
            continue
        seen.add(key)
        normalized.append(item)
    normalized.sort(key=lambda item: (item["type"], item["value"]))
    return normalized


def normalize_list_entries(name, entries):
    allowed = LIST_ENTRY_TYPES.get(name, ENTRY_TYPES)
    normalized = normalize_entries(entries)
    invalid = sorted({item["type"] for item in normalized if item["type"] not in allowed})
    if invalid:
        raise ValueError(f"Unsupported type for {name}: {', '.join(invalid)}")
    return normalized


def normalize_tag(value):
    tag = str(value or "").strip()
    if not re.match(r"^[A-Za-z0-9_.@-]{1,64}$", tag):
        raise ValueError(f"Invalid node tag: {tag}")
    if tag in SPECIAL_OUTBOUNDS:
        raise ValueError(f"Reserved node tag: {tag}")
    return tag


def normalize_host(value):
    host = str(value or "").strip()
    if not host or len(host) > 253:
        raise ValueError("Invalid server")
    return host


def normalize_port(value):
    try:
        port = int(value)
    except Exception as exc:
        raise ValueError("Invalid port") from exc
    if port < 1 or port > 65535:
        raise ValueError("Invalid port")
    return port


def normalize_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("1", "true", "yes", "on"):
            return True
        if lowered in ("0", "false", "no", "off"):
            return False
    if value in (0, 1):
        return bool(value)
    raise ValueError("Invalid boolean value")


def normalize_number(value, default=None):
    if value in ("", None):
        return default
    try:
        return int(value)
    except Exception as exc:
        raise ValueError(f"Invalid number: {value}") from exc


def normalize_url(value, default):
    url = str(value or "").strip() or default
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")
    return url


def normalize_non_negative_number(value, default=0):
    number = normalize_number(value, default)
    if number is None or number < 0:
        raise ValueError(f"Invalid non-negative number: {value}")
    return number


def normalize_positive_number(value, default=None):
    number = normalize_number(value, default)
    if number is not None and number <= 0:
        raise ValueError(f"Invalid positive number: {value}")
    return number


def normalize_cidr(value, default=None, strict=False):
    cidr = str(value or "").strip()
    if not cidr:
        return default
    try:
        return str(ipaddress.ip_network(cidr, strict=strict))
    except Exception as exc:
        hint = ""
        if strict:
            hint = "; use a network address, for example 28.0.0.0/8"
        raise ValueError(f"Invalid CIDR: {value}{hint}") from exc


def normalize_node(raw):
    if not isinstance(raw, dict):
        raise ValueError("node must be an object")
    outbound = dict(raw.get("outbound") or {})
    node_type = str(outbound.get("type") or raw.get("type") or "").strip()
    if node_type not in SUPPORTED_NODE_TYPES:
        raise ValueError(f"Unsupported node type: {node_type}")
    tag = normalize_tag(outbound.get("tag") or raw.get("tag"))
    outbound["type"] = node_type
    outbound["tag"] = tag
    outbound["server"] = normalize_host(outbound.get("server"))
    outbound["server_port"] = normalize_port(outbound.get("server_port"))
    if node_type == "hysteria2":
        if not str(outbound.get("password", "")).strip():
            raise ValueError(f"{tag}: password is required")
        outbound["password"] = str(outbound["password"]).strip()
        up = normalize_positive_number(outbound.get("up_mbps"), None)
        down = normalize_positive_number(outbound.get("down_mbps"), None)
        if up is not None:
            outbound["up_mbps"] = up
        if down is not None:
            outbound["down_mbps"] = down
    if node_type == "vless":
        if not str(outbound.get("uuid", "")).strip():
            raise ValueError(f"{tag}: uuid is required")
        outbound["uuid"] = str(outbound["uuid"]).strip()
        brutal = outbound.get("multiplex", {}).get("brutal") if isinstance(outbound.get("multiplex"), dict) else None
        if isinstance(brutal, dict):
            up = normalize_positive_number(brutal.get("up_mbps"), None)
            down = normalize_positive_number(brutal.get("down_mbps"), None)
            if up is not None:
                brutal["up_mbps"] = up
            else:
                brutal.pop("up_mbps", None)
            if down is not None:
                brutal["down_mbps"] = down
            else:
                brutal.pop("down_mbps", None)
    tls = outbound.get("tls")
    if isinstance(tls, dict):
        tls["enabled"] = normalize_bool(tls.get("enabled", True))
        if "insecure" in tls:
            tls["insecure"] = normalize_bool(tls["insecure"])
    return {"enabled": normalize_bool(raw.get("enabled", True)), "outbound": outbound}


def normalize_nodes(nodes):
    normalized = []
    seen = set()
    for raw in nodes or []:
        node = normalize_node(raw)
        tag = node["outbound"]["tag"]
        if tag in seen:
            raise ValueError(f"Duplicate node tag: {tag}")
        seen.add(tag)
        normalized.append(node)
    return normalized


def entries_to_rule_set(entries):
    grouped = {kind: [] for kind in ENTRY_TYPES}
    for item in entries:
        grouped[item["type"]].append(item["value"])
    rule = {kind: values for kind, values in grouped.items() if values}
    return {"version": 3, "rules": [rule] if rule else []}


def extract_initial_manager_data(config):
    outbounds = config.get("outbounds", []) or []
    nodes = []
    proxy = None
    auto = None
    direct = None
    block = None
    fakeip = {}
    local_dns_choice = DEFAULT_LOCAL_DNS_CHOICE
    for outbound in outbounds:
        tag = outbound.get("tag")
        if tag == "Proxy":
            proxy = outbound
        elif tag == "Auto":
            auto = outbound
        elif tag == "direct":
            direct = outbound
        elif tag == "block":
            block = outbound
        elif tag:
            nodes.append({"enabled": True, "outbound": outbound})
    for server in config.get("dns", {}).get("servers", []) or []:
        if isinstance(server, dict) and server.get("type") == "fakeip":
            fakeip = {
                "tag": server.get("tag", "fakeip-dns"),
                "inet4_range": server.get("inet4_range", "28.0.0.0/8"),
                "inet6_range": server.get("inet6_range", "2001:2::/64"),
            }
            break
    for server in config.get("dns", {}).get("servers", []) or []:
        if isinstance(server, dict) and server.get("tag") == "local-dns":
            local_dns_choice = LOCAL_DNS_BY_SERVER.get(str(server.get("server", "")).strip(), DEFAULT_LOCAL_DNS_CHOICE)
            break
    base = json.loads(json.dumps(config))
    base["outbounds"] = []
    groups = {
        "proxy": {
            "default": (proxy or {}).get("default", "Auto"),
            "interrupt_exist_connections": (proxy or {}).get("interrupt_exist_connections", True),
        },
        "auto": {
            "url": (auto or {}).get("url", "https://www.gstatic.com/generate_204"),
            "interval": (auto or {}).get("interval", "30s"),
            "tolerance": (auto or {}).get("tolerance", 50),
            "interrupt_exist_connections": (auto or {}).get("interrupt_exist_connections", True),
        },
        "direct": direct or {"type": "direct", "tag": "direct"},
        "block": block or {"type": "block", "tag": "block"},
        "fakeip": {**{"tag": "fakeip-dns", "inet4_range": "28.0.0.0/8", "inet6_range": "2001:2::/64", "block_quic": True}, **fakeip},
        "dns": {"local": local_dns_choice},
        "ddns": {"dns": "local"},
    }
    return base, normalize_nodes(nodes), groups


def ensure_manager_data():
    ensure_dirs()
    if BASE_CONFIG_PATH.exists() and NODES_PATH.exists() and GROUPS_PATH.exists():
        return
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    base, nodes, groups = extract_initial_manager_data(config)
    if not BASE_CONFIG_PATH.exists():
        write_json(BASE_CONFIG_PATH, base)
    if not NODES_PATH.exists():
        write_json(NODES_PATH, nodes)
    if not GROUPS_PATH.exists():
        write_json(GROUPS_PATH, groups)


def load_nodes():
    ensure_manager_data()
    return normalize_nodes(load_json(NODES_PATH, []))


def load_groups():
    ensure_manager_data()
    groups = load_json(GROUPS_PATH, {})
    groups.setdefault("proxy", {})
    groups.setdefault("auto", {})
    groups.setdefault("direct", {"type": "direct", "tag": "direct"})
    groups.setdefault("block", {"type": "block", "tag": "block"})
    groups.setdefault("fakeip", {})
    groups.setdefault("dns", {})
    groups.setdefault("ddns", {})
    groups["proxy"].setdefault("default", "Auto")
    groups["proxy"].setdefault("interrupt_exist_connections", True)
    groups["proxy"]["interrupt_exist_connections"] = normalize_bool(groups["proxy"]["interrupt_exist_connections"])
    groups["auto"].setdefault("url", "https://www.gstatic.com/generate_204")
    groups["auto"].setdefault("interval", "30s")
    groups["auto"].setdefault("tolerance", 50)
    groups["auto"].setdefault("interrupt_exist_connections", True)
    groups["auto"]["interrupt_exist_connections"] = normalize_bool(groups["auto"]["interrupt_exist_connections"])
    groups["fakeip"].setdefault("tag", "fakeip-dns")
    groups["fakeip"].setdefault("inet4_range", "28.0.0.0/8")
    groups["fakeip"].setdefault("inet6_range", "2001:2::/64")
    # FakeIP QUIC 保护固定开启，避免旧备份或旧 UI 状态把稳定性边界关掉。
    groups["fakeip"]["block_quic"] = True
    if groups["dns"].get("local") not in LOCAL_DNS_CHOICES:
        groups["dns"]["local"] = DEFAULT_LOCAL_DNS_CHOICE
    if groups["ddns"].get("dns") not in ("local", "remote"):
        groups["ddns"]["dns"] = "local"
    return groups


def enabled_node_tags(nodes):
    return [node["outbound"]["tag"] for node in nodes if node.get("enabled", True)]


def render_config(nodes=None, groups=None, rule_dir=RULE_DIR):
    ensure_manager_data()
    nodes = normalize_nodes(nodes if nodes is not None else load_nodes())
    groups = groups or load_groups()
    tags = enabled_node_tags(nodes)
    if not tags:
        raise ValueError("At least one node must be enabled")
    config = load_json(BASE_CONFIG_PATH, {})
    rewrite_custom_rule_paths(config, rule_dir)
    ensure_managed_rule_sets(config)
    remove_legacy_app_rule_sets(config)
    apply_portable_listeners(config)
    apply_cache_file_settings(config)
    apply_local_dns_settings(config, groups)
    apply_fakeip_settings(config, groups)
    apply_blacklist_dns_reject(config)
    apply_greylist_dns_fakeip(config)
    apply_inbound_dns_fakeip_fallback(config)
    apply_ddns_dns_settings(config, groups)
    apply_fakeip_route_rule(config, groups)
    apply_direct_speedtest_route(config)
    apply_direct_telegram_route(config)
    apply_fakeip_quic_policy(config, groups)
    apply_route_final_policy(config)
    proxy_default = groups.get("proxy", {}).get("default", "Auto")
    if proxy_default not in {"Auto", *tags}:
        proxy_default = "Auto"
    proxy = {
        "type": "selector",
        "tag": "Proxy",
        "outbounds": ["Auto", *tags],
        "default": proxy_default,
        "interrupt_exist_connections": normalize_bool(groups.get("proxy", {}).get("interrupt_exist_connections", True)),
    }
    auto = {
        "type": "urltest",
        "tag": "Auto",
        "outbounds": tags,
        "url": groups.get("auto", {}).get("url", "https://www.gstatic.com/generate_204"),
        "interval": groups.get("auto", {}).get("interval", "30s"),
        "tolerance": groups.get("auto", {}).get("tolerance", 50),
        # Auto 切换节点时必须断开已有入站连接，否则旧连接会继续粘在失效节点上。
        "interrupt_exist_connections": normalize_bool(groups.get("auto", {}).get("interrupt_exist_connections", True)),
    }
    direct = groups.get("direct") or {"type": "direct", "tag": "direct"}
    block = groups.get("block") or {"type": "block", "tag": "block"}
    config["outbounds"] = [proxy, auto, *[node["outbound"] for node in nodes if node.get("enabled", True)], direct, block]
    prune_managed_outbound_references(config, tags)
    return config


def prune_managed_outbound_references(config, valid_tags):
    valid = set(valid_tags) | SPECIAL_OUTBOUNDS

    def scrub_outbound_refs(value):
        if isinstance(value, dict):
            for key, item in list(value.items()):
                if key in {"outbound", "detour"} and isinstance(item, str) and item not in valid:
                    # 删除节点后，旧配置里的直连节点引用要回到受管理的 Proxy，避免引用不存在的 outbound。
                    value[key] = "Proxy"
                elif key in {"final", "default"} and isinstance(item, str) and item not in valid:
                    value[key] = "direct" if key == "final" else "Auto"
                elif key == "outbounds" and isinstance(item, list):
                    value[key] = [tag for tag in item if not isinstance(tag, str) or tag in valid]
                else:
                    scrub_outbound_refs(item)
        elif isinstance(value, list):
            for item in value:
                scrub_outbound_refs(item)

    def scrub_dns_detours(value):
        if isinstance(value, dict):
            for key, item in list(value.items()):
                if key == "detour" and isinstance(item, str) and item not in valid:
                    # DNS 的 final/default/server 指向 DNS server tag，不能按 outbound 规则改；只清理 detour。
                    value[key] = "Proxy"
                else:
                    scrub_dns_detours(item)
        elif isinstance(value, list):
            for item in value:
                scrub_dns_detours(item)

    scrub_dns_detours(config.get("dns", {}))
    scrub_outbound_refs(config.get("route", {}))
    for outbound in config.get("outbounds", []) or []:
        if isinstance(outbound, dict):
            scrub_outbound_refs(outbound)


def apply_route_final_policy(config):
    config.setdefault("route", {})["final"] = "direct"


def managed_binary_rule_set(tag, path):
    return {"type": "local", "tag": tag, "format": "binary", "path": path}


def ensure_managed_rule_sets(config):
    route = config.setdefault("route", {})
    rule_sets = route.setdefault("rule_set", [])
    existing = {item.get("tag") for item in rule_sets if isinstance(item, dict)}
    managed = [
        managed_binary_rule_set("geosite-speedtest", "/etc/sing-box/rules/geosite/speedtest.srs"),
        managed_binary_rule_set("geosite-telegram", "/etc/sing-box/rules/geosite/telegram.srs"),
        managed_binary_rule_set("geoip-telegram", "/etc/sing-box/rules/geoip/telegram.srs"),
    ]
    for item in managed:
        if item["tag"] in existing:
            continue
        # 路由规则引用的内置规则集必须在同一份配置里声明，避免旧安装升级后保存出不可启动配置。
        rule_sets.append(item)


def remove_legacy_rule_set_values(value):
    if isinstance(value, list):
        kept = [item for item in value if item not in LEGACY_APP_RULE_SETS]
        if not kept:
            return None
        return kept[0] if len(kept) == 1 else kept
    if value in LEGACY_APP_RULE_SETS:
        return None
    return value


def remove_legacy_app_rule_sets(config):
    route = config.setdefault("route", {})
    route["rule_set"] = [
        item
        for item in route.get("rule_set", []) or []
        if not (isinstance(item, dict) and item.get("tag") in LEGACY_APP_RULE_SETS)
    ]
    for section_name in ("dns", "route"):
        rules = config.setdefault(section_name, {}).setdefault("rules", [])
        cleaned = []
        for rule in rules:
            if not isinstance(rule, dict):
                cleaned.append(rule)
                continue
            if "rule_set" not in rule:
                cleaned.append(rule)
                continue
            updated = dict(rule)
            updated["rule_set"] = remove_legacy_rule_set_values(updated.get("rule_set"))
            if updated["rule_set"] is None:
                continue
            cleaned.append(updated)
        # 旧版本曾把大量应用规则硬编码进 DNS/路由，维护成本高且会放大源失效影响；统一迁移到 geolocation 分流。
        rules[:] = cleaned


def remove_rule_set_value(value, target):
    if value == target:
        return None
    if isinstance(value, list):
        kept = [item for item in value if item != target]
        if not kept:
            return None
        return kept
    return value


def apply_direct_speedtest_route(config):
    rules = config.setdefault("route", {}).setdefault("rules", [])
    direct_rule = {"rule_set": "geosite-speedtest", "outbound": "direct"}
    fakeip_networks = set()
    for server in config.get("dns", {}).get("servers", []) or []:
        if isinstance(server, dict) and server.get("type") == "fakeip":
            fakeip_networks.update(
                str(value)
                for value in (server.get("inet4_range"), server.get("inet6_range"))
                if value
            )
    cleaned = []
    for rule in rules:
        if not isinstance(rule, dict):
            cleaned.append(rule)
            continue
        if rule.get("rule_set") == "geosite-speedtest" and rule.get("outbound") == "direct":
            continue
        rule_set = rule.get("rule_set")
        if rule.get("outbound") == "Proxy" and (
            rule_set == "geosite-speedtest" or (isinstance(rule_set, list) and "geosite-speedtest" in rule_set)
        ):
            updated = dict(rule)
            updated["rule_set"] = remove_rule_set_value(rule_set, "geosite-speedtest")
            if updated.get("rule_set") is None:
                continue
            cleaned.append(updated)
            continue
        cleaned.append(rule)
    rules[:] = cleaned
    insert_at = len(rules)
    for index, rule in enumerate(rules):
        if (
            isinstance(rule, dict)
            and rule.get("outbound") == "Proxy"
            and isinstance(rule.get("ip_cidr"), list)
            and any(str(item) in fakeip_networks for item in rule.get("ip_cidr", []))
        ):
            insert_at = index
            break
        if isinstance(rule, dict) and rule.get("rule_set") in (CUSTOM_TAGS["whitelist"], CUSTOM_TAGS["ddns"], CUSTOM_TAGS["greylist"]):
            insert_at = index + 1
    # 测速流量必须排在 FakeIP 捕获前；否则域名先变成 FakeIP 后会被送进代理。
    rules.insert(insert_at, direct_rule)


def apply_direct_telegram_route(config):
    rules = config.setdefault("route", {}).setdefault("rules", [])
    telegram_rule = {"rule_set": ["geosite-telegram", "geoip-telegram"], "outbound": "Proxy"}
    cleaned = []
    for rule in rules:
        if not isinstance(rule, dict):
            cleaned.append(rule)
            continue
        rule_set = rule.get("rule_set")
        if rule.get("outbound") == "Proxy" and (
            rule_set in ("geosite-telegram", "geoip-telegram")
            or (isinstance(rule_set, list) and any(item in {"geosite-telegram", "geoip-telegram"} for item in rule_set))
        ):
            updated = dict(rule)
            updated["rule_set"] = remove_rule_set_value(
                remove_rule_set_value(rule_set, "geosite-telegram"),
                "geoip-telegram",
            )
            if updated.get("rule_set") is None:
                continue
            cleaned.append(updated)
            continue
        cleaned.append(rule)
    rules[:] = cleaned
    insert_at = len(rules)
    for index, rule in enumerate(rules):
        if (
            isinstance(rule, dict)
            and rule.get("outbound") == "Proxy"
            and isinstance(rule.get("ip_cidr"), list)
            and any(str(item).startswith(("28.", "2001:2", "2408:")) for item in rule.get("ip_cidr", []))
        ):
            insert_at = index
            break
        if isinstance(rule, dict) and rule.get("rule_set") == "geosite-speedtest":
            insert_at = index + 1
    # Telegram 客户端常直接连接官方 IP 段，必须在 FakeIP 捕获和 UDP/443 阻断前先送代理。
    rules.insert(insert_at, telegram_rule)


def apply_fakeip_route_rule(config, groups):
    fakeip = groups.get("fakeip", {})
    fakeip4 = normalize_cidr(fakeip.get("inet4_range", "28.0.0.0/8"), "28.0.0.0/8")
    fakeip6 = normalize_cidr(fakeip.get("inet6_range", "2001:2::/64"), "2001:2::/64")
    fake_networks = {
        "28.0.0.0/8",
        "2001:2::/64",
        fakeip4,
        fakeip6,
    }
    rules = config.setdefault("route", {}).setdefault("rules", [])
    rules[:] = [
        rule
        for rule in rules
        if not (
            isinstance(rule, dict)
            and rule.get("outbound") == "Proxy"
            and isinstance(rule.get("ip_cidr"), list)
            and any(str(item) in fake_networks for item in rule.get("ip_cidr", []))
        )
    ]
    insert_at = 0
    for index, rule in enumerate(rules):
        if isinstance(rule, dict) and rule.get("rule_set") == CUSTOM_TAGS["greylist"]:
            insert_at = index + 1
            break
    rules.insert(insert_at, {"ip_cidr": [fakeip4, fakeip6], "outbound": "Proxy"})


def apply_fakeip_quic_policy(config, groups):
    fakeip = groups.get("fakeip", {})
    fakeip4 = normalize_cidr(fakeip.get("inet4_range", "28.0.0.0/8"), "28.0.0.0/8")
    fakeip6 = normalize_cidr(fakeip.get("inet6_range", "2001:2::/64"), "2001:2::/64")
    fake_networks = {
        "28.0.0.0/8",
        "2001:2::/64",
        fakeip4,
        fakeip6,
    }
    rules = config.setdefault("route", {}).setdefault("rules", [])
    rules[:] = [
        rule
        for rule in rules
        if not (
            isinstance(rule, dict)
            and rule.get("network") == "udp"
            and rule.get("port") == 443
            and rule.get("outbound") == "block"
            and isinstance(rule.get("ip_cidr"), list)
            and any(str(item) in fake_networks for item in rule.get("ip_cidr", []))
        )
    ]
    insert_at = 0
    for index, rule in enumerate(rules):
        if (
            isinstance(rule, dict)
            and rule.get("outbound") == "Proxy"
            and isinstance(rule.get("ip_cidr"), list)
            and any(str(item) in {fakeip4, fakeip6} for item in rule.get("ip_cidr", []))
        ):
            insert_at = index
            break
    # 只拦 FakeIP 的 UDP/443，促使浏览器回落 TCP，避免 QUIC 长连接压住代理节点；真实 IP 的游戏 UDP 不受影响。
    rules.insert(insert_at, {"network": "udp", "port": 443, "ip_cidr": [fakeip4, fakeip6], "outbound": "block"})


def apply_cache_file_settings(config):
    cache = config.setdefault("experimental", {}).setdefault("cache_file", {})
    cache["enabled"] = True
    cache["store_fakeip"] = True


def apply_portable_listeners(config):
    lan_ip = default_lan_ip()
    ipv6_listen = preferred_ipv6_listener(lan_ip)
    inbounds = config.get("inbounds", []) or []
    kept_inbounds = []
    for inbound in inbounds:
        if not isinstance(inbound, dict):
            kept_inbounds.append(inbound)
            continue
        listen = str(inbound.get("listen", ""))
        try:
            listen_port = int(inbound.get("listen_port") or 0)
            is_ipv4_listen = isinstance(ipaddress.ip_address(listen), ipaddress.IPv4Address)
        except Exception:
            listen_port = 0
            is_ipv4_listen = False
        if lan_ip and (inbound.get("tag") == "dns-in" or (inbound.get("type") == "direct" and listen_port == 53 and is_ipv4_listen)):
            inbound["listen"] = lan_ip
        if inbound.get("tag") == "dns-in-v6":
            if ipv6_listen:
                inbound["listen"] = ipv6_listen
            else:
                remove_inbound_tag(config, "dns-in-v6")
                continue
        kept_inbounds.append(inbound)
    if kept_inbounds != inbounds:
        config["inbounds"] = kept_inbounds
    if ipv6_listen and not any(isinstance(item, dict) and item.get("tag") == "dns-in-v6" for item in kept_inbounds):
        config.setdefault("inbounds", []).append({"type": "direct", "tag": "dns-in-v6", "listen": ipv6_listen, "listen_port": 53})
        add_inbound_tag(config, "dns-in-v6")
    clash = config.setdefault("experimental", {}).setdefault("clash_api", {})
    controller = str(clash.get("external_controller", "")).strip()
    controller_host = controller.rsplit(":", 1)[0] if ":" in controller else controller
    try:
        is_ipv4_controller = isinstance(ipaddress.ip_address(controller_host), ipaddress.IPv4Address)
    except Exception:
        is_ipv4_controller = False
    if lan_ip and (not controller or is_ipv4_controller):
        clash["external_controller"] = f"{lan_ip}:9090"


def assigned_ipv6_addresses():
    result = run_command(["ip", "-o", "-6", "addr", "show", "scope", "global"], timeout=8)
    addresses = []
    for line in result["stdout"].splitlines():
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


def add_inbound_tag(config, tag):
    for section in ("dns", "route"):
        for rule in config.get(section, {}).get("rules", []) or []:
            if not isinstance(rule, dict):
                continue
            inbound = rule.get("inbound")
            if inbound is None:
                continue
            if isinstance(inbound, list):
                if tag not in inbound:
                    inbound.append(tag)
            elif inbound == "dns-in":
                rule["inbound"] = ["dns-in", tag]


def apply_fakeip_settings(config, groups):
    fakeip = groups.get("fakeip", {})
    inet4_range = normalize_cidr(fakeip.get("inet4_range", "28.0.0.0/8"), "28.0.0.0/8")
    inet6_range = normalize_cidr(fakeip.get("inet6_range", "2001:2::/64"), "2001:2::/64")
    tag = str(fakeip.get("tag", "fakeip-dns")).strip() or "fakeip-dns"
    servers = config.setdefault("dns", {}).setdefault("servers", [])
    target = None
    for server in servers:
        if isinstance(server, dict) and (server.get("type") == "fakeip" or server.get("tag") == tag):
            target = server
            break
    if target is None:
        target = {"tag": tag, "type": "fakeip"}
        servers.append(target)
    target["tag"] = tag
    target["type"] = "fakeip"
    target["inet4_range"] = inet4_range
    target["inet6_range"] = inet6_range


def local_dns_server_config(choice):
    item = LOCAL_DNS_CHOICES.get(choice, LOCAL_DNS_CHOICES[DEFAULT_LOCAL_DNS_CHOICE])
    server = json.loads(json.dumps(LOCAL_DNS_SERVER))
    server["server"] = item["server"]
    server["server_port"] = item["server_port"]
    return server


def apply_local_dns_settings(config, groups):
    servers = config.setdefault("dns", {}).setdefault("servers", [])
    choice = groups.get("dns", {}).get("local", DEFAULT_LOCAL_DNS_CHOICE)
    desired = local_dns_server_config(choice)
    target = None
    for server in servers:
        if isinstance(server, dict) and server.get("tag") == "local-dns":
            target = server
            break
    if target is None:
        servers.append(desired)
        return
    target.clear()
    # local-dns 是国内直连域名的唯一上游，保存时必须按 UI 选择精确写入，不能伪装成并发或备用。
    target.update(desired)


def apply_blacklist_dns_reject(config):
    dns_rules = config.setdefault("dns", {}).setdefault("rules", [])
    dns_rules[:] = [
        rule
        for rule in dns_rules
        if not (isinstance(rule, dict) and rule.get("rule_set") == CUSTOM_TAGS["blacklist"] and rule.get("action") == "reject")
    ]
    dns_rules.insert(0, {"rule_set": CUSTOM_TAGS["blacklist"], "action": "reject"})


def apply_greylist_dns_fakeip(config):
    dns_rules = config.setdefault("dns", {}).setdefault("rules", [])
    dns_rules[:] = [
        rule
        for rule in dns_rules
        if not (
            isinstance(rule, dict)
            and rule.get("rule_set") == CUSTOM_TAGS["greylist"]
            and rule.get("server") == "fakeip-dns"
        )
    ]
    dns_rules.insert(
        1,
        {
            "rule_set": CUSTOM_TAGS["greylist"],
            "action": "route",
            "server": "fakeip-dns",
            "rewrite_ttl": 60,
            "query_type": ["A", "AAAA"],
        },
    )


def apply_inbound_dns_fakeip_fallback(config):
    dns_rules = config.setdefault("dns", {}).setdefault("rules", [])
    dns_inbounds = dns_inbound_tags(config)
    dns_rules[:] = [
        rule
        for rule in dns_rules
        if not (
            isinstance(rule, dict)
            and same_inbound(rule.get("inbound"), dns_inbounds)
            and rule.get("query_type") == ["A", "AAAA"]
            and rule.get("action") == "route"
            and rule.get("server") in ("remote-dns", "fakeip-dns")
            and "rule_set" not in rule
        )
    ]
    insert_at = 0
    for index, rule in enumerate(dns_rules):
        if isinstance(rule, dict) and same_inbound(rule.get("inbound"), dns_inbounds):
            insert_at = index + 1
    dns_rules.insert(
        insert_at,
        {
            "inbound": dns_inbounds,
            "query_type": ["A", "AAAA"],
            "action": "route",
            "server": "fakeip-dns",
            "rewrite_ttl": 60,
        },
    )


def dns_inbound_tags(config):
    tags = []
    for inbound in config.get("inbounds", []) or []:
        if isinstance(inbound, dict) and inbound.get("tag") in ("dns-in", "dns-in-v6"):
            tags.append(inbound["tag"])
    return tags or ["dns-in"]


def same_inbound(value, tags):
    expected = set(tags)
    if isinstance(value, list):
        return set(value) == expected
    return value in expected and len(expected) == 1


def apply_ddns_dns_settings(config, groups):
    mode = groups.get("ddns", {}).get("dns", "local")
    server = "remote-dns" if mode == "remote" else "local-dns"
    dns_rules = config.setdefault("dns", {}).setdefault("rules", [])
    for rule in dns_rules:
        if isinstance(rule, dict) and rule.get("rule_set") == CUSTOM_TAGS["ddns"]:
            rule["action"] = "route"
            rule["server"] = server
            rule["rewrite_ttl"] = 60


def collect_outbound_references(value, refs=None):
    if refs is None:
        refs = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"outbound", "detour", "final", "default"} and isinstance(item, str):
                refs.add(item)
            else:
                collect_outbound_references(item, refs)
    elif isinstance(value, list):
        for item in value:
            collect_outbound_references(item, refs)
    return refs


def validate_outbound_references(config):
    defined = {item.get("tag") for item in config.get("outbounds", []) if isinstance(item, dict)}
    refs = collect_outbound_references({"dns": config.get("dns", {}), "route": config.get("route", {})})
    ignored = {None, "remote-dns", "local-dns", "fakeip-dns"}
    missing = sorted(ref for ref in refs if ref not in defined and ref not in ignored)
    if missing:
        raise ValueError("Missing outbound referenced by config: " + ", ".join(missing))


def read_entries(name):
    path = rule_path(name)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = []
    for rule in data.get("rules", []):
        for kind in ENTRY_TYPES:
            for value in rule.get(kind, []) or []:
                entries.append({"type": kind, "value": value})
    return normalize_entries(entries)


def write_entries(name, entries):
    normalized = entries if all(isinstance(item, dict) and "type" in item and "value" in item for item in entries) else normalize_entries(entries)
    path = rule_path(name)
    backup = backup_file(path)
    path.write_text(
        json.dumps(entries_to_rule_set(normalized), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return {"name": name, "count": len(normalized), "backup": backup}


def run_command(args, timeout=20):
    proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return {
        "code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def service_status():
    active = run_command(["systemctl", "is-active", "sing-box.service"], timeout=8)
    return active["stdout"] or active["stderr"] or "unknown"


def unit_status(unit):
    active = run_command(["systemctl", "is-active", unit], timeout=8)
    return active["stdout"] or active["stderr"] or "unknown"


def sing_box_memory():
    pid_result = run_command(["systemctl", "show", "sing-box.service", "--property=MainPID", "--value"], timeout=8)
    try:
        pid = int((pid_result["stdout"] or "0").strip())
    except ValueError:
        pid = 0
    if pid <= 0:
        return {"rssBytes": None, "rss": "unknown"}
    status_path = Path(f"/proc/{pid}/status")
    try:
        for line in status_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("VmRSS:"):
                parts = line.split()
                kb = int(parts[1])
                mib = kb / 1024
                return {"pid": pid, "rssBytes": kb * 1024, "rss": f"{mib:.1f} MiB"}
    except Exception:
        pass
    return {"pid": pid, "rssBytes": None, "rss": "unknown"}


def sing_box_version():
    result = run_command(["/usr/local/bin/sing-box", "version"], timeout=8)
    first_line = (result["stdout"] or result["stderr"]).splitlines()[0:1]
    if not first_line:
        return "unknown"
    match = re.search(r"sing-box version\s+(\S+)", first_line[0])
    return match.group(1) if match else first_line[0].strip()


def check_config(config_path=CONFIG_PATH):
    return run_command(["/usr/local/bin/sing-box", "check", "-c", str(config_path)], timeout=20)


def restart_sing_box():
    return run_command(["systemctl", "restart", "sing-box.service"], timeout=20)


def restart_tproxy():
    restart = run_command(["systemctl", "restart", TPROXY_SERVICE], timeout=20)
    status = unit_status(TPROXY_SERVICE)
    code = 0 if restart["code"] == 0 and status == "active" else 1
    return {"code": code, "stdout": restart["stdout"], "stderr": restart["stderr"], "service": status}


def restart_rule_ui_later(delay=1.0):
    def target():
        time.sleep(delay)
        subprocess.run(["systemctl", "restart", RULE_UI_SERVICE], capture_output=True, text=True, timeout=20)

    threading.Thread(target=target, daemon=True).start()


def systemctl_show(unit, properties):
    args = ["systemctl", "show", unit]
    for prop in properties:
        args.append(f"--property={prop}")
    result = run_command(args, timeout=8)
    values = {}
    for line in result["stdout"].splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def default_lan_ip():
    result = run_command(["ip", "-o", "-4", "route", "get", "1.1.1.1"], timeout=8)
    parts = result["stdout"].split()
    if "src" in parts:
        return parts[parts.index("src") + 1]
    return ""


def recent_unit_logs(unit, lines=80):
    result = run_command(["journalctl", "-u", unit, "--no-pager", "-n", str(lines)], timeout=12)
    text = result["stdout"] or result["stderr"]
    parts = re.split(r"(?=^.*Starting update-sing-box-rules-jsdelivr\.service\b)", text, flags=re.MULTILINE)
    return parts[-1] if parts else text


def rule_update_summary(text):
    summary = {"updated": [], "kept": [], "skipped": [], "errors": [], "final": "", "status": "", "requiredOk": False}
    for raw in (text or "").splitlines():
        line = raw.strip()
        message = re.sub(r"^.*update-sing-box-rules-jsdelivr\[\d+\]:\s*", "", line)
        if "downloaded " in message:
            summary["updated"].append(message)
        elif "installed " in message and message not in summary["updated"]:
            summary["updated"].append(message)
            if (
                "geoip/cn.srs" in message
                or "geosite/cn.srs" in message
                or "geosite/geolocation-cn.srs" in message
                or "geosite/speedtest.srs" in message
            ):
                summary["requiredOk"] = True
        elif "keeping existing file" in message:
            summary["kept"].append(message)
        elif "update skipped" in message:
            summary["skipped"].append(message)
        elif message.startswith("ERROR:"):
            summary["errors"].append(message)
        elif "timed out" in message:
            summary["errors"].append(message)
        elif "skipped this update safely" in message:
            summary["final"] = "skipped_safe"
            summary["status"] = "skipped_safe"
            summary["requiredOk"] = True
        elif "service restart skipped" in message and "config checked" in message:
            summary["final"] = "checked"
            summary["status"] = summary["status"] or "checked"
            summary["requiredOk"] = True
        elif "sing-box rule sets updated" in message:
            summary["final"] = "updated"
            summary["status"] = "updated"
    for key in ("updated", "kept", "skipped", "errors"):
        seen = []
        for item in summary[key]:
            if item not in seen:
                seen.append(item)
        summary[key] = seen[-30:]
    return summary


def first_default_interface():
    result = run_command(["ip", "-o", "route", "show", "default"], timeout=8)
    match = re.search(r"\bdev\s+(\S+)", result["stdout"])
    return match.group(1) if match else ""


def current_ipv6_prefixes(interface):
    if not interface:
        return []
    result = run_command(["ip", "-o", "-6", "addr", "show", "dev", interface, "scope", "global"], timeout=8)
    prefixes = []
    for line in result["stdout"].splitlines():
        match = re.search(r"\binet6\s+([0-9a-fA-F:]+/\d+)", line)
        if not match:
            continue
        try:
            network = ipaddress.ip_network(match.group(1), strict=False)
        except ValueError:
            continue
        item = str(network)
        if item not in prefixes:
            prefixes.append(item)
    return prefixes


def global_ipv6_prefixes(interface):
    values = []
    for item in current_ipv6_prefixes(interface):
        try:
            network = ipaddress.ip_network(item, strict=False)
        except ValueError:
            continue
        if not network.is_private and not network.is_link_local and not network.is_multicast:
            values.append(str(network))
    return values


def current_ipv4_prefixes(interface):
    if not interface:
        return []
    result = run_command(["ip", "-o", "-4", "addr", "show", "dev", interface], timeout=8)
    prefixes = []
    for line in result["stdout"].splitlines():
        match = re.search(r"\binet\s+(\d+(?:\.\d+){3}/\d+)", line)
        if not match:
            continue
        try:
            network = ipaddress.ip_network(match.group(1), strict=False)
        except ValueError:
            continue
        item = str(network)
        if item not in prefixes:
            prefixes.append(item)
    return prefixes


def script_ipv6_prefixes(path):
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    values = []
    for raw in re.findall(r"\b[0-9a-fA-F:]+/[0-9]{1,3}\b", text):
        try:
            network = ipaddress.ip_network(raw, strict=False)
        except ValueError:
            continue
        if network.version == 6:
            item = str(network)
            if item not in values:
                values.append(item)
    return values


def outbound_server_ips():
    return [item["address"] for item in resolved_outbound_servers() if item.get("address")]


def outbound_sources(nodes=None):
    if nodes is not None:
        return [node.get("outbound", {}) for node in nodes if node.get("enabled", True)]
    config = load_json(CONFIG_PATH, {})
    return [
        outbound
        for outbound in config.get("outbounds", []) or []
        if isinstance(outbound, dict) and outbound.get("server")
    ]


def resolve_server_addresses(server):
    host = str(server or "").strip()
    if not host:
        return [], "empty server"
    try:
        return [str(ipaddress.ip_address(host))], ""
    except ValueError:
        pass
    addresses, error = resolve_via_public_dns(host)
    if addresses:
        return addresses, ""
    addresses, system_error = resolve_via_system_dns(host)
    if addresses:
        return addresses, ""
    return [], error or system_error or "public DNS returned no address"


def dns_query_name(host):
    encoded = bytearray()
    for label in host.rstrip(".").split("."):
        raw = label.encode("idna")
        if not raw or len(raw) > 63:
            raise ValueError("invalid DNS label")
        encoded.append(len(raw))
        encoded.extend(raw)
    encoded.append(0)
    return bytes(encoded)


def read_dns_name(packet, offset, depth=0):
    if depth > 8:
        raise ValueError("too many DNS compression pointers")
    labels = []
    jumped = False
    end = offset
    while True:
        length = packet[offset]
        if length & 0xC0 == 0xC0:
            pointer = ((length & 0x3F) << 8) | packet[offset + 1]
            labels.extend(read_dns_name(packet, pointer, depth + 1)[0])
            offset += 2
            if not jumped:
                end = offset
            break
        if length == 0:
            offset += 1
            if not jumped:
                end = offset
            break
        offset += 1
        labels.append(packet[offset : offset + length].decode("ascii", errors="replace"))
        offset += length
    return labels, end


def parse_dns_addresses(packet, query_count, answer_count):
    offset = 12
    addresses = []
    for _ in range(query_count):
        _, offset = read_dns_name(packet, offset)
        offset += 4
    for _ in range(answer_count):
        _, offset = read_dns_name(packet, offset)
        rtype = int.from_bytes(packet[offset : offset + 2], "big")
        rclass = int.from_bytes(packet[offset + 2 : offset + 4], "big")
        rdlength = int.from_bytes(packet[offset + 8 : offset + 10], "big")
        offset += 10
        rdata = packet[offset : offset + rdlength]
        offset += rdlength
        if rclass != 1:
            continue
        if rtype == 1 and rdlength == 4:
            addresses.append(str(ipaddress.IPv4Address(rdata)))
        elif rtype == 28 and rdlength == 16:
            addresses.append(str(ipaddress.IPv6Address(rdata)))
    return addresses


def sing_box_dns_endpoint():
    config = load_json(CONFIG_PATH, {})
    for inbound in config.get("inbounds", []) or []:
        if not isinstance(inbound, dict):
            continue
        if inbound.get("tag") == "dns-in" or (inbound.get("type") == "direct" and inbound.get("listen_port") == 53):
            listen = str(inbound.get("listen") or "127.0.0.1")
            port = int(inbound.get("listen_port") or 53)
            return listen, port
    return "127.0.0.1", 53


def query_dns_once(server, port, host, qtype, timeout=4):
    txid = secrets.randbits(16)
    question = dns_query_name(host) + qtype.to_bytes(2, "big") + (1).to_bytes(2, "big")
    packet = (
        txid.to_bytes(2, "big")
        + b"\x01\x00"
        + (1).to_bytes(2, "big")
        + (0).to_bytes(2, "big")
        + (0).to_bytes(2, "big")
        + (0).to_bytes(2, "big")
        + question
    )
    family = socket.AF_INET6 if ":" in server else socket.AF_INET
    with socket.socket(family, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        sock.sendto(packet, (server, port))
        response, _ = sock.recvfrom(4096)
    if len(response) < 12 or int.from_bytes(response[:2], "big") != txid:
        raise OSError("invalid DNS response")
    flags = int.from_bytes(response[2:4], "big")
    rcode = flags & 0x0F
    if rcode != 0:
        raise OSError(f"DNS rcode {rcode}")
    qdcount = int.from_bytes(response[4:6], "big")
    ancount = int.from_bytes(response[6:8], "big")
    return parse_dns_addresses(response, qdcount, ancount)


def resolve_via_sing_box_dns(host):
    server, port = sing_box_dns_endpoint()
    addresses = []
    errors = []
    for qtype in (1, 28):
        try:
            for address in query_dns_once(server, port, host, qtype):
                if address not in addresses:
                    addresses.append(address)
        except OSError as exc:
            errors.append(str(exc))
    if addresses:
        return addresses, ""
    return [], f"sing-box DNS {server}:{port} failed: {'; '.join(errors) or 'no records'}"


def resolve_via_public_dns(host):
    addresses = []
    errors = []
    for server in ("223.5.5.5", "1.1.1.1", "8.8.8.8"):
        for qtype in (1, 28):
            try:
                for address in query_dns_once(server, 53, host, qtype):
                    if address not in addresses:
                        addresses.append(address)
            except OSError as exc:
                errors.append(f"{server}: {exc}")
        if addresses:
            break
    return addresses, "; ".join(errors)


def resolve_via_system_dns(host):
    try:
        records = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except OSError as exc:
        return [], str(exc)
    addresses = []
    for record in records:
        address = record[4][0]
        if address not in addresses:
            addresses.append(address)
    return addresses, ""


def filter_fakeip_addresses(addresses, groups=None):
    fakeip = (groups or load_groups()).get("fakeip", {})
    ranges = []
    for value, fallback in ((fakeip.get("inet4_range"), "28.0.0.0/8"), (fakeip.get("inet6_range"), "2001:2::/64")):
        try:
            ranges.append(ipaddress.ip_network(value or fallback, strict=False))
        except ValueError:
            ranges.append(ipaddress.ip_network(fallback, strict=False))
    filtered = []
    for address in addresses:
        try:
            parsed = ipaddress.ip_address(str(address))
        except ValueError:
            continue
        if any(parsed in network for network in ranges):
            continue
        if str(parsed) not in filtered:
            filtered.append(str(parsed))
    return filtered


def resolved_outbound_servers(nodes=None, groups=None):
    resolved = []
    seen = set()
    groups = groups or load_groups()
    for outbound in outbound_sources(nodes):
        tag = outbound.get("tag") or ""
        server = outbound.get("server")
        addresses, error = resolve_server_addresses(server)
        addresses = filter_fakeip_addresses(addresses, groups)
        if not addresses:
            key = (tag, server, "")
            if key not in seen:
                resolved.append({"tag": tag, "server": server, "address": "", "error": error or "unresolved"})
                seen.add(key)
            continue
        for address in addresses:
            key = (tag, server, address)
            if key in seen:
                continue
            resolved.append({"tag": tag, "server": server, "address": address, "error": ""})
            seen.add(key)
    return resolved


def outbound_server_ip_networks(nodes=None):
    networks = []
    for item in resolved_outbound_servers(nodes):
        address = item.get("address")
        if not address:
            continue
        try:
            parsed = ipaddress.ip_address(str(address))
        except ValueError:
            continue
        network = f"{parsed}/32" if parsed.version == 4 else f"{parsed}/128"
        if network not in networks:
            networks.append(network)
    return networks


def collapse_network_strings(items):
    networks = []
    for item in items:
        try:
            networks.append(ipaddress.ip_network(item, strict=False))
        except ValueError:
            continue
    collapsed = sorted(ipaddress.collapse_addresses(networks), key=lambda net: (net.version, int(net.network_address), net.prefixlen))
    return [str(net) for net in collapsed]


def tproxy_bypass_sets(nodes=None, groups=None):
    iface = first_default_interface()
    fakeip = (groups or load_groups()).get("fakeip", {})
    fakeip4 = normalize_cidr(fakeip.get("inet4_range", "28.0.0.0/8"), "28.0.0.0/8")
    fakeip6 = normalize_cidr(fakeip.get("inet6_range", "2001:2::/64"), "2001:2::/64")
    bypass4 = [
        "0.0.0.0/8",
        "10.0.0.0/8",
        "100.64.0.0/10",
        "127.0.0.0/8",
        "169.254.0.0/16",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "224.0.0.0/4",
        "240.0.0.0/4",
    ]
    bypass6 = [
        "::/128",
        "::1/128",
        "fc00::/7",
        "fe80::/10",
        "ff00::/8",
    ]
    for item in current_ipv4_prefixes(iface):
        if item not in bypass4:
            bypass4.append(item)
    for item in current_ipv6_prefixes(iface):
        if item not in bypass6:
            bypass6.append(item)
    node_networks = outbound_server_ip_networks(nodes)
    for item in node_networks:
        target = bypass6 if ":" in item else bypass4
        if item not in target:
            target.append(item)
    return {
        "interface": iface,
        "bypass4": collapse_network_strings(bypass4),
        "bypass6": collapse_network_strings(bypass6),
        "fakeip4": fakeip4,
        "fakeip6": fakeip6,
        "nodeServerIpNetworks": node_networks,
        "nodeServers": resolved_outbound_servers(nodes, groups),
    }


def format_nft_elements(items, indent="      "):
    return ",\n".join(f"{indent}{item}" for item in items)


def render_tproxy_script(nodes=None, groups=None):
    sets = tproxy_bypass_sets(nodes=nodes, groups=groups)
    iface = sets["interface"]
    if not iface:
        raise ValueError("Cannot detect default network interface")
    bypass4 = format_nft_elements(sets["bypass4"])
    bypass6 = format_nft_elements(sets["bypass6"])
    return f"""#!/usr/bin/env bash
set -euo pipefail

# Generated by Sing-box UI. LAN DNS port 53 is redirected to sing-box DNS.
# Only FakeIP ranges are captured by TProxy; real IPv4/IPv6 destinations stay on the normal route.

IFACE={json.dumps(iface)}
TPROXY_PORT={TPROXY_PORT}
TPROXY_MARK={TPROXY_MARK}
TPROXY_TABLE={TPROXY_TABLE}

sysctl -w net.ipv4.ip_forward=1 >/dev/null
sysctl -w net.ipv4.conf.all.rp_filter=0 >/dev/null
sysctl -w net.ipv4.conf.default.rp_filter=0 >/dev/null
sysctl -w "net.ipv4.conf.${{IFACE}}.rp_filter=0" >/dev/null 2>&1 || true
sysctl -w net.ipv6.conf.all.forwarding=1 >/dev/null
sysctl -w net.ipv6.conf.default.forwarding=1 >/dev/null
sysctl -w "net.ipv6.conf.${{IFACE}}.forwarding=1" >/dev/null 2>&1 || true
sysctl -w "net.ipv6.conf.${{IFACE}}.accept_ra=2" >/dev/null 2>&1 || true
sysctl -w "net.ipv6.conf.${{IFACE}}.accept_ra_defrtr=1" >/dev/null 2>&1 || true

# IPv4/IPv6 FakeIP 都必须把 TProxy 标记包送回本机 lo；缺少 IPv6 表会让浏览器拿到 AAAA FakeIP 后仍无法进入 sing-box。
ip rule add fwmark "${{TPROXY_MARK}}" table "${{TPROXY_TABLE}}" priority 100 2>/dev/null || true
ip -6 rule add fwmark "${{TPROXY_MARK}}" table "${{TPROXY_TABLE}}" priority 100 2>/dev/null || true
ip route replace local 0.0.0.0/0 dev lo table "${{TPROXY_TABLE}}"
ip -6 route replace local ::/0 dev lo table "${{TPROXY_TABLE}}"

nft delete table inet singbox_tproxy 2>/dev/null || true
nft -f - <<NFT
add table inet singbox_tproxy

table inet singbox_tproxy {{
  set bypass4 {{
    type ipv4_addr
    flags interval
    elements = {{
{bypass4}
    }}
  }}

  set bypass6 {{
    type ipv6_addr
    flags interval
    elements = {{
{bypass6}
    }}
  }}

  set proxy4 {{
    type ipv4_addr
    flags interval
    elements = {{
      91.108.4.0/22,
      91.108.8.0/22,
      91.108.12.0/22,
      91.108.16.0/22,
      91.108.20.0/22,
      91.108.56.0/22,
      95.161.64.0/20,
      149.154.160.0/20
    }}
  }}

  set proxy6 {{
    type ipv6_addr
    flags interval
    elements = {{
      2001:67c:4e8::/48,
      2001:b28:f23c::/47,
      2001:b28:f23f::/48
    }}
  }}

  chain prerouting {{
    type filter hook prerouting priority mangle; policy accept;

    iifname != "${{IFACE}}" return
    udp dport 53 return
    tcp dport 53 return

    ip daddr {sets["fakeip4"]} meta l4proto {{ tcp, udp }} meta mark set "${{TPROXY_MARK}}" tproxy ip to :"${{TPROXY_PORT}}" accept
    ip6 daddr {sets["fakeip6"]} meta l4proto {{ tcp, udp }} meta mark set "${{TPROXY_MARK}}" tproxy ip6 to :"${{TPROXY_PORT}}" accept
    ip daddr @proxy4 meta l4proto {{ tcp, udp }} meta mark set "${{TPROXY_MARK}}" tproxy ip to :"${{TPROXY_PORT}}" accept
    ip6 daddr @proxy6 meta l4proto {{ tcp, udp }} meta mark set "${{TPROXY_MARK}}" tproxy ip6 to :"${{TPROXY_PORT}}" accept
    meta l4proto {{ tcp, udp }} return
  }}

  chain dns_hijack {{
    type nat hook prerouting priority dstnat; policy accept;

    iifname != "${{IFACE}}" return
    udp dport 53 redirect to :53
    tcp dport 53 redirect to :53
  }}

  chain postrouting {{
    type nat hook postrouting priority srcnat; policy accept;

    oifname "${{IFACE}}" ip saddr 10.0.0.0/8 ip daddr != 10.0.0.0/8 ip daddr != 100.64.0.0/10 ip daddr != 127.0.0.0/8 ip daddr != 169.254.0.0/16 ip daddr != 172.16.0.0/12 ip daddr != 192.168.0.0/16 masquerade
  }}
}}
NFT
"""


def ipv6_dns_listeners():
    config = load_json(CONFIG_PATH, {})
    values = []
    for inbound in config.get("inbounds", []) or []:
        if not isinstance(inbound, dict) or inbound.get("listen_port") != 53:
            continue
        listen = str(inbound.get("listen") or "").strip()
        if not listen:
            continue
        try:
            address = ipaddress.ip_address(listen)
        except ValueError:
            continue
        if address.version == 6 and not address.is_link_local:
            text = str(address)
            if text not in values:
                values.append(text)
    return values


def render_radvd_conf(interface=None):
    iface = interface or first_default_interface()
    prefixes = global_ipv6_prefixes(iface)
    if not iface or not prefixes:
        return ""
    prefix_blocks = "\n".join(
        f"""    prefix {prefix} {{
        AdvOnLink on;
        AdvAutonomous on;
        AdvRouterAddr off;
    }};"""
        for prefix in prefixes
    )
    return f"""# Generated by Sing-box UI. Advertise this gateway as the preferred IPv6 router.
interface {iface} {{
    AdvSendAdvert on;
    MaxRtrAdvInterval 30;
    MinRtrAdvInterval 10;
    AdvDefaultPreference high;
    AdvManagedFlag off;
    AdvOtherConfigFlag on;
    AdvDefaultLifetime 1800;
{prefix_blocks}
}};
"""


def sync_radvd(interface):
    conf = render_radvd_conf(interface)
    if not conf:
        return {"code": 0, "skipped": True, "reason": "no global IPv6 prefix"}
    # 只有用户显式开启 RA 广播时才会走到这里；解除 mask 是为了避免默认安装的保护挡住手动 opt-in。
    unmask = run_command(["systemctl", "unmask", RADVD_SERVICE], timeout=20)
    if unmask["code"] != 0:
        return {"code": 1, "stdout": unmask["stdout"], "stderr": unmask["stderr"]}
    with tempfile.TemporaryDirectory(prefix="radvd-sync-") as temp_name:
        conf_path = Path(temp_name) / "radvd.conf"
        conf_path.write_text(conf, encoding="utf-8")
        check = run_command(["radvd", "-c", "-C", str(conf_path)], timeout=8)
        if check["code"] != 0:
            return {"code": 1, "stdout": check["stdout"], "stderr": check["stderr"]}
        if RADVD_CONF.exists():
            shutil.copy2(RADVD_CONF, RADVD_CONF.with_name(f"{RADVD_CONF.name}.bak.{now_stamp()}"))
        shutil.copy2(conf_path, RADVD_CONF)
    restart = run_command(["systemctl", "enable", "--now", RADVD_SERVICE], timeout=20)
    status = unit_status(RADVD_SERVICE)
    code = 0 if restart["code"] == 0 and status == "active" else 1
    return {"code": code, "stdout": restart["stdout"], "stderr": restart["stderr"], "service": status}


def render_tproxy_sysctl(interface):
    return "\n".join(
        [
            "net.ipv4.ip_forward=1",
            "net.ipv4.conf.all.rp_filter=0",
            "net.ipv4.conf.default.rp_filter=0",
            f"net.ipv4.conf.{interface}.rp_filter=0",
            "net.ipv6.conf.all.forwarding=1",
            "net.ipv6.conf.default.forwarding=1",
            f"net.ipv6.conf.{interface}.forwarding=1",
            f"net.ipv6.conf.{interface}.accept_ra=2",
            f"net.ipv6.conf.{interface}.accept_ra_defrtr=1",
            "",
        ]
    )


def sync_tproxy(nodes=None, groups=None):
    script = render_tproxy_script(nodes=nodes, groups=groups)
    sets = tproxy_bypass_sets(nodes=nodes, groups=groups)
    with tempfile.TemporaryDirectory(prefix="tproxy-sync-") as temp_name:
        temp_dir = Path(temp_name)
        script_path = temp_dir / "sing-box-tproxy-setup"
        sysctl_path = temp_dir / "99-sing-box-tproxy.conf"
        script_path.write_text(script, encoding="utf-8")
        script_path.chmod(0o755)
        sysctl_path.write_text(render_tproxy_sysctl(sets["interface"]), encoding="utf-8")
        check = run_command(["bash", "-n", str(script_path)], timeout=8)
        if check["code"] != 0:
            return {"code": 1, "stdout": check["stdout"], "stderr": check["stderr"], "sets": sets}
        if TPROXY_SCRIPT.exists():
            shutil.copy2(TPROXY_SCRIPT, TPROXY_SCRIPT.with_name(f"{TPROXY_SCRIPT.name}.bak.{now_stamp()}"))
        if TPROXY_SYSCTL.exists():
            shutil.copy2(TPROXY_SYSCTL, TPROXY_SYSCTL.with_name(f"{TPROXY_SYSCTL.name}.bak.{now_stamp()}"))
        shutil.copy2(script_path, TPROXY_SCRIPT)
        TPROXY_SCRIPT.chmod(0o755)
        shutil.copy2(sysctl_path, TPROXY_SYSCTL)
    if ENABLE_RADVD and shutil.which("radvd"):
        radvd = sync_radvd(sets["interface"])
    else:
        reason = "disabled; set SING_BOX_GATEWAY_ENABLE_RADVD=1 to advertise this host as an IPv6 router"
        if ENABLE_RADVD and not shutil.which("radvd"):
            reason = "radvd not installed"
        radvd = {"code": 0, "skipped": True, "reason": reason}
    restart = run_command(["systemctl", "restart", TPROXY_SERVICE], timeout=20)
    status = unit_status(TPROXY_SERVICE)
    code = 0 if restart["code"] == 0 and status == "active" and radvd.get("code", 0) == 0 else 1
    return {"code": code, "stdout": restart["stdout"], "stderr": restart["stderr"], "service": status, "sets": sets, "radvd": radvd}


def maintenance_status():
    timer = systemctl_show(RULE_UPDATE_TIMER, ["ActiveState", "SubState", "LastTriggerUSec", "NextElapseUSecRealtime", "Result"])
    service = systemctl_show(RULE_UPDATE_SERVICE, ["ActiveState", "SubState", "Result"])
    rule_logs = recent_unit_logs(RULE_UPDATE_SERVICE, 100)
    last_manual = load_json(RULE_UPDATE_LAST_PATH, {})
    journal_summary = rule_update_summary(rule_logs)
    summary = last_manual.get("summary") or journal_summary
    log = last_manual.get("log") or rule_logs
    result_text = last_manual.get("result") or timer.get("Result", "") or service.get("Result", "")
    last_text = last_manual.get("finishedAt") or timer.get("LastTriggerUSec", "")
    iface = first_default_interface()
    current_v6 = current_ipv6_prefixes(iface)
    script_v6 = script_ipv6_prefixes(TPROXY_SCRIPT)
    return {
        "ruleUpdate": {
            "script": str(RULE_UPDATE_SCRIPT),
            "scriptExists": RULE_UPDATE_SCRIPT.exists(),
            "timer": RULE_UPDATE_TIMER,
            "timerActive": unit_status(RULE_UPDATE_TIMER),
            "next": timer.get("NextElapseUSecRealtime", ""),
            "last": last_text,
            "result": result_text,
            "serviceState": service.get("ActiveState", ""),
            "log": log,
            "summary": summary,
        },
        "tproxy": {
            "service": TPROXY_SERVICE,
            "serviceActive": unit_status(TPROXY_SERVICE),
            "script": str(TPROXY_SCRIPT),
            "scriptExists": TPROXY_SCRIPT.exists(),
            "defaultInterface": iface,
            "currentIpv6Prefixes": current_v6,
            "currentIpv4Prefixes": current_ipv4_prefixes(iface),
            "scriptIpv6Prefixes": script_v6,
            "ipv6PrefixMatches": not script_v6 or any(item in script_v6 for item in current_v6),
            "outboundServerIps": outbound_server_ips(),
            "outboundServers": resolved_outbound_servers(),
            "planned": tproxy_bypass_sets(),
        },
    }


def update_rule_sets():
    if not RULE_UPDATE_SCRIPT.exists():
        return {"code": 1, "stdout": "", "stderr": f"Missing script: {RULE_UPDATE_SCRIPT}"}
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    write_json(
        RULE_UPDATE_LAST_PATH,
        {
            "startedAt": started,
            "finishedAt": "",
            "result": "running",
            "code": None,
            "log": "Manual rule update is running.",
            "summary": {"updated": [], "kept": [], "skipped": [], "errors": [], "final": "Manual rule update is running.", "requiredOk": False},
        },
    )
    try:
        result = run_command([str(RULE_UPDATE_SCRIPT)], timeout=300)
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.stdout or "").strip() if isinstance(exc.stdout, str) else ""
        stderr = (exc.stderr or "").strip() if isinstance(exc.stderr, str) else ""
        result = {
            "code": 124,
            "stdout": stdout,
            "stderr": (stderr + "\nManual rule update is taking longer than expected. Existing rule files were kept.").strip(),
        }
    text = "\n".join(item for item in (result.get("stdout"), result.get("stderr")) if item)
    result["summary"] = rule_update_summary(text)
    write_json(
        RULE_UPDATE_LAST_PATH,
        {
            "startedAt": started,
            "finishedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
            "result": "success" if result["code"] == 0 else "slow" if result["code"] == 124 else "failed",
            "code": result["code"],
            "log": text,
            "summary": result["summary"],
        },
    )
    return result


def clash_api_request(path, method="GET", payload=None, timeout=8):
    api_url, api_secret = clash_api_settings()
    body = None
    headers = {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if api_secret:
        headers["Authorization"] = f"Bearer {api_secret}"
    request = Request(f"{api_url}{path}", data=body, method=method, headers=headers)
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return {"ok": True, "code": response.status, "data": json.loads(raw or "{}")}
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        return {"ok": False, "code": exc.code, "error": raw or str(exc)}
    except (URLError, TimeoutError, OSError) as exc:
        return {"ok": False, "code": 0, "error": str(exc)}


def clash_runtime_snapshot(kind):
    paths = {
        "configs": "/configs",
        "connections": "/connections",
        "rules": "/rules",
        "traffic": "/traffic",
    }
    if kind not in paths:
        raise ValueError("Unsupported runtime endpoint")
    result = clash_api_request(paths[kind], timeout=10)
    if not result["ok"]:
        return result
    return {"ok": True, "code": result["code"], "data": result.get("data", {})}


def normalize_log_level(value):
    level = str(value or "").strip().lower()
    aliases = {"warning": "warn"}
    level = aliases.get(level, level)
    if level not in LOG_LEVELS:
        raise ValueError(f"Invalid log level: {value}")
    return level


def current_log_level():
    config = load_json(CONFIG_PATH, {}) if CONFIG_PATH.exists() else {}
    return normalize_log_level(config.get("log", {}).get("level", "warn"))


def set_log_level(level):
    level = normalize_log_level(level)
    ensure_manager_data()
    base = load_json(BASE_CONFIG_PATH, {})
    previous_base = backup_manager_file(BASE_CONFIG_PATH)
    previous_config = backup_manager_file(CONFIG_PATH)
    old_level = normalize_log_level(base.get("log", {}).get("level", current_log_level()))
    base.setdefault("log", {})
    # 日志级别会影响实时诊断数据量，必须写入 base 配置；否则下一次保存节点/规则会把运行态改动覆盖掉。
    base["log"]["level"] = level
    write_json(BASE_CONFIG_PATH, base)
    try:
        config = render_config()
        validate_outbound_references(config)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(MANAGER_DIR), prefix=".log-level-", suffix=".json", delete=False) as handle:
            staged_path = Path(handle.name)
            handle.write(json.dumps(config, indent=2, ensure_ascii=False) + "\n")
        check = check_config(staged_path)
        staged_path.unlink(missing_ok=True)
        if check["code"] != 0:
            restore_file(BASE_CONFIG_PATH, previous_base)
            return {"ok": False, "error": "Config check failed. Log level was not changed.", "check": check, "restart": None, "state": load_state()}
        write_json(CONFIG_PATH, config)
        restart = restart_sing_box()
        if restart["code"] != 0 or service_status() != "active":
            restore_file(BASE_CONFIG_PATH, previous_base)
            restore_file(CONFIG_PATH, previous_config)
            rollback_restart = restart_sing_box()
            return {
                "ok": False,
                "error": "Restart failed. Previous log level was restored.",
                "check": check,
                "restart": restart,
                "rollback": {"restart": rollback_restart, "service": service_status()},
                "state": load_state(),
            }
        return {"ok": True, "level": level, "previous": old_level, "check": check, "restart": restart, "state": load_state()}
    except Exception:
        restore_file(BASE_CONFIG_PATH, previous_base)
        restore_file(CONFIG_PATH, previous_config)
        raise


def get_proxy_state():
    proxy_result = clash_api_request("/proxies/Proxy")
    if not proxy_result["ok"]:
        return proxy_result
    proxy_data = proxy_result["data"]
    data = {
        "now": proxy_data.get("now"),
        "all": proxy_data.get("all", []),
        "autoNow": None,
        "autoHistory": [],
    }
    if "Auto" in data["all"]:
        auto_result = clash_api_request("/proxies/Auto")
        if auto_result["ok"]:
            auto_data = auto_result["data"]
            data["autoNow"] = auto_data.get("now")
            data["autoHistory"] = auto_data.get("history", [])
        else:
            data["autoError"] = auto_result.get("error") or "Auto status unavailable"
    return {"ok": True, "code": proxy_result["code"], "data": data}


def set_proxy_now(tag):
    if tag != "Auto" and tag not in enabled_node_tags(load_nodes()):
        raise ValueError(f"Unknown enabled node: {tag}")
    return clash_api_request("/proxies/Proxy", method="PUT", payload={"name": tag})


def set_proxy_now_checked(tag, attempts=8, delay=0.5):
    last_result = None
    for _ in range(attempts):
        last_result = set_proxy_now(tag)
        if last_result["ok"]:
            state = get_proxy_state()
            if state.get("ok") and state.get("data", {}).get("now") == tag:
                return {"ok": True, "code": last_result["code"], "data": state["data"]}
        time.sleep(delay)
    state = get_proxy_state()
    return {
        "ok": False,
        "code": (last_result or {}).get("code", 0),
        "error": f"Runtime proxy did not switch to {tag}",
        "data": state.get("data") if isinstance(state, dict) else None,
    }


def read_delay_history(tag):
    result = clash_api_request(f"/proxies/{quote(tag, safe='')}")
    if not result["ok"]:
        return None
    history = result.get("data", {}).get("history") or []
    delays = [item.get("delay") for item in history if isinstance(item, dict) and isinstance(item.get("delay"), int)]
    return delays[-1] if delays else None


def test_node_delay(tag, url=None, timeout_ms=5000):
    query = urlencode({"timeout": int(timeout_ms), "url": url or load_groups().get("auto", {}).get("url", "https://www.gstatic.com/generate_204")})
    result = clash_api_request(f"/proxies/{quote(tag, safe='')}/delay?{query}", timeout=max(8, int(timeout_ms / 1000) + 3))
    if not result["ok"]:
        return {"tag": tag, "ok": False, "delay": None, "error": result["error"]}
    delay = result.get("data", {}).get("delay")
    return {"tag": tag, "ok": isinstance(delay, int), "delay": delay if isinstance(delay, int) else None, "error": None if isinstance(delay, int) else "No delay returned"}


def refresh_proxy_delays():
    nodes = load_nodes()
    tags = enabled_node_tags(nodes)
    values = {}
    api_error = None
    # 先请求 Auto 自身测速，让 sing-box 的 urltest 按真实运行态更新 now；单测节点只用于 UI 展示。
    auto_probe = test_node_delay("Auto", timeout_ms=8000) if tags else None
    if auto_probe and not auto_probe["ok"]:
        api_error = auto_probe.get("error")
    for tag in tags:
        item = test_node_delay(tag)
        values[tag] = item
        if not item["ok"] and not api_error:
            api_error = item.get("error")
    return {"available": api_error is None, "error": api_error, "delays": values, "autoProbe": auto_probe}


def get_node_delays(test=False):
    if test:
        return refresh_proxy_delays()
    nodes = load_nodes()
    tags = enabled_node_tags(nodes)
    values = {}
    api_error = None
    for tag in tags:
        values[tag] = {"tag": tag, "ok": True, "delay": read_delay_history(tag), "error": None}
    return {"available": api_error is None, "error": api_error, "delays": values}


def measure_dns_delay(choice, host="www.qq.com"):
    item = LOCAL_DNS_CHOICES[choice]
    started = time.monotonic()
    try:
        answers = query_dns_once(item["server"], item["server_port"], host, 1, timeout=3)
        elapsed = int(round((time.monotonic() - started) * 1000))
        return {
            "choice": choice,
            "label": item["label"],
            "server": item["server"],
            "server_port": item["server_port"],
            "ok": bool(answers),
            "delay": elapsed if answers else None,
            "answers": answers[:3],
            "error": "" if answers else "no A record",
        }
    except Exception as exc:
        return {
            "choice": choice,
            "label": item["label"],
            "server": item["server"],
            "server_port": item["server_port"],
            "ok": False,
            "delay": None,
            "answers": [],
            "error": str(exc),
        }


def get_dns_delays():
    # 这里测的是网关机到各国内 DNS 的实际 UDP 查询耗时，供用户手动选择单个 local-dns 上游。
    return {
        "host": "www.qq.com",
        "items": {choice: measure_dns_delay(choice) for choice in LOCAL_DNS_CHOICES},
    }


def normalize_payload_lists(raw_lists):
    if not isinstance(raw_lists, dict):
        raise ValueError("lists must be an object")
    return {name: normalize_list_entries(name, raw_lists.get(name, [])) for name in LISTS}


def normalize_payload_groups(raw_groups, nodes=None):
    groups = load_groups()
    tags = set(enabled_node_tags(nodes or load_nodes()))
    if isinstance(raw_groups, dict):
        proxy = raw_groups.get("proxy")
        if isinstance(proxy, dict):
            groups["proxy"]["default"] = str(proxy.get("default", groups["proxy"]["default"]))
            if groups["proxy"]["default"] not in {"Auto", *tags}:
                raise ValueError(f"Unknown proxy default: {groups['proxy']['default']}")
            groups["proxy"]["interrupt_exist_connections"] = normalize_bool(
                proxy.get("interrupt_exist_connections", groups["proxy"]["interrupt_exist_connections"])
            )
        auto = raw_groups.get("auto")
        if isinstance(auto, dict):
            groups["auto"]["url"] = normalize_url(auto.get("url", groups["auto"]["url"]), groups["auto"]["url"])
            groups["auto"]["interval"] = str(auto.get("interval", groups["auto"]["interval"])).strip() or groups["auto"]["interval"]
            groups["auto"]["tolerance"] = normalize_non_negative_number(auto.get("tolerance", groups["auto"]["tolerance"]), 50)
            groups["auto"]["interrupt_exist_connections"] = normalize_bool(
                auto.get("interrupt_exist_connections", groups["auto"].get("interrupt_exist_connections", True))
            )
        fakeip = raw_groups.get("fakeip")
        if isinstance(fakeip, dict):
            groups["fakeip"]["inet4_range"] = normalize_cidr(
                fakeip.get("inet4_range", groups["fakeip"]["inet4_range"]),
                groups["fakeip"]["inet4_range"],
                strict=True,
            )
            groups["fakeip"]["inet6_range"] = normalize_cidr(
                fakeip.get("inet6_range", groups["fakeip"]["inet6_range"]),
                groups["fakeip"]["inet6_range"],
                strict=True,
            )
            # FakeIP QUIC 保护是网关稳定边界：关闭会让浏览器 QUIC 长连接压住代理链路和连接表。
            groups["fakeip"]["block_quic"] = True
        dns = raw_groups.get("dns")
        if isinstance(dns, dict):
            local_dns = str(dns.get("local", groups["dns"].get("local", DEFAULT_LOCAL_DNS_CHOICE))).strip()
            if local_dns not in LOCAL_DNS_CHOICES:
                raise ValueError(f"Invalid local DNS upstream: {local_dns}")
            # 国内 DNS 上游影响所有直连域名解析，只接受内置候选，避免把错误地址写成“已保存”。
            groups["dns"]["local"] = local_dns
        ddns = raw_groups.get("ddns")
        if isinstance(ddns, dict):
            mode = str(ddns.get("dns", groups["ddns"].get("dns", "local"))).strip()
            if mode not in ("local", "remote"):
                raise ValueError(f"Invalid DDNS DNS mode: {mode}")
            groups["ddns"]["dns"] = mode
    return groups


def rewrite_custom_rule_paths(config, staged_dir):
    route = config.get("route", {})
    for item in route.get("rule_set", []) or []:
        if not isinstance(item, dict):
            continue
        tag = item.get("tag")
        for name, custom_tag in CUSTOM_TAGS.items():
            if tag == custom_tag:
                item["path"] = str(staged_dir / f"{name}.json")


def write_rule_files(target_dir, normalized_lists):
    target_dir.mkdir(parents=True, exist_ok=True)
    for name, entries in normalized_lists.items():
        (target_dir / f"{name}.json").write_text(
            json.dumps(entries_to_rule_set(entries), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


def staged_check(normalized_lists, nodes=None, groups=None):
    ensure_dirs()
    with tempfile.TemporaryDirectory(prefix=".staged-", dir=str(RULE_DIR)) as temp_name:
        staged_dir = Path(temp_name)
        write_rule_files(staged_dir, normalized_lists)
        try:
            config = render_config(nodes=nodes, groups=groups, rule_dir=staged_dir)
            validate_outbound_references(config)
        except Exception as exc:
            return {"code": 1, "stdout": "", "stderr": str(exc)}
        staged_config = staged_dir / "config.json"
        staged_config.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return check_config(staged_config)


def apply_all(normalized_lists, nodes, groups):
    backups = {
        "config": backup_manager_file(CONFIG_PATH),
        "nodes": backup_manager_file(NODES_PATH),
        "groups": backup_manager_file(GROUPS_PATH),
    }
    saved = {}
    for name in LISTS:
        saved[name] = write_entries(name, normalized_lists[name])
    backup_manager_file(BASE_CONFIG_PATH)
    backup_manager_file(NODES_PATH)
    backup_manager_file(GROUPS_PATH)
    write_json(NODES_PATH, nodes)
    write_json(GROUPS_PATH, groups)
    write_json(CONFIG_PATH, render_config(nodes=nodes, groups=groups, rule_dir=RULE_DIR))
    return {"rules": saved, "backups": backups}


def apply_proxy_default(tag):
    nodes = load_nodes()
    tags = {"Auto", *enabled_node_tags(nodes)}
    if tag not in tags:
        raise ValueError(f"Unknown proxy default: {tag}")
    groups = load_groups()
    groups.setdefault("proxy", {})
    groups["proxy"]["default"] = tag
    normalized_lists = {name: read_entries(name) for name in LISTS}
    check = staged_check(normalized_lists, nodes=nodes, groups=groups)
    if check["code"] != 0:
        return {"ok": False, "error": "Config check failed. Default proxy was not saved.", "check": check, "state": load_state()}
    result = apply_all(normalized_lists, nodes, groups)
    restart = restart_sing_box()
    rollback = None
    if restart["code"] != 0 or service_status() != "active":
        rollback_apply(result)
        rollback_restart = restart_sing_box()
        rollback = {"restart": rollback_restart, "service": service_status()}
        return {
            "ok": False,
            "error": "Restart failed. Previous config was restored.",
            "check": check,
            "saved": result,
            "restart": restart,
            "rollback": rollback,
            "state": load_state(),
        }
    tproxy_sync = sync_tproxy(nodes=nodes, groups=groups)
    # 默认节点关系到真实出站路径，不能只写配置或只切运行态；保存后必须校验 Clash API 的当前选择已经对齐。
    proxy = set_proxy_now_checked(tag)
    # sing-box 重启后 Auto 的 now/history 可能短暂为空，主动触发一次测速，避免 UI 新增节点后看不到 Auto 当前判断。
    auto_probe = test_node_delay("Auto", timeout_ms=8000) if "Auto" in tags else None
    if not proxy["ok"]:
        return {
            "ok": False,
            "error": proxy.get("error") or "Runtime proxy switch failed.",
            "check": check,
            "saved": result,
            "restart": restart,
            "rollback": rollback,
            "tproxySync": tproxy_sync,
            "proxy": proxy,
            "autoProbe": auto_probe,
            "maintenance": maintenance_status(),
            "state": load_state(),
        }
    return {
        "ok": True,
        "error": "",
        "check": check,
        "saved": result,
        "restart": restart,
        "rollback": rollback,
        "tproxySync": tproxy_sync,
        "proxy": proxy,
        "autoProbe": auto_probe,
        "maintenance": maintenance_status(),
        "state": load_state(),
    }


def export_backup_payload():
    ensure_manager_data()
    return {
        "kind": "sing-box-gateway-ui-backup",
        "version": BACKUP_VERSION,
        "exportedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "host": socket.gethostname(),
        "paths": {
            "config": str(CONFIG_PATH),
            "manager": str(MANAGER_DIR),
            "rules": str(RULE_DIR),
            "tproxyScript": str(TPROXY_SCRIPT),
            "tproxySysctl": str(TPROXY_SYSCTL),
            "radvd": str(RADVD_CONF),
        },
        "lists": {name: read_entries(name) for name in LISTS},
        "nodes": load_nodes(),
        "groups": load_groups(),
        "snapshots": {
            "config": load_json(CONFIG_PATH, {}) if CONFIG_PATH.exists() else {},
            "base": load_json(BASE_CONFIG_PATH, {}) if BASE_CONFIG_PATH.exists() else {},
            "tproxyScript": read_text_if_exists(TPROXY_SCRIPT),
            "tproxySysctl": read_text_if_exists(TPROXY_SYSCTL),
            "radvd": read_text_if_exists(RADVD_CONF),
            "ruleFiles": {
                name: load_json(rule_path(name), empty_rule_set()) if rule_path(name).exists() else empty_rule_set()
                for name in LISTS
            },
        },
    }


def import_backup_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError("Backup must be a JSON object")
    if payload.get("kind") != "sing-box-gateway-ui-backup":
        raise ValueError("Unsupported backup file")
    version = int(payload.get("version") or 0)
    if version < 1 or version > BACKUP_VERSION:
        raise ValueError(f"Unsupported backup version: {version}")
    normalized_lists = normalize_payload_lists(payload.get("lists", {}))
    nodes = normalize_nodes(payload.get("nodes", []))
    groups = normalize_payload_groups(payload.get("groups", {}), nodes=nodes)
    check = staged_check(normalized_lists, nodes=nodes, groups=groups)
    if check["code"] != 0:
        return {
            "ok": False,
            "error": "Config check failed. Backup was not imported.",
            "check": check,
            "saved": None,
            "restart": None,
            "rollback": None,
            "tproxySync": None,
        }
    result = apply_all(normalized_lists, nodes, groups)
    restart = restart_sing_box()
    rollback = None
    if restart["code"] != 0 or service_status() != "active":
        rollback_apply(result)
        rollback_restart = restart_sing_box()
        rollback = {"restart": rollback_restart, "service": service_status()}
        return {
            "ok": False,
            "error": "Restart failed. Previous config was restored.",
            "check": check,
            "saved": result,
            "restart": restart,
            "rollback": rollback,
            "tproxySync": None,
        }
    tproxy_sync = sync_tproxy(nodes=nodes, groups=groups)
    return {
        "ok": True,
        "error": "",
        "check": check,
        "saved": result,
        "restart": restart,
        "rollback": rollback,
        "tproxySync": tproxy_sync,
    }


def rollback_apply(result):
    backups = (result or {}).get("backups", {})
    restore_file(CONFIG_PATH, backups.get("config"))
    restore_file(NODES_PATH, backups.get("nodes"))
    restore_file(GROUPS_PATH, backups.get("groups"))
    for item in ((result or {}).get("rules") or {}).values():
        if isinstance(item, dict):
            name = item.get("name")
            backup = item.get("backup")
            if name in LISTS and backup:
                restore_file(rule_path(name), backup)


def load_state():
    ensure_manager_data()
    lists = {}
    for name in LISTS:
        lists[name] = read_entries(name)
    return {
        "lists": lists,
        "nodes": load_nodes(),
        "groups": load_groups(),
        "meta": {
            "ruleDir": str(RULE_DIR),
            "managerDir": str(MANAGER_DIR),
            "configPath": str(CONFIG_PATH),
            "service": service_status(),
            "memory": sing_box_memory(),
            # 只展示当前运行二进制版本，便于现场判断配置兼容性；不代表会自动升级 sing-box。
            "singBoxVersion": sing_box_version(),
            "dnsChoices": LOCAL_DNS_CHOICES,
        },
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "SingBoxRuleUI/1.0"

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))

    def authorized(self):
        token = get_token()
        auth = self.headers.get("Authorization", "")
        return auth == f"Bearer {token}"

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message, status=400):
        self.send_json({"error": message}, status)

    def send_download(self, filename, payload):
        body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def stream_clash_api(self, path, content_type="application/json; charset=utf-8", timeout=60):
        api_url, api_secret = clash_api_settings()
        headers = {}
        if api_secret:
            headers["Authorization"] = f"Bearer {api_secret}"
        # 9091 已经完成 Rule UI token 鉴权；这里仅用后端读取到的 Clash secret 访问白名单接口，不能把 secret 暴露给浏览器。
        request = Request(f"{api_url}{path}", headers=headers)
        try:
            with urlopen(request, timeout=timeout) as response:
                self.send_response(response.status)
                self.send_header("Content-Type", content_type)
                self.end_headers()
                while True:
                    chunk = response.read(4096)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
        except HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            self.send_error_json(raw or str(exc), exc.code)
        except (BrokenPipeError, ConnectionResetError):
            return
        except (URLError, TimeoutError, OSError) as exc:
            self.send_error_json(str(exc), 502)

    def read_json_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length > 2_000_000:
            raise ValueError("Request body is too large")
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw or "{}")

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/state":
            if not self.authorized():
                self.send_error_json("Unauthorized", 401)
                return
            self.send_json(load_state())
            return
        if parsed.path == "/api/proxy":
            if not self.authorized():
                self.send_error_json("Unauthorized", 401)
                return
            self.send_json({"proxy": get_proxy_state(), "delays": get_node_delays(test=False)})
            return
        if parsed.path == "/api/maintenance":
            if not self.authorized():
                self.send_error_json("Unauthorized", 401)
                return
            self.send_json({"maintenance": maintenance_status(), "state": load_state()})
            return
        if parsed.path == "/api/backup/export":
            if not self.authorized():
                self.send_error_json("Unauthorized", 401)
                return
            filename = f"sing-box-gateway-ui-backup-{socket.gethostname()}-{now_stamp()}.json"
            self.send_download(filename, export_backup_payload())
            return
        if parsed.path == "/api/delays":
            if not self.authorized():
                self.send_error_json("Unauthorized", 401)
                return
            query = dict(item.split("=", 1) for item in parsed.query.split("&") if "=" in item)
            self.send_json({"delays": get_node_delays(test=query.get("test") == "1")})
            return
        if parsed.path == "/api/dns-delays":
            if not self.authorized():
                self.send_error_json("Unauthorized", 401)
                return
            self.send_json({"dnsDelays": get_dns_delays()})
            return
        if parsed.path.startswith("/api/runtime/"):
            if not self.authorized():
                self.send_error_json("Unauthorized", 401)
                return
            kind = parsed.path.rsplit("/", 1)[-1]
            if kind == "logs":
                try:
                    query = parse_qs(parsed.query)
                    level = normalize_log_level((query.get("level") or ["info"])[0])
                except ValueError as exc:
                    self.send_error_json(str(exc), 400)
                    return
                self.stream_clash_api(f"/logs?{urlencode({'level': level})}", content_type="text/plain; charset=utf-8", timeout=300)
                return
            if kind in {"configs", "connections", "rules", "traffic"}:
                self.send_json({"runtime": clash_runtime_snapshot(kind), "logLevel": current_log_level()})
                return
            self.send_error_json("Not found", 404)
            return
        if parsed.path == "/api/token-hint":
            self.send_json({"message": "Use Authorization: Bearer <token> from the server token file."})
            return
        self.serve_static(parsed.path)

    def do_HEAD(self):
        parsed = urlparse(self.path)
        path = "/index.html" if parsed.path in ("", "/") else parsed.path
        safe = Path(unquote(path).lstrip("/"))
        target = (STATIC_DIR / safe).resolve()
        if not str(target).startswith(str(STATIC_DIR.resolve())) or not target.exists() or target.is_dir():
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Length", str(target.stat().st_size))
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if not self.authorized():
            self.send_error_json("Unauthorized", 401)
            return
        try:
            payload = self.read_json_body()
            if parsed.path == "/api/save":
                normalized_lists = normalize_payload_lists(payload.get("lists", {}))
                nodes = normalize_nodes(payload.get("nodes", load_nodes()))
                groups = normalize_payload_groups(payload.get("groups", load_groups()), nodes=nodes)
                check = staged_check(normalized_lists, nodes=nodes, groups=groups)
                if check["code"] != 0:
                    self.send_json(
                        {
                            "error": "Config check failed. Changes were not saved and sing-box was not restarted.",
                            "saved": None,
                            "check": check,
                            "restart": None,
                            "state": load_state(),
                        },
                        422,
                    )
                    return
                result = apply_all(normalized_lists, nodes, groups)
                restart = restart_sing_box()
                rollback = None
                if restart["code"] != 0 or service_status() != "active":
                    rollback_apply(result)
                    rollback_restart = restart_sing_box()
                    rollback = {"restart": rollback_restart, "service": service_status()}
                    self.send_json(
                        {
                            "error": "Restart failed. Previous config was restored.",
                            "saved": result,
                            "check": check,
                            "restart": restart,
                            "rollback": rollback,
                            "state": load_state(),
                        },
                        500,
                    )
                    return
                tproxy_sync = sync_tproxy(nodes=nodes, groups=groups)
                self.send_json(
                    {
                        "saved": result,
                        "check": check,
                        "restart": restart,
                        "rollback": rollback,
                        "tproxySync": tproxy_sync,
                        "maintenance": maintenance_status(),
                        "state": load_state(),
                    }
                )
                return
            if parsed.path == "/api/check":
                self.send_json({"check": check_config(), "state": load_state()})
                return
            if parsed.path == "/api/restart":
                check = check_config()
                if check["code"] != 0:
                    self.send_json(
                        {
                            "error": "Config check failed. sing-box was not restarted.",
                            "check": check,
                            "restart": None,
                            "state": load_state(),
                        },
                        422,
                    )
                    return
                self.send_json({"check": check, "restart": restart_sing_box(), "state": load_state()})
                return
            if parsed.path == "/api/rules/update":
                result = update_rule_sets()
                status = 200 if result["code"] == 0 else 500
                self.send_json({"update": result, "maintenance": maintenance_status(), "state": load_state()}, status)
                return
            if parsed.path == "/api/tproxy/sync":
                result = sync_tproxy()
                status = 200 if result["code"] == 0 else 500
                self.send_json({"sync": result, "maintenance": maintenance_status(), "state": load_state()}, status)
                return
            if parsed.path == "/api/tproxy/restart":
                result = restart_tproxy()
                status = 200 if result["code"] == 0 else 500
                self.send_json({"restart": result, "maintenance": maintenance_status(), "state": load_state()}, status)
                return
            if parsed.path == "/api/ui/restart":
                restart_rule_ui_later()
                self.send_json({"scheduled": True, "service": RULE_UI_SERVICE})
                return
            if parsed.path == "/api/backup/import":
                result = import_backup_payload(payload)
                status = 200 if result["ok"] else 422 if result.get("check", {}).get("code") != 0 else 500
                self.send_json(
                    {
                        **result,
                        "maintenance": maintenance_status(),
                        "state": load_state(),
                    },
                    status,
                )
                return
            if parsed.path == "/api/proxy/select":
                tag = str(payload.get("tag", "")).strip()
                if not tag:
                    raise ValueError("tag is required")
                self.send_json({"proxy": set_proxy_now(tag), "state": load_state()})
                return
            if parsed.path == "/api/proxy/default":
                tag = str(payload.get("tag", "")).strip()
                if not tag:
                    raise ValueError("tag is required")
                result = apply_proxy_default(tag)
                status = 200 if result["ok"] else 422 if result.get("check", {}).get("code") != 0 else 500
                self.send_json(result, status)
                return
            if parsed.path == "/api/runtime/log-level":
                level = str(payload.get("level", "")).strip()
                if not level:
                    raise ValueError("level is required")
                result = set_log_level(level)
                status = 200 if result["ok"] else 422 if result.get("check", {}).get("code") != 0 else 500
                self.send_json(result, status)
                return
            self.send_error_json("Not found", 404)
        except Exception as exc:
            self.send_error_json(str(exc), 400)

    def serve_static(self, path):
        if path in ("", "/"):
            path = "/index.html"
        safe = Path(unquote(path).lstrip("/"))
        target = (STATIC_DIR / safe).resolve()
        if not str(target).startswith(str(STATIC_DIR.resolve())) or not target.exists() or target.is_dir():
            self.send_response(404)
            self.end_headers()
            return
        content_type = "text/plain"
        if target.suffix == ".html":
            content_type = "text/html; charset=utf-8"
        elif target.suffix == ".css":
            content_type = "text/css; charset=utf-8"
        elif target.suffix == ".js":
            content_type = "application/javascript; charset=utf-8"
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if target.suffix == ".html":
            self.send_header("Cache-Control", "no-store")
        elif target.suffix in {".js", ".css"}:
            self.send_header("Cache-Control", "no-cache, must-revalidate")
        self.end_headers()
        self.wfile.write(body)


def main():
    token = get_token()
    host = os.environ.get("RULE_UI_HOST", "0.0.0.0")
    port = int(os.environ.get("RULE_UI_PORT", "9091"))
    print(f"Sing-box Rule UI listening on http://{host}:{port}")
    print(f"Token file: {TOKEN_FILE}")
    print(f"Token: {token}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
