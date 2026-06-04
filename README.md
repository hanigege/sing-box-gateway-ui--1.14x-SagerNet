# sing-box-gateway-ui

一键部署 `sing-box` 旁路网关、TProxy、分流规则自动更新和 Web UI。

项目目标很简单：**高效、简洁、sing-box 不死**。任何 UI 保存、规则更新、TProxy 同步都应先检测或可回滚，不能因为用户填错内容导致 `sing-box` 起不来。

## 功能

- Web UI 管理白名单、黑名单、灰名单、DDNS 和节点
- 保存前执行 `sing-box check`
- 保存失败不写正式配置
- 重启失败自动回滚上一份配置
- DDNS 支持本地解析或代理解析
- TProxy 自动检测默认网卡和本机网段
- 节点服务器 IP 自动加入 TProxy bypass
- 域名节点通过 sing-box 远程 DNS 解析后加入 TProxy bypass
- FakeIP 网段不绕过 TProxy，交给 sing-box 分流
- 规则集定时更新，失败保留旧文件
- 维护页显示规则更新、TProxy、服务状态
- 9090 Clash API 和本地 zashboard 控制面板
- `sing-box-gateway-info` 一键查看两个 UI 的地址和密钥

## 支持系统

第一版面向 Debian/Ubuntu 系统：

- Debian 12/13
- Ubuntu 22.04/24.04/25.04

需要 root 权限。

## 快速安装

```bash
git clone https://github.com/hanigege/sing-box-gateway-ui.git
cd sing-box-gateway-ui
sudo bash scripts/install.sh
```

安装器会交互式询问：

- 旁路网关的 LAN IPv4 地址
- FakeIP IPv4/IPv6 网段
- IPv6 DNS 监听地址，不需要可留空
- 初始节点数量，默认 2 个
- 节点 tag、server、端口和认证参数

安装过程中会先下载必需分流规则、生成 TProxy 规则脚本，并执行 `sing-box check`。检查不通过时不会启用服务。

安装完成后会输出规则 UI token 和 9090 控制面板 secret。忘记也没关系，在网关机器上运行：

```bash
sing-box-gateway-info
```

入口：

```text
http://<你的旁路网关IP>:9091/
http://<你的旁路网关IP>:9090/ui/
```

## 安全说明

不要把以下内容提交到 GitHub：

- 节点密码
- UUID
- Reality public key / short id
- UI token
- 真实服务器 IP
- 私有域名

本仓库只放模板和安装逻辑，不放生产机私密配置。

## 服务

安装后会创建：

- `sing-box.service`
- `sing-box-tproxy.service`
- `singbox-rule-ui.service`
- `update-sing-box-rules-jsdelivr.timer`

常用命令：

```bash
systemctl status sing-box
systemctl status sing-box-tproxy
systemctl status singbox-rule-ui
systemctl list-timers update-sing-box-rules-jsdelivr.timer
```

## 项目状态

当前是 MVP 阶段。已经在一台生产旁路网关上验证核心功能，下一步需要在干净新机器上完整测试安装器。
