# sing-box-gateway-ui

`sing-box-gateway-ui` 是一个面向旁路网关场景的一键安装项目，集成 `sing-box`、TProxy、分流规则自动更新、规则管理 UI 和 9090 Clash API 面板。

设计目标是：**高效、简洁、sing-box 不死**。所有配置保存、规则更新和 TProxy 同步都应先检查、可回滚，避免因为错误输入导致正在运行的 `sing-box` 无法启动。

## 截图

规则管理 UI：

![Rule UI login](docs/images/rule-ui-login.jpg)

节点管理：

![Rule UI nodes](docs/images/rule-ui-nodes.png)

9090 zashboard 面板：

![zashboard](docs/images/zashboard.jpg)

## 功能

- 一键安装 `sing-box` 二进制、systemd 服务、TProxy 和 Web UI
- 默认使用仓库内置并验证过的 `sing-box 1.13.13`，同时包含 `amd64` 和 `arm64`
- 规则 UI 管理白名单、黑名单、灰名单、DDNS 和代理节点
- 保存前执行 `sing-box check`，失败不覆盖正式配置
- 重启失败自动回滚上一份可用配置
- DDNS 可选择本地 DNS 或经代理节点访问的远程 DNS
- TProxy 自动检测默认网卡、本机网段和 IPv6 前缀
- 节点服务器 IP 自动加入 TProxy bypass，避免代理链路被透明代理套住
- FakeIP 网段不绕过 TProxy，继续交给 `sing-box` 分流
- LAN 侧 TCP/UDP 53 会被重定向到 sing-box DNS，降低 IPv4/IPv6 明文 DNS 泄漏
- 分流规则定时更新，下载失败保留旧文件
- 维护页展示规则更新、TProxy、服务状态和节点服务器解析结果
- 内置 9090 Clash API 和 zashboard 静态面板
- `sing-box-gateway-info` 一键查看访问地址和密钥

## 透明网关 sysctl

下面是一套可参考的 sing-box 透明网关 sysctl 参数。核心目标是开启 IPv4/IPv6 转发，关闭会影响 TProxy/策略路由的反向路径过滤，并在开启 IPv6 forwarding 后继续接受上游路由器的 RA 默认路由。不同网络环境可以按需手动调整。

默认参数如下：

```conf
net.ipv4.ip_forward=1
net.ipv4.conf.all.rp_filter=0
net.ipv4.conf.default.rp_filter=0
net.ipv4.conf.eth0.rp_filter=0
net.ipv4.conf.lo.rp_filter=0

net.ipv6.conf.all.forwarding=1
net.ipv6.conf.default.forwarding=1
net.ipv6.conf.eth0.forwarding=1
net.ipv6.conf.all.accept_ra=2
net.ipv6.conf.default.accept_ra=2
net.ipv6.conf.eth0.accept_ra=2
net.ipv6.conf.all.accept_ra_defrtr=1
net.ipv6.conf.default.accept_ra_defrtr=1
net.ipv6.conf.eth0.accept_ra_defrtr=1
net.ipv6.conf.all.autoconf=1
net.ipv6.conf.default.autoconf=1
net.ipv6.conf.eth0.autoconf=1
net.ipv6.conf.all.disable_ipv6=0
net.ipv6.conf.default.disable_ipv6=0
net.ipv6.conf.eth0.disable_ipv6=0
```

其中 `eth0` 需要替换成实际默认网卡名。

## 支持系统

当前安装器面向 apt 系 Linux：

- Debian 12/13
- Ubuntu 22.04/24.04/25.04

需要 root 权限。

## 一键安装

推荐使用反代入口，适合新机器还没有代理环境、GitHub DNS 可能被污染的情况：

```bash
curl -fsSL https://scg.jgaga.tk/https://raw.githubusercontent.com/hanigege/sing-box-gateway-ui/main/scripts/quick-install.sh | sudo bash
```

如果当前机器直连 GitHub 稳定，也可以使用官方入口：

```bash
curl -fsSL https://github.com/hanigege/sing-box-gateway-ui/raw/refs/heads/main/scripts/quick-install.sh | sudo bash
```

安装脚本默认使用仓库内置的 `sing-box 1.13.13`，避免上游版本变化导致配置不兼容。项目源码和 zashboard 下载会优先尝试反代地址，失败后再尝试 GitHub 官方地址。

安装器会交互式询问：

- sing-box 来源，默认 `bundled`
- CPU 架构，默认 `auto`，也可以手动选 `amd64` 或 `arm64`
- 是否使用简单模式，默认 yes
- 旁路网关的 LAN IPv4 地址

简单模式会使用默认 FakeIP 网段和两个脱敏模板节点，让 `sing-box` 与 UI 先跑起来。模板节点不能直接代理流量，进入规则 UI 后，把 `TEMPLATE-HY2` 或 `TEMPLATE-VLESS` 改成自己的真实节点即可。

如果选择高级模式，安装器还会询问：

- FakeIP IPv4/IPv6 网段
- IPv6 DNS 监听地址，不需要可留空
- 是否使用模板节点，或手动输入节点 tag、server、端口和认证参数

安装过程中会先下载必需分流规则、生成 TProxy 规则脚本，并执行 `sing-box check`。检查不通过时不会启用服务。

如需在线下载上游最新版：

```bash
SING_BOX_SOURCE=latest sudo bash scripts/install.sh
```

如需指定版本和架构：

```bash
SING_BOX_SOURCE=custom SING_BOX_VERSION=1.13.13 SING_BOX_ARCH=arm64 sudo bash scripts/install.sh
```

## 一键卸载

默认卸载会停止服务、移除 UI、systemd 单元、TProxy 运行规则和辅助脚本，但保留 `/etc/sing-box` 配置和 `/usr/local/bin/sing-box`，方便以后恢复：

```bash
curl -fsSL https://scg.jgaga.tk/https://raw.githubusercontent.com/hanigege/sing-box-gateway-ui/main/scripts/quick-install.sh | sudo bash -s uninstall
```

彻底删除配置、规则缓存和 sing-box 二进制：

```bash
curl -fsSL https://scg.jgaga.tk/https://raw.githubusercontent.com/hanigege/sing-box-gateway-ui/main/scripts/quick-install.sh | sudo bash -s purge
```

直连 GitHub 稳定时也可以使用官方入口：

```bash
curl -fsSL https://github.com/hanigege/sing-box-gateway-ui/raw/refs/heads/main/scripts/quick-install.sh | sudo bash -s purge
```

## Git 安装

适合想修改脚本或参与开发的用户：

```bash
git clone https://github.com/hanigege/sing-box-gateway-ui.git
cd sing-box-gateway-ui
sudo bash scripts/install.sh
```

本地卸载：

```bash
sudo bash scripts/install.sh uninstall
sudo bash scripts/install.sh purge
```

## 访问入口

安装完成后会输出规则 UI token 和 9090 控制面板 secret。忘记也没关系，在网关机器上运行：

```bash
sing-box-gateway-info
```

默认入口：

```text
http://<网关IP>:9091/
http://<网关IP>:9090/ui/
```

## 服务

安装后会创建：

- `sing-box.service`
- `sing-box-tproxy.service`
- `singbox-rule-ui.service`
- `update-sing-box-rules-jsdelivr.timer`

常用检查命令：

```bash
systemctl status sing-box
systemctl status sing-box-tproxy
systemctl status singbox-rule-ui
systemctl list-timers update-sing-box-rules-jsdelivr.timer
sing-box-gateway-info
```

## 安全

不要把以下内容提交到公开仓库：

- 节点密码
- UUID
- Reality public key / short id
- UI token
- 真实服务器 IP
- 私有域名

本仓库只保存安装逻辑和通用模板，不包含任何可用代理节点或私人配置。
