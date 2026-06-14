#!/usr/bin/env python3
import json
import importlib.util
import os
import subprocess
import sys
import tempfile
from importlib.machinery import SourceFileLoader
from pathlib import Path


APP_DIR = Path(os.environ.get("RULE_UI_APP_DIR", "/opt/singbox-rule-ui"))
CONFIG_PATH = Path(os.environ.get("RULE_UI_SING_BOX_CONFIG", "/etc/sing-box/config.json"))
REFRESH_CONFIG = Path(os.environ.get("SING_BOX_REFRESH_RUNTIME_CONFIG", "/usr/local/sbin/refresh-sing-box-runtime-config"))
LOCAL_REFRESH_CONFIG = Path(__file__).resolve().parent / "refresh_runtime_config.py"
SING_BOX_BIN = Path(os.environ.get("SING_BOX_BIN", "/usr/local/bin/sing-box"))
SING_BOX_SERVICE = os.environ.get("SING_BOX_SERVICE", "sing-box.service")
TPROXY_SERVICE = os.environ.get("RULE_UI_TPROXY_SERVICE", "sing-box-tproxy.service")
RULE_UI_SERVICE = os.environ.get("RULE_UI_SERVICE", "singbox-rule-ui.service")


def run(args, timeout=20):
    proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return {"code": proc.returncode, "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}


def unit_active(unit):
    result = run(["systemctl", "is-active", unit], timeout=8)
    return result["stdout"] == "active"


def restart_unit(unit, actions):
    result = run(["systemctl", "restart", unit], timeout=30)
    status = run(["systemctl", "is-active", unit], timeout=8)
    actions.append({"unit": unit, "code": result["code"], "status": status["stdout"] or status["stderr"], "stderr": result["stderr"]})
    return result["code"] == 0 and status["stdout"] == "active"


def render_expected_runtime(app):
    runtime_refresh = load_runtime_refresh_module()
    lan_ip = runtime_refresh.default_lan_ip()
    ipv6_listen = runtime_refresh.preferred_ipv6_listener(lan_ip)
    config = app.render_config(nodes=app.load_nodes(), groups=app.load_groups(), rule_dir=app.RULE_DIR)
    # 这里直接加载 refresh-sing-box-runtime-config 的修正规则，避免 monitor 判断和实际修复路径长期分叉。
    runtime_refresh.apply_runtime_listeners(config, lan_ip, ipv6_listen)
    return lan_ip, ipv6_listen, json.dumps(config, indent=2, ensure_ascii=False) + "\n"


def load_runtime_refresh_module():
    module_path = REFRESH_CONFIG if REFRESH_CONFIG.exists() else LOCAL_REFRESH_CONFIG
    loader = SourceFileLoader("sing_box_runtime_refresh", str(module_path))
    spec = importlib.util.spec_from_loader("sing_box_runtime_refresh", loader)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot load runtime refresh helper: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_sing_box_config(path):
    if not SING_BOX_BIN.exists():
        return {"code": 0, "stdout": "", "stderr": "sing-box binary not installed; skipped"}
    return run([str(SING_BOX_BIN), "check", "-c", str(path)], timeout=25)


def config_is_valid(content):
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        handle.write(content)
        temp_path = Path(handle.name)
    try:
        result = validate_sing_box_config(temp_path)
        return result["code"] == 0, result
    finally:
        temp_path.unlink(missing_ok=True)


def rendered_tproxy(app):
    nodes = app.load_nodes()
    groups = app.load_groups()
    sets = app.tproxy_bypass_sets(nodes=nodes, groups=groups)
    return sets, app.render_tproxy_script(nodes=nodes, groups=groups), app.render_tproxy_sysctl(sets["interface"])


def file_text(path):
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def sync_tproxy_if_needed(app, actions):
    sets, expected_script, expected_sysctl = rendered_tproxy(app)
    script_path = app.TPROXY_SCRIPT
    sysctl_path = app.TPROXY_SYSCTL
    drifted = file_text(script_path) != expected_script or file_text(sysctl_path) != expected_sysctl
    inactive = not unit_active(TPROXY_SERVICE)
    if not drifted and not inactive:
        return True, {"interface": sets["interface"], "changed": False}

    result = app.sync_tproxy()
    actions.append(
        {
            "unit": TPROXY_SERVICE,
            "reason": "drift" if drifted else "inactive",
            "code": result.get("code"),
            "status": result.get("service"),
            "interface": sets["interface"],
            "stderr": result.get("stderr", ""),
        }
    )
    return result.get("code") == 0, {"interface": sets["interface"], "changed": True}


def refresh_config_if_needed(expected_config, actions):
    current = file_text(CONFIG_PATH)
    drifted = current != expected_config
    valid, check = config_is_valid(expected_config)
    if not valid:
        actions.append({"unit": SING_BOX_SERVICE, "reason": "config-check-failed", "code": check["code"], "stderr": check["stderr"]})
        return False, {"changed": False, "valid": False}
    if not drifted:
        return True, {"changed": False, "valid": True}

    result = run([str(REFRESH_CONFIG)], timeout=30)
    actions.append({"unit": SING_BOX_SERVICE, "reason": "config-drift", "code": result["code"], "stderr": result["stderr"]})
    return result["code"] == 0, {"changed": result["code"] == 0, "valid": True}


def ensure_services(config_changed, actions):
    ok = True
    if not unit_active(RULE_UI_SERVICE):
        ok = restart_unit(RULE_UI_SERVICE, actions) and ok
    if config_changed or not unit_active(SING_BOX_SERVICE):
        ok = restart_unit(SING_BOX_SERVICE, actions) and ok
    return ok


def main():
    sys.path.insert(0, str(APP_DIR))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import app

    actions = []
    lan_ip, ipv6_listen, expected_config = render_expected_runtime(app)
    config_ok, config_state = refresh_config_if_needed(expected_config, actions)
    tproxy_ok, tproxy_state = sync_tproxy_if_needed(app, actions)
    services_ok = ensure_services(config_state["changed"], actions)
    ok = config_ok and tproxy_ok and services_ok
    summary = {
        "ok": ok,
        "lanIPv4": lan_ip,
        "ipv6DnsListen": ipv6_listen,
        "tproxyInterface": tproxy_state.get("interface", ""),
        "configChanged": config_state["changed"],
        "tproxyChanged": tproxy_state["changed"],
        "actions": actions,
    }
    # 监控服务只在发现漂移或服务异常时修复；无漂移时不重启，避免扰动 UI 和分流运行态。
    print(json.dumps(summary, ensure_ascii=False, separators=(",", ":")))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
