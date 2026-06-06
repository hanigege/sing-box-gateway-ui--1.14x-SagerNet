const translations = {
  en: {
    title: "Sing-box",
    loading: "Loading",
    ready: "Ready",
    restart: "Restart",
    restartHint: "Use only when you need to reload sing-box without changing rules.",
    restartSingbox: "Restart sing-box",
    restartTproxy: "Restart TProxy",
    restartingTproxy: "Restarting TProxy",
    restartingSingbox: "Restarting sing-box",
    singboxRestarted: "sing-box restarted",
    tproxyRestarted: "TProxy restarted",
    tproxyRestartFailed: "TProxy restart failed. sing-box is still running.",
    save: "Save",
    saveHint: "Save runs a staged sing-box check first. If it passes, rules are saved and sing-box restarts. If it fails, nothing is changed.",
    add: "Add",
    accessToken: "Access Token",
    pasteToken: "Paste token",
    unlock: "Unlock",
    logout: "Logout",
    loggedOut: "Logged out",
    filter: "Filter",
    loaded: "Loaded",
    tokenRequired: "Token required",
    changed: "Changed",
    noChanges: "No unsaved changes",
    saving: "Saving",
    savingWithCheck: "Checking staged rules. If it passes, rules will be saved and sing-box will restart.",
    savedAndRestarted: "Check passed. Rules saved and sing-box restarted.",
    savedAlert: "Saved successfully. sing-box and TProxy are ready.",
    restarting: "Checking before restart",
    restarted: "Config check passed and sing-box restarted",
    checkFailed: "Config check failed. Nothing was restarted.",
    saveBlocked: "Config check failed. Rules were not saved and sing-box was not restarted.",
    changesBlocked: "Config check failed. Changes were not saved and sing-box was not restarted.",
    restartFailed: "Restart failed",
    noMatches: "No matching entries",
    noEntries: "No entries",
    entries: "entries",
    matchHelp: "Match examples",
    remove: "Remove",
    service: "Service",
    memory: "Memory",
    updated: "Updated",
    ruleDir: "Rule dir",
    nodes: "Nodes",
    nodesNote: "Managed outbounds",
    enabled: "Enabled",
    disabled: "Disabled",
    deleteNode: "Delete node",
    addNode: "Add node",
    updateNode: "Update node",
    cancelEdit: "Cancel",
    editCancelled: "Edit cancelled",
    allowInsecure: "Allow insecure TLS",
    defaultProxy: "Default proxy",
    activeProxy: "Active proxy",
    setDefault: "Set default",
    defaultSaved: "Saved default",
    activeNow: "Active now",
    pendingDefault: "Default changed. Save to persist and restart sing-box.",
    proxySwitchFailed: "Runtime proxy switch failed. Save can still persist the config.",
    delay: "Delay",
    delayUnknown: "Not tested",
    delayFailed: "Failed",
    refreshDelay: "Refresh delay",
    refreshMaintenance: "Refresh",
    refreshingMaintenance: "Refreshing",
    maintenanceRefreshed: "Refreshed",
    restartUi: "Restart UI",
    restartingUi: "Restarting UI",
    uiRestartScheduled: "UI restart requested. The page will reconnect shortly.",
    uiRestartReady: "UI restarted and reconnected",
    uiRestartManualRefresh: "UI restart was requested. If the page does not update, refresh the browser.",
    actionDone: "Done",
    actionFailed: "Failed",
    updateRules: "Update rule sets",
    syncTproxy: "Sync TProxy",
    exportBackup: "Export backup",
    importBackup: "Import backup",
    exportingBackup: "Exporting backup",
    importingBackup: "Importing backup",
    backupExported: "Backup exported",
    backupImported: "Backup imported and sing-box restarted",
    backupExportedAlert: "Backup exported successfully.",
    backupImportedAlert: "Backup imported successfully. sing-box and TProxy are ready.",
    backupImportFailed: "Backup import failed. Existing config is still in use.",
    updatingRules: "Updating rule sets",
    ruleUpdateRunning: "Updating now. Please wait.",
    ruleUpdateSlow: "Update is slow. Existing rule files are still in use.",
    syncingTproxy: "Syncing TProxy",
    rulesUpdated: "Rule sets updated safely",
    tproxySynced: "TProxy synced safely",
    tproxySyncFailed: "TProxy sync failed. sing-box is still running.",
    maintenance: "Maintenance",
    maintenanceNote: "Rule-set updates and TProxy status",
    backupTitle: "Backup and restore",
    backupNote: "Export or restore the UI-managed rules, nodes, and routing settings.",
    ruleUpdateTitle: "Rule-set updates",
    ruleUpdateDetails: "Update details",
    updatedRules: "Updated",
    keptRules: "Optional cache",
    skippedRules: "Skipped",
    errorDetails: "Needs attention",
    finalResult: "Final",
    updateHealthOk: "Core rule sets are current. Optional service IP lists kept their cached copies.",
    optionalCacheOk: "Optional service IP lists are unavailable upstream, so cached copies are used. No action needed.",
    updatedCount: "Updated files",
    optionalCount: "Cached optional files",
    noUpdateDetails: "No update details yet",
    tproxyTitle: "TProxy gateway",
    nextUpdate: "Next update",
    lastUpdate: "Last update",
    updateResult: "Result",
    updateScript: "Script",
    timerStatus: "Timer",
    tproxyService: "TProxy service",
    defaultInterface: "Default interface",
    currentIpv6Prefix: "Local IPv6 LAN prefixes",
    currentIpv4Prefix: "Local IPv4 LAN prefix",
    scriptIpv6Prefix: "IPv6 destinations not intercepted",
    plannedBypass4: "IPv4 destinations not intercepted",
    plannedBypass6: "IPv6 destinations not intercepted",
    fakeipRanges: "FakeIP ranges",
    nodeServerIps: "Node server addresses",
    tproxyPolicy: "LAN/private and node server IPs bypass TProxy. LAN DNS port 53 is redirected to sing-box DNS. FakeIP ranges are captured by TProxy and handled by sing-box.",
    prefixMismatch: "IPv6 bypass prefix should be regenerated for this host.",
    healthy: "OK",
    unknown: "Unknown",
    testingDelay: "Testing node delay",
    delayUpdated: "Delay updated",
    autoTitle: "Auto",
    autoNote: "Urltest selects the lowest-latency node within tolerance.",
    autoUrl: "Test URL",
    autoInterval: "Interval",
    autoTolerance: "Tolerance",
    dnsMode: "DNS mode",
    ddnsLocalDns: "Local DNS",
    ddnsRemoteDns: "Proxy DNS",
    ddnsLocalSummary: "Local DNS + direct",
    ddnsRemoteSummary: "Proxy DNS + direct",
    ddnsLocalHint: ["Lookup: use local DNS.", "Connect: keep direct routing."],
    ddnsRemoteHint: ["Lookup: use remote DNS through Proxy to avoid local DNS pollution.", "Connect: keep direct routing after the IP is resolved."],
    fakeipTitle: "FakeIP",
    fakeipNote: "Match this range with the upstream router.",
    fakeipV4: "IPv4 range",
    fakeipV6: "IPv6 range",
    editingNode: "Editing node",
    nodeSelected: "Node loaded into the form",
    nodeDeleteBlocked: "This node is still referenced by the active default. Choose another default first.",
    duplicateNode: "Invalid or duplicate tag",
    placeholders: {
      domain: "login.example.com",
      domain_suffix: "example.com",
      domain_keyword: "google",
      domain_regex: "^api[0-9]+\\.example\\.com$",
    },
    typeHelp: {
      domain: { use: "match one exact domain", example: "login.example.com" },
      domain_suffix: { use: "match this domain and all subdomains", example: "example.com" },
      domain_keyword: { use: "match domains containing this word", example: "google" },
      domain_regex: { use: "match domains with a pattern, such as api1 or api23", example: "^api[0-9]+\\.example\\.com$" },
    },
    listTypeHelp: {
      whitelist: "Direct: suffix is usually enough; keyword/regex are for broad or advanced direct rules.",
      blacklist: "Block: suffix blocks a site family; keyword/regex can catch ad or tracking patterns.",
      greylist: "Proxy: suffix is safest; keyword/regex can force groups of related domains through Proxy.",
      ddns: "DDNS only needs exact host or suffix. Keyword and regex are hidden to avoid accidental broad matches.",
    },
    lists: {
      whitelist: { title: "Whitelist", note: "Direct routing" },
      blacklist: { title: "Blacklist", note: "Blocked routing" },
      greylist: { title: "Greylist", note: "Forced proxy" },
      ddns: { title: "Local DDNS", note: "Local DNS and direct routing" },
      nodes: { title: "Nodes", note: "Add, delete, and enable outbounds" },
      maintenance: { title: "Maintenance", note: "Rule-set updates and TProxy status" },
    },
    types: {
      domain: "Domain",
      domain_suffix: "Suffix",
      domain_keyword: "Keyword",
      domain_regex: "Regex",
    },
  },
  zh: {
    title: "Sing-box",
    loading: "加载中",
    ready: "就绪",
    restart: "重启",
    restartHint: "仅在没有改规则、但需要重新加载 sing-box 时使用。",
    restartSingbox: "重启 sing-box",
    restartTproxy: "重启 TProxy",
    restartingTproxy: "正在重启 TProxy",
    restartingSingbox: "正在重启 sing-box",
    singboxRestarted: "sing-box 已重启",
    tproxyRestarted: "TProxy 已重启",
    tproxyRestartFailed: "TProxy 重启失败，sing-box 仍在运行。",
    save: "保存",
    saveHint: "保存会先用临时规则检测 sing-box 配置；通过才保存并重启，失败不会改正式规则。",
    add: "添加",
    accessToken: "访问令牌",
    pasteToken: "粘贴 token",
    unlock: "解锁",
    logout: "退出",
    loggedOut: "已退出",
    filter: "筛选",
    loaded: "已加载",
    tokenRequired: "需要 token",
    changed: "有未保存修改",
    noChanges: "没有未保存修改",
    saving: "正在保存",
    savingWithCheck: "正在检测临时规则；通过后才会保存并重启 sing-box",
    savedAndRestarted: "检测通过，规则已保存，sing-box 已重启",
    savedAlert: "保存成功，sing-box 和 TProxy 已就绪。",
    restarting: "重启前检测中",
    restarted: "检测通过，sing-box 已重启",
    checkFailed: "配置检测失败，没有执行重启",
    saveBlocked: "配置检测失败，规则未保存，也未重启 sing-box",
    changesBlocked: "配置检测失败，修改未保存，也未重启 sing-box",
    restartFailed: "重启失败",
    noMatches: "没有匹配条目",
    noEntries: "没有条目",
    entries: "条",
    matchHelp: "匹配示例",
    remove: "删除",
    service: "服务",
    memory: "内存",
    updated: "刷新",
    ruleDir: "规则目录",
    nodes: "节点",
    nodesNote: "受管理的出站节点",
    enabled: "启用",
    disabled: "停用",
    deleteNode: "删除节点",
    addNode: "添加节点",
    updateNode: "更新节点",
    cancelEdit: "取消编辑",
    editCancelled: "已取消编辑",
    allowInsecure: "允许不安全 TLS",
    defaultProxy: "默认代理",
    activeProxy: "当前生效",
    setDefault: "设为默认",
    defaultSaved: "已保存默认",
    activeNow: "当前生效",
    pendingDefault: "默认代理已切换，保存后会持久化并重启 sing-box",
    proxySwitchFailed: "运行态切换失败；仍可保存配置让它持久化生效",
    delay: "延迟",
    delayUnknown: "未检测",
    delayFailed: "失败",
    refreshDelay: "刷新延迟",
    refreshMaintenance: "刷新状态",
    refreshingMaintenance: "正在刷新",
    maintenanceRefreshed: "已刷新",
    restartUi: "重启 UI",
    restartingUi: "正在重启 UI",
    uiRestartScheduled: "UI 正在重启，页面稍后会自动恢复。",
    uiRestartReady: "UI 已重启并恢复连接",
    uiRestartManualRefresh: "UI 重启请求已发送；如果页面没有变化，可以手动刷新浏览器。",
    actionDone: "完成",
    actionFailed: "失败",
    updateRules: "立即更新分流规则",
    syncTproxy: "同步 TProxy",
    exportBackup: "导出备份",
    importBackup: "导入备份",
    exportingBackup: "正在导出备份",
    importingBackup: "正在导入备份",
    backupExported: "备份已导出",
    backupImported: "备份已导入，sing-box 已重启",
    backupExportedAlert: "备份导出成功。",
    backupImportedAlert: "备份导入成功，sing-box 和 TProxy 已就绪。",
    backupImportFailed: "备份导入失败，当前配置仍在使用。",
    updatingRules: "正在更新分流规则",
    ruleUpdateRunning: "正在更新，请稍候。",
    ruleUpdateSlow: "更新较慢，旧规则仍在使用，不影响 sing-box。",
    syncingTproxy: "正在同步 TProxy",
    rulesUpdated: "分流规则已安全更新",
    tproxySynced: "TProxy 已安全同步",
    tproxySyncFailed: "TProxy 同步失败，sing-box 仍在运行。",
    maintenance: "维护",
    maintenanceNote: "规则集更新与 TProxy 状态",
    backupTitle: "备份与恢复",
    backupNote: "导出或恢复 UI 管理的规则、节点和分流设置。",
    ruleUpdateTitle: "分流规则更新",
    ruleUpdateDetails: "更新明细",
    updatedRules: "已更新",
    keptRules: "可选规则缓存",
    skippedRules: "已跳过",
    errorDetails: "需要处理",
    finalResult: "最终结果",
    updateHealthOk: "核心分流规则已更新；可选服务 IP 列表沿用缓存，不影响正常分流。",
    optionalCacheOk: "这些可选服务 IP 上游暂时没有文件，已自动沿用旧缓存，无需处理。",
    updatedCount: "更新文件数",
    optionalCount: "沿用缓存数",
    noUpdateDetails: "暂无更新明细",
    tproxyTitle: "TProxy 旁路网关",
    nextUpdate: "下次自动更新",
    lastUpdate: "上次触发",
    updateResult: "结果",
    updateScript: "脚本",
    timerStatus: "定时器",
    tproxyService: "TProxy 服务",
    defaultInterface: "默认网卡",
    currentIpv6Prefix: "本机 IPv6 局域网段",
    currentIpv4Prefix: "本机 IPv4 局域网段",
    scriptIpv6Prefix: "不接管的 IPv6 目标",
    plannedBypass4: "不接管的 IPv4 目标",
    plannedBypass6: "不接管的 IPv6 目标",
    fakeipRanges: "FakeIP 网段",
    nodeServerIps: "节点服务器地址",
    tproxyPolicy: "内网/本机网段和节点服务器 IP 会绕过 TProxy；LAN 进来的 53 端口 DNS 会被劫回 sing-box；FakeIP 网段不会绕过，会交给 sing-box 分流。",
    prefixMismatch: "IPv6 绕过前缀和当前机器不一致，打包安装时应自动生成。",
    healthy: "正常",
    unknown: "未知",
    testingDelay: "正在检测节点延迟",
    delayUpdated: "延迟已更新",
    autoTitle: "Auto 自动选择",
    autoNote: "按测速链接和容差从可用节点里自动选择",
    autoUrl: "测速链接",
    autoInterval: "检测间隔",
    autoTolerance: "容差",
    dnsMode: "解析方式",
    ddnsLocalDns: "本地解析",
    ddnsRemoteDns: "代理解析",
    ddnsLocalSummary: "本地解析 + 直连",
    ddnsRemoteSummary: "代理解析 + 直连",
    ddnsLocalHint: ["查 IP：使用本地 DNS。", "连接：拿到 IP 后仍保持直连。"],
    ddnsRemoteHint: ["查 IP：使用国外 DNS，并经代理节点发起解析，绕开本地 DNS 污染。", "连接：拿到 IP 后仍按 DDNS 规则直连，不走代理。"],
    fakeipTitle: "FakeIP",
    fakeipNote: "需要和前端软路由里的 FakeIP 网段保持一致",
    fakeipV4: "IPv4 网段",
    fakeipV6: "IPv6 网段",
    editingNode: "正在编辑节点",
    nodeSelected: "已把节点参数填入上方表单",
    nodeDeleteBlocked: "这个节点仍是当前默认选择，请先切换默认节点。",
    duplicateNode: "节点名称无效或重复",
    placeholders: {
      domain: "home.example.com",
      domain_suffix: "example.com",
      domain_keyword: "google",
      domain_regex: "^api[0-9]+\\.example\\.com$",
    },
    typeHelp: {
      domain: { use: "只匹配这个完整域名", example: "home.example.com" },
      domain_suffix: { use: "匹配该域名及其所有子域名", example: "example.com" },
      domain_keyword: { use: "域名里包含这个关键词就匹配", example: "google" },
      domain_regex: { use: "按一条表达式匹配有规律的域名，如 api1、api23", example: "^api[0-9]+\\.example\\.com$" },
    },
    listTypeHelp: {
      whitelist: "白名单用于强制直连；通常用域名后缀，关键词/正则适合更宽泛或高级规则。",
      blacklist: "黑名单用于强制阻断；后缀适合整站，关键词/正则适合广告、跟踪等模式。",
      greylist: "灰名单用于强制代理；后缀最稳，关键词/正则适合把一组相关域名走代理。",
      ddns: "DDNS 只保留完整域名和域名后缀；关键词/正则容易误伤，已隐藏。",
    },
    lists: {
      whitelist: { title: "白名单", note: "强制直连" },
      blacklist: { title: "黑名单", note: "强制阻断" },
      greylist: { title: "灰名单", note: "强制代理" },
      ddns: { title: "本地 DDNS", note: "本地 DNS + 直连" },
      nodes: { title: "节点", note: "添加、删除、启停出站节点" },
      maintenance: { title: "维护", note: "规则集更新与 TProxy 状态" },
    },
    types: {
      domain: "完整域名",
      domain_suffix: "域名后缀",
      domain_keyword: "关键词",
      domain_regex: "正则",
    },
  },
};

let token = localStorage.getItem("ruleUiToken") || "";
let lang = localStorage.getItem("ruleUiLang") || ((navigator.language || "").toLowerCase().startsWith("zh") ? "zh" : "en");
let state = { lists: { whitelist: [], blacklist: [], greylist: [], ddns: [] }, nodes: [], groups: {}, meta: {} };
let maintenance = {};
let runtimeProxy = { now: null, available: false };
let delays = {};
let active = "nodes";
let dirty = false;
let busy = false;
let editingNodeTag = null;
let editingNodeSnapshot = "";
let nodeEditChanged = false;
let metaUpdatedAt = null;
const actionButtonTimers = {};

const $ = (id) => document.getElementById(id);
const t = (key) => translations[lang][key] || translations.en[key] || key;
const allEntryTypes = ["domain_suffix", "domain", "domain_keyword", "domain_regex"];
const listEntryTypes = {
  whitelist: allEntryTypes,
  blacklist: allEntryTypes,
  greylist: allEntryTypes,
  ddns: ["domain_suffix", "domain"],
};

function setStatus(text, tone = "") {
  const node = $("status");
  node.textContent = text;
  node.className = `status ${tone}`;
}

function setBusy(value) {
  busy = value;
  updateButtons();
}

function setDirty(value) {
  dirty = value;
  updateButtons();
}

function updateButtons() {
  $("logoutBtn").disabled = busy;
  $("refreshMaintenanceBtn").disabled = busy;
  $("restartSingboxBtn").disabled = busy;
  $("restartTproxyBtn").disabled = busy;
  $("restartUiBtn").disabled = busy;
  $("syncTproxyBtn").disabled = busy;
  $("exportBackupBtn").disabled = busy;
  $("importBackupBtn").disabled = busy;
  $("updateRulesBtn").disabled = busy;
  $("saveBtn").disabled = busy || !dirty;
  $("nodeSubmit").disabled = busy || Boolean(editingNodeTag && !nodeEditChanged);
}

function setActionButton(id, textKey, tone = "") {
  const button = $(id);
  clearTimeout(actionButtonTimers[id]);
  button.textContent = t(textKey);
  button.classList.remove("working", "done", "failed");
  if (tone) button.classList.add(tone);
}

function pulseActionButton(id, textKey) {
  setActionButton(id, textKey, "working");
}

function finishActionButton(id, textKey, tone = "done", resetKey = null) {
  setActionButton(id, textKey, tone);
  actionButtonTimers[id] = setTimeout(() => {
    if (resetKey) setActionButton(id, resetKey);
    else applyLanguage();
  }, 1600);
}

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (options.body && !headers["Content-Type"]) headers["Content-Type"] = "application/json";
  const response = await fetch(path, { ...options, headers });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.check?.stderr || body.error || `HTTP ${response.status}`);
  return body;
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function waitForUiReconnect(timeoutMs = 12000) {
  const deadline = Date.now() + timeoutMs;
  await sleep(900);
  while (Date.now() < deadline) {
    try {
      return await api("/api/maintenance");
    } catch (error) {
      await sleep(700);
    }
  }
  return null;
}

function showLogin() {
  $("login").classList.remove("hidden");
  $("app").classList.add("hidden");
  $("tokenInput").value = token;
  $("tokenInput").focus();
}

function showApp() {
  $("login").classList.add("hidden");
  $("app").classList.remove("hidden");
}

function logout() {
  token = "";
  localStorage.removeItem("ruleUiToken");
  state = { lists: { whitelist: [], blacklist: [], greylist: [], ddns: [] }, nodes: [], groups: {}, meta: {} };
  maintenance = {};
  runtimeProxy = { now: null, available: false };
  delays = {};
  metaUpdatedAt = null;
  setDirty(false);
  $("tokenInput").value = "";
  showLogin();
  renderMeta();
  setStatus(t("loggedOut"), "ok");
}

async function load() {
  try {
    state = await api("/api/state");
    metaUpdatedAt = new Date();
    await loadProxyInfo(false);
    setDirty(false);
    showApp();
    render();
    setStatus(t("loaded"), "ok");
  } catch (error) {
    showLogin();
    setStatus(error.message === "Unauthorized" ? t("tokenRequired") : error.message, "bad");
  }
}

async function refreshMeta() {
  if (!token || $("app").classList.contains("hidden")) return;
  try {
    const latest = await api("/api/state");
    state.meta = latest.meta || state.meta;
    metaUpdatedAt = new Date();
    renderMeta();
  } catch (error) {
    // A missed telemetry refresh should never interrupt rule or node editing.
  }
}

async function loadProxyInfo(testDelay = false) {
  try {
    const result = await api(testDelay ? "/api/delays?test=1" : "/api/proxy");
    if (result.proxy) {
      runtimeProxy = {
        now: result.proxy.ok ? result.proxy.data?.now || null : null,
        available: Boolean(result.proxy.ok),
        error: result.proxy.ok ? "" : result.proxy.error,
      };
    }
    const delayPayload = result.delays?.delays || {};
    delays = { ...delays, ...delayPayload };
    return result;
  } catch (error) {
    runtimeProxy = { now: null, available: false, error: error.message };
    return null;
  }
}

function applyLanguage() {
  document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
  document.title = t("title");
  $("brandLink").textContent = t("title");
  $("langSelect").value = lang;
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
    node.placeholder = t(node.dataset.i18nPlaceholder);
  });
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.textContent = translations[lang].lists[tab.dataset.list].title;
  });
  $("saveBtn").title = t("saveHint");
  $("logoutBtn").textContent = t("logout");
  $("restartSingboxBtn").textContent = t("restartSingbox");
  $("restartSingboxBtn").title = t("restartHint");
  $("restartTproxyBtn").textContent = t("restartTproxy");
  $("refreshDelayBtn").textContent = t("refreshDelay");
  $("refreshMaintenanceBtn").textContent = t("refreshMaintenance");
  $("restartUiBtn").textContent = t("restartUi");
  $("syncTproxyBtn").textContent = t("syncTproxy");
  $("updateRulesBtn").textContent = t("updateRules");
  $("nodeSubmit").textContent = editingNodeTag ? t("updateNode") : t("addNode");
  $("nodeCancel").textContent = t("cancelEdit");
}

function goNodes() {
  if ($("app").classList.contains("hidden")) return;
  active = "nodes";
  $("searchInput").value = "";
  setStatus(t("ready"));
  render();
}

function renderMeta() {
  const memory = state.meta?.memory?.rss || "unknown";
  const bytes = state.meta?.memory?.rssBytes || 0;
  let memoryTone = "good";
  if (bytes > 512 * 1024 * 1024) memoryTone = "bad";
  else if (bytes > 256 * 1024 * 1024) memoryTone = "warn";
  $("meta").innerHTML = "";
  const serviceStatus = state.meta.service || "unknown";
  const service = document.createElement("span");
  service.className = `meta-pill service-pill ${serviceStatus === "active" ? "good" : "bad"}`;
  const servicePulse = document.createElement("span");
  servicePulse.className = "memory-pulse";
  const serviceText = document.createElement("span");
  serviceText.textContent = `${t("service")}: ${serviceStatus}`;
  service.append(servicePulse, serviceText);
  const memoryPill = document.createElement("span");
  memoryPill.className = `meta-pill memory-pill ${memoryTone}`;
  const pulse = document.createElement("span");
  pulse.className = "memory-pulse";
  const memoryText = document.createElement("span");
  memoryText.textContent = `${t("memory")}: ${memory}`;
  memoryPill.append(pulse, memoryText);
  const ruleDir = document.createElement("span");
  ruleDir.textContent = `${t("ruleDir")}: ${state.meta.ruleDir || ""}`;
  $("meta").append(service, memoryPill, ruleDir);
  if (metaUpdatedAt) {
    const updated = document.createElement("span");
    updated.className = "meta-updated";
    updated.textContent = `${t("updated")}: ${metaUpdatedAt.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    })}`;
    $("meta").append(updated);
  }
}

function render() {
  applyLanguage();
  renderMeta();
  renderTypeOptions();
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.list === active);
  });
  $("ruleEditor").classList.toggle("hidden", active === "nodes" || active === "maintenance");
  $("nodeEditor").classList.toggle("hidden", active !== "nodes");
  $("maintenanceEditor").classList.toggle("hidden", active !== "maintenance");
  if (active === "maintenance") {
    renderMaintenance();
    updateButtons();
    return;
  }
  if (active === "nodes") {
    renderNodes();
    updateButtons();
    return;
  }
  const items = state.lists[active] || [];
  const query = $("searchInput").value.trim().toLowerCase();
  const filtered = query
    ? items.filter((item) => `${item.type}:${item.value}`.toLowerCase().includes(query))
    : items;
  const listInfo = translations[lang].lists[active];
  const note = active === "ddns" ? t(ddnsDnsMode() === "remote" ? "ddnsRemoteSummary" : "ddnsLocalSummary") : listInfo.note;
  $("listTitle").textContent = listInfo.title;
  $("listSummary").textContent = `${items.length} ${t("entries")} · ${note}`;

  const rows = $("rows");
  rows.innerHTML = "";
  rows.appendChild(renderMatchHelp());
  if (active === "ddns") rows.appendChild(renderDdnsControls());
  if (!filtered.length) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = query ? t("noMatches") : t("noEntries");
    rows.appendChild(empty);
    return;
  }
  for (const item of filtered) {
    const row = document.createElement("div");
    row.className = "rule-row";
    const badge = document.createElement("span");
    badge.className = `badge ${item.type}`;
    badge.textContent = translations[lang].types[item.type] || item.type;
    const value = document.createElement("code");
    value.textContent = item.value;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "icon-btn";
    remove.title = t("remove");
    remove.textContent = "×";
    remove.addEventListener("click", () => removeEntry(item));
    row.append(badge, value, remove);
    rows.appendChild(row);
  }
  updateButtons();
}

function formatMaintenanceValue(value) {
  if (Array.isArray(value)) return value.length ? value.join(", ") : t("unknown");
  return value || t("unknown");
}

function statusTone(value) {
  return value === "active" || value === "success" || value === true ? "good" : "warn";
}

function renderMaintenanceItem(label, value, tone = "") {
  const row = document.createElement("div");
  row.className = `maintenance-item ${tone}`;
  const name = document.createElement("span");
  name.textContent = label;
  const detail = document.createElement("strong");
  detail.textContent = formatMaintenanceValue(value);
  row.append(name, detail);
  return row;
}

function formatNodeServers(items) {
  if (!Array.isArray(items) || !items.length) return [];
  return items.map((item) => {
    const tag = item.tag ? `${item.tag}: ` : "";
    if (item.address) {
      return item.server === item.address ? `${tag}${item.address}` : `${tag}${item.server} -> ${item.address}`;
    }
    return `${tag}${item.server} -> ${item.error || t("unknown")}`;
  });
}

function renderMaintenanceCard(titleText, items, note = "") {
  const card = document.createElement("section");
  card.className = "maintenance-card";
  const title = document.createElement("h3");
  title.textContent = titleText;
  card.appendChild(title);
  for (const item of items) {
    card.appendChild(renderMaintenanceItem(item[0], item[1], item[2] || ""));
  }
  if (note) {
    const warning = document.createElement("p");
    warning.className = "maintenance-note";
    warning.textContent = note;
    card.appendChild(warning);
  }
  return card;
}

function compactRuleMessages(items) {
  if (!Array.isArray(items) || !items.length) return t("unknown");
  return items
    .map((item) => String(item).replace(/^downloaded\s+/, "").replace(/^installed\s+/, "").replace(/\s+via\s+https?:\/\/\S+$/, ""))
    .join(", ");
}

function ruleNames(items) {
  if (!Array.isArray(items) || !items.length) return "";
  return items
    .map((item) => {
      const match = String(item).match(/(?:for|downloaded|installed)\s+([a-z0-9@!_./-]+\.srs)/i);
      return match ? match[1] : "";
    })
    .filter(Boolean)
    .filter((item, index, arr) => arr.indexOf(item) === index)
    .join(", ");
}

function renderMaintenance() {
  const info = maintenance || {};
  const rule = info.ruleUpdate || {};
  const tproxy = info.tproxy || {};
  $("maintenanceTitle").textContent = t("maintenance");
  $("maintenanceSummary").textContent = t("maintenanceNote");
  const rows = $("maintenanceRows");
  rows.innerHTML = "";
  rows.appendChild(renderMaintenanceCard(t("ruleUpdateTitle"), [
    [t("timerStatus"), rule.timerActive, statusTone(rule.timerActive)],
    [t("nextUpdate"), rule.next],
    [t("lastUpdate"), rule.last],
    [t("updateResult"), rule.result || rule.serviceState, statusTone(rule.result || rule.serviceState)],
    [t("updateScript"), rule.scriptExists ? rule.script : t("unknown"), rule.scriptExists ? "good" : "bad"],
  ]));
  const summary = rule.summary || {};
  const hasDetails = Boolean((summary.updated || []).length || (summary.kept || []).length || (summary.skipped || []).length || (summary.errors || []).length || summary.final);
  const keptCount = (summary.kept || []).length;
  const errorCount = (summary.errors || []).length;
  const finalTone = errorCount ? "bad" : summary.requiredOk ? "good" : summary.final ? "soft" : "";
  rows.appendChild(renderMaintenanceCard(t("ruleUpdateDetails"), hasDetails ? [
    [t("finalResult"), summary.final || t("unknown"), finalTone],
    [t("updatedCount"), String((summary.updated || []).length), "good"],
    [t("optionalCount"), keptCount ? `${keptCount} · ${ruleNames(summary.kept)}` : "0", keptCount ? "soft" : "good"],
    [t("keptRules"), keptCount ? t("optionalCacheOk") : "0", keptCount ? "soft" : "good"],
    [t("errorDetails"), errorCount ? compactRuleMessages(summary.errors) : "0", errorCount ? "bad" : "good"],
  ] : [
    [t("ruleUpdateDetails"), t("noUpdateDetails")],
  ]));
  rows.appendChild(renderMaintenanceCard(t("tproxyTitle"), [
    [t("tproxyService"), tproxy.serviceActive, statusTone(tproxy.serviceActive)],
    [t("defaultInterface"), tproxy.defaultInterface],
    [t("currentIpv4Prefix"), tproxy.currentIpv4Prefixes],
    [t("currentIpv6Prefix"), tproxy.currentIpv6Prefixes],
    [t("scriptIpv6Prefix"), tproxy.scriptIpv6Prefixes, tproxy.ipv6PrefixMatches ? "good" : "warn"],
    [t("fakeipRanges"), [tproxy.planned?.fakeip4, tproxy.planned?.fakeip6].filter(Boolean)],
    [t("nodeServerIps"), formatNodeServers(tproxy.outboundServers) || tproxy.outboundServerIps],
    [t("plannedBypass4"), tproxy.planned?.bypass4],
    [t("plannedBypass6"), tproxy.planned?.bypass6],
  ], `${t("tproxyPolicy")}${tproxy.ipv6PrefixMatches === false ? ` ${t("prefixMismatch")}` : ""}`));
}

async function refreshMaintenance() {
  setBusy(true);
  pulseActionButton("refreshMaintenanceBtn", "refreshingMaintenance");
  setStatus(t("refreshingMaintenance"));
  try {
    const result = await api("/api/maintenance");
    maintenance = result.maintenance || {};
    if (result.state) state = result.state;
    render();
    finishActionButton("refreshMaintenanceBtn", "actionDone", "done", "refreshMaintenance");
    setStatus(t("maintenanceRefreshed"), "ok");
  } catch (error) {
    finishActionButton("refreshMaintenanceBtn", "actionFailed", "failed", "refreshMaintenance");
    setStatus(error.message, "bad");
  } finally {
    setBusy(false);
  }
}

async function updateRuleSets() {
  setBusy(true);
  pulseActionButton("updateRulesBtn", "updatingRules");
  setStatus(t("updatingRules"));
  maintenance.ruleUpdate = maintenance.ruleUpdate || {};
  maintenance.ruleUpdate.result = t("updatingRules");
  maintenance.ruleUpdate.summary = { updated: [], kept: [], skipped: [], errors: [], final: t("ruleUpdateRunning") };
  render();
  try {
    const result = await api("/api/rules/update", { method: "POST", body: "{}" });
    maintenance = result.maintenance || maintenance;
    if (result.update?.summary) {
      maintenance.ruleUpdate = maintenance.ruleUpdate || {};
      maintenance.ruleUpdate.summary = result.update.summary;
      maintenance.ruleUpdate.result = result.update.code === 0 ? "success" : result.update.code === 124 ? "slow" : "failed";
      maintenance.ruleUpdate.log = [result.update.stdout, result.update.stderr].filter(Boolean).join("\n");
    }
    if (result.state) state = result.state;
    render();
    if (result.update?.code !== 0) {
      if (result.update?.code === 124) {
        finishActionButton("updateRulesBtn", "actionDone", "done", "updateRules");
        setStatus(t("ruleUpdateSlow"), "ok");
      } else {
        finishActionButton("updateRulesBtn", "actionFailed", "failed", "updateRules");
        setStatus(result.update?.stderr || t("restartFailed"), "bad");
      }
      return;
    }
    finishActionButton("updateRulesBtn", "actionDone", "done", "updateRules");
    setStatus(t("rulesUpdated"), "ok");
  } catch (error) {
    finishActionButton("updateRulesBtn", "actionFailed", "failed", "updateRules");
    setStatus(error.message, "bad");
  } finally {
    setBusy(false);
  }
}

async function syncTproxy() {
  setBusy(true);
  pulseActionButton("syncTproxyBtn", "syncingTproxy");
  setStatus(t("syncingTproxy"));
  try {
    const result = await api("/api/tproxy/sync", { method: "POST", body: "{}" });
    maintenance = result.maintenance || maintenance;
    if (result.state) state = result.state;
    render();
    if (result.sync?.code !== 0) {
      finishActionButton("syncTproxyBtn", "actionFailed", "failed", "syncTproxy");
      setStatus(result.sync?.stderr || t("tproxySyncFailed"), "bad");
      return;
    }
    finishActionButton("syncTproxyBtn", "actionDone", "done", "syncTproxy");
    setStatus(t("tproxySynced"), "ok");
  } catch (error) {
    finishActionButton("syncTproxyBtn", "actionFailed", "failed", "syncTproxy");
    setStatus(`${t("tproxySyncFailed")} ${error.message}`, "bad");
  } finally {
    setBusy(false);
  }
}

async function exportBackup() {
  setBusy(true);
  pulseActionButton("exportBackupBtn", "exportingBackup");
  setStatus(t("exportingBackup"));
  try {
    const headers = {};
    if (token) headers.Authorization = `Bearer ${token}`;
    const response = await fetch("/api/backup/export", { headers });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.error || `HTTP ${response.status}`);
    }
    const blob = await response.blob();
    const disposition = response.headers.get("Content-Disposition") || "";
    const match = disposition.match(/filename="([^"]+)"/);
    const filename = match ? match[1] : `sing-box-gateway-ui-backup-${Date.now()}.json`;
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    finishActionButton("exportBackupBtn", "actionDone", "done", "exportBackup");
    setStatus(t("backupExported"), "ok");
    window.alert(t("backupExportedAlert"));
  } catch (error) {
    finishActionButton("exportBackupBtn", "actionFailed", "failed", "exportBackup");
    setStatus(error.message, "bad");
  } finally {
    setBusy(false);
  }
}

function chooseBackupFile() {
  $("backupFileInput").value = "";
  $("backupFileInput").click();
}

async function importBackupFromFile(event) {
  const file = event.target.files && event.target.files[0];
  event.target.value = "";
  if (!file) return;
  setBusy(true);
  pulseActionButton("importBackupBtn", "importingBackup");
  setStatus(t("importingBackup"));
  try {
    const payload = JSON.parse(await file.text());
    const result = await api("/api/backup/import", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    state = result.state;
    maintenance = result.maintenance || maintenance;
    runtimeProxy = { now: null, available: false };
    delays = {};
    setDirty(false);
    render();
    if (result.tproxySync && result.tproxySync.code !== 0) {
      finishActionButton("importBackupBtn", "actionFailed", "failed", "importBackup");
      setStatus(`${t("backupImported")}；${t("tproxySyncFailed")}`, "bad");
      return;
    }
    finishActionButton("importBackupBtn", "actionDone", "done", "importBackup");
    setStatus(t("backupImported"), "ok");
    window.alert(t("backupImportedAlert"));
    loadProxyInfo(false).then(() => render()).catch(() => {});
  } catch (error) {
    finishActionButton("importBackupBtn", "actionFailed", "failed", "importBackup");
    setStatus(error.message || t("backupImportFailed"), "bad");
  } finally {
    setBusy(false);
  }
}

function allowedEntryTypes() {
  return listEntryTypes[active] || allEntryTypes;
}

function renderTypeOptions() {
  const select = $("typeInput");
  const current = allowedEntryTypes().includes(select.value) ? select.value : allowedEntryTypes()[0];
  select.innerHTML = "";
  for (const type of allowedEntryTypes()) {
    const option = document.createElement("option");
    option.value = type;
    option.textContent = translations[lang].types[type];
    option.selected = type === current;
    select.appendChild(option);
  }
  updateValueHint();
}

function updateValueHint() {
  const type = $("typeInput").value || allowedEntryTypes()[0];
  $("valueInput").placeholder = translations[lang].placeholders[type] || "example.com";
}

function renderMatchHelp() {
  const box = document.createElement("section");
  box.className = "match-help";
  const title = document.createElement("strong");
  title.textContent = t("matchHelp");
  const listNote = document.createElement("p");
  listNote.textContent = translations[lang].listTypeHelp[active];
  const examples = document.createElement("div");
  examples.className = "match-examples";
  for (const type of allowedEntryTypes()) {
    const item = document.createElement("span");
    const label = document.createElement("b");
    label.textContent = translations[lang].types[type];
    const help = translations[lang].typeHelp[type];
    const detail = document.createElement("small");
    detail.textContent = `${help.use}; ${lang === "zh" ? "例如" : "example"}: ${help.example}`;
    item.append(label, detail);
    examples.appendChild(item);
  }
  box.append(title, listNote, examples);
  return box;
}

function ddnsDnsMode() {
  state.groups.ddns = state.groups.ddns || {};
  return state.groups.ddns.dns === "remote" ? "remote" : "local";
}

function renderDdnsControls() {
  const panel = document.createElement("section");
  panel.className = "ddns-mode";
  const copy = document.createElement("div");
  const title = document.createElement("strong");
  title.textContent = t("dnsMode");
  const hint = document.createElement("div");
  hint.className = "ddns-hint";
  const lines = translations[lang][ddnsDnsMode() === "remote" ? "ddnsRemoteHint" : "ddnsLocalHint"];
  for (const line of lines) {
    const item = document.createElement("p");
    item.textContent = line;
    hint.appendChild(item);
  }
  copy.append(title, hint);
  const switcher = document.createElement("div");
  switcher.className = "segment";
  [
    ["local", t("ddnsLocalDns")],
    ["remote", t("ddnsRemoteDns")],
  ].forEach(([mode, label]) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.className = ddnsDnsMode() === mode ? "active" : "";
    button.addEventListener("click", () => setDdnsDnsMode(mode));
    switcher.appendChild(button);
  });
  panel.append(copy, switcher);
  return panel;
}

function setDdnsDnsMode(mode) {
  state.groups.ddns = state.groups.ddns || {};
  if (state.groups.ddns.dns === mode) return;
  state.groups.ddns.dns = mode;
  markChanged();
  render();
}

function nodeTags() {
  return (state.nodes || []).map((node) => node.outbound.tag);
}

function enabledNodeTags() {
  return (state.nodes || []).filter((node) => node.enabled !== false).map((node) => node.outbound.tag);
}

function renderDefaultSelect() {
  const select = $("proxyDefault");
  const current = state.groups?.proxy?.default || "Auto";
  const options = ["Auto", ...enabledNodeTags()];
  select.innerHTML = "";
  for (const tag of options) {
    const option = document.createElement("option");
    option.value = tag;
    option.textContent = `${t("defaultProxy")}: ${tag}`;
    option.selected = tag === current;
    select.appendChild(option);
  }
}

function currentDefault() {
  return state.groups?.proxy?.default || "Auto";
}

function formatDelay(tag) {
  const item = delays[tag];
  if (!item) return t("delayUnknown");
  if (item.delay === null || item.delay === undefined) return item.error ? t("delayFailed") : t("delayUnknown");
  return `${item.delay} ms`;
}

function delayTone(tag) {
  const item = delays[tag];
  if (!item || item.delay === null || item.delay === undefined) return "unknown";
  if (item.delay <= 180) return "good";
  if (item.delay <= 450) return "warn";
  return "bad";
}

function renderNodes() {
  const nodes = state.nodes || [];
  state.groups.auto = state.groups.auto || {};
  state.groups.fakeip = state.groups.fakeip || {};
  if (document.activeElement !== $("autoUrl")) $("autoUrl").value = state.groups.auto.url || "https://www.gstatic.com/generate_204";
  if (document.activeElement !== $("autoInterval")) $("autoInterval").value = state.groups.auto.interval || "2m";
  if (document.activeElement !== $("autoTolerance")) $("autoTolerance").value = state.groups.auto.tolerance ?? 50;
  if (document.activeElement !== $("fakeipV4")) $("fakeipV4").value = state.groups.fakeip.inet4_range || "28.0.0.0/8";
  if (document.activeElement !== $("fakeipV6")) $("fakeipV6").value = state.groups.fakeip.inet6_range || "2001:2::/64";
  $("nodeTitle").textContent = t("nodes");
  $("nodeSummary").textContent = editingNodeTag
    ? `${t("editingNode")}: ${editingNodeTag}`
    : `${nodes.length} ${t("entries")} · ${t("defaultProxy")}: ${currentDefault()}${runtimeProxy.now ? ` · ${t("activeProxy")}: ${runtimeProxy.now}` : ""}`;
  $("nodeSubmit").textContent = editingNodeTag ? t("updateNode") : t("addNode");
  $("nodeCancel").classList.toggle("hidden", !editingNodeTag);
  renderDefaultSelect();
  const rows = $("nodeRows");
  rows.innerHTML = "";
  if (!nodes.length) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = t("noEntries");
    rows.appendChild(empty);
    return;
  }
  const autoCard = document.createElement("div");
  autoCard.className = `node-card auto-card ${currentDefault() === "Auto" ? "default" : ""} ${runtimeProxy.now === "Auto" ? "runtime" : ""}`;
  const autoTitle = document.createElement("div");
  autoTitle.className = "node-title";
  const autoName = document.createElement("strong");
  autoName.textContent = "Auto";
  const autoMeta = document.createElement("span");
  autoMeta.textContent = "urltest · automatic best node";
  const autoBadges = document.createElement("div");
  autoBadges.className = "node-badges";
  if (currentDefault() === "Auto") {
    const saved = document.createElement("span");
    saved.className = "node-pill saved";
    saved.textContent = t("defaultSaved");
    autoBadges.appendChild(saved);
  }
  if (runtimeProxy.now === "Auto") {
    const activeBadge = document.createElement("span");
    activeBadge.className = "node-pill active";
    activeBadge.textContent = t("activeNow");
    autoBadges.appendChild(activeBadge);
  }
  autoTitle.append(autoName, autoMeta, autoBadges);
  const autoActions = document.createElement("div");
  autoActions.className = "node-actions";
  const autoDefaultButton = document.createElement("button");
  autoDefaultButton.type = "button";
  autoDefaultButton.className = "secondary-btn";
  autoDefaultButton.textContent = currentDefault() === "Auto" ? t("defaultSaved") : t("setDefault");
  autoDefaultButton.disabled = currentDefault() === "Auto" || busy;
  autoDefaultButton.addEventListener("click", (event) => {
    event.stopPropagation();
    chooseDefault("Auto");
  });
  autoActions.appendChild(autoDefaultButton);
  autoCard.append(autoTitle, autoActions);
  rows.appendChild(autoCard);
  for (const node of nodes) {
    const outbound = node.outbound;
    const isEnabled = node.enabled !== false;
    const isDefault = currentDefault() === outbound.tag;
    const isRuntime = runtimeProxy.now === outbound.tag;
    const card = document.createElement("div");
    card.className = `node-card ${editingNodeTag === outbound.tag ? "selected" : ""} ${isDefault ? "default" : ""} ${!isEnabled ? "disabled" : ""}`;
    card.addEventListener("click", () => selectNode(outbound.tag));
    const title = document.createElement("div");
    title.className = "node-title";
    const name = document.createElement("strong");
    name.textContent = outbound.tag;
    const meta = document.createElement("span");
    meta.textContent = `${outbound.type} · ${outbound.server}:${outbound.server_port}`;
    const badges = document.createElement("div");
    badges.className = "node-badges";
    const delay = document.createElement("span");
    delay.className = `node-pill delay ${delayTone(outbound.tag)}`;
    delay.textContent = `${t("delay")}: ${formatDelay(outbound.tag)}`;
    badges.appendChild(delay);
    if (isDefault) {
      const saved = document.createElement("span");
      saved.className = "node-pill saved";
      saved.textContent = t("defaultSaved");
      badges.appendChild(saved);
    }
    if (isRuntime) {
      const activeBadge = document.createElement("span");
      activeBadge.className = "node-pill active";
      activeBadge.textContent = t("activeNow");
      badges.appendChild(activeBadge);
    }
    title.append(name, meta, badges);

    const actions = document.createElement("div");
    actions.className = "node-actions";
    const defaultButton = document.createElement("button");
    defaultButton.type = "button";
    defaultButton.className = "secondary-btn";
    defaultButton.textContent = isDefault ? t("defaultSaved") : t("setDefault");
    defaultButton.disabled = !isEnabled || isDefault || busy;
    defaultButton.addEventListener("click", (event) => {
      event.stopPropagation();
      chooseDefault(outbound.tag);
    });
    const toggle = document.createElement("label");
    toggle.className = "switchline";
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = isEnabled;
    checkbox.addEventListener("click", (event) => event.stopPropagation());
    checkbox.addEventListener("change", () => toggleNode(outbound.tag, checkbox.checked));
    const label = document.createElement("span");
    label.textContent = checkbox.checked ? t("enabled") : t("disabled");
    toggle.append(checkbox, label);
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "danger-btn";
    remove.textContent = t("deleteNode");
    remove.addEventListener("click", (event) => {
      event.stopPropagation();
      deleteNode(outbound.tag);
    });
    const primaryActions = document.createElement("div");
    primaryActions.className = "node-primary-actions";
    primaryActions.append(toggle, defaultButton);
    actions.append(primaryActions, remove);
    card.append(title, actions);
    rows.appendChild(card);
  }
}

function getNode(tag) {
  return (state.nodes || []).find((node) => node.outbound.tag === tag);
}

function stableNodeString(node) {
  return JSON.stringify(node || null);
}

function nodeFormChanged() {
  if (!editingNodeTag) return true;
  try {
    return stableNodeString(buildNodeFromForm()) !== editingNodeSnapshot;
  } catch (error) {
    return true;
  }
}

function selectNode(tag) {
  const node = getNode(tag);
  if (!node) return;
  const outbound = node.outbound;
  editingNodeTag = tag;
  $("nodeType").value = outbound.type || "hysteria2";
  $("nodeTag").value = outbound.tag || "";
  $("nodeServer").value = outbound.server || "";
  $("nodePort").value = outbound.server_port || "";
  $("nodeSecret").value = outbound.type === "vless" ? outbound.uuid || "" : outbound.password || "";
  $("nodeSni").value = outbound.tls?.server_name || "";
  $("nodeObfs").value = outbound.obfs?.password || "";
  $("nodePublicKey").value = outbound.tls?.reality?.public_key || "";
  $("nodeShortId").value = outbound.tls?.reality?.short_id || "";
  $("nodeUp").value = outbound.up_mbps || outbound.multiplex?.brutal?.up_mbps || "";
  $("nodeDown").value = outbound.down_mbps || outbound.multiplex?.brutal?.down_mbps || "";
  $("nodeInsecure").checked = outbound.tls?.insecure !== false;
  editingNodeSnapshot = stableNodeString(buildNodeFromForm());
  nodeEditChanged = false;
  setStatus(`${t("nodeSelected")}: ${tag}`, "ok");
  render();
}

function clearNodeForm() {
  editingNodeTag = null;
  editingNodeSnapshot = "";
  nodeEditChanged = false;
  $("nodeForm").reset();
  $("nodeInsecure").checked = true;
  setStatus(t("editCancelled"));
  render();
}

function syncNodeFormState() {
  nodeEditChanged = nodeFormChanged();
  updateButtons();
}

async function chooseDefault(tag) {
  state.groups.proxy = state.groups.proxy || {};
  state.groups.proxy.default = tag;
  markChanged();
  setBusy(true);
  setStatus(t("pendingDefault"));
  render();
  try {
    const result = await api("/api/proxy/select", {
      method: "POST",
      body: JSON.stringify({ tag }),
    });
    if (result.proxy?.ok) {
      runtimeProxy = { now: tag, available: true, error: "" };
      setStatus(t("pendingDefault"), "ok");
    } else {
      setStatus(`${t("proxySwitchFailed")}: ${result.proxy?.error || ""}`, "bad");
    }
  } catch (error) {
    setStatus(`${t("proxySwitchFailed")}: ${error.message}`, "bad");
  } finally {
    setBusy(false);
    render();
  }
}

function toggleNode(tag, enabled) {
  const enabledCount = enabledNodeTags().length;
  if (!enabled && enabledCount <= 1) {
    setStatus("At least one node must stay enabled", "bad");
    render();
    return;
  }
  const node = (state.nodes || []).find((item) => item.outbound.tag === tag);
  if (node) node.enabled = enabled;
  if (!enabled && state.groups?.proxy?.default === tag) {
    state.groups.proxy.default = "Auto";
  }
  markChanged();
  render();
}

async function refreshDelays() {
  setBusy(true);
  setStatus(t("testingDelay"));
  try {
    await loadProxyInfo(true);
    render();
    setStatus(t("delayUpdated"), "ok");
  } catch (error) {
    setStatus(error.message, "bad");
  } finally {
    setBusy(false);
  }
}

function deleteNode(tag) {
  if (state.groups?.proxy?.default === tag) {
    setStatus(t("nodeDeleteBlocked"), "bad");
    return;
  }
  state.nodes = (state.nodes || []).filter((node) => node.outbound.tag !== tag);
  if (editingNodeTag === tag) {
    editingNodeTag = null;
    editingNodeSnapshot = "";
    nodeEditChanged = false;
    $("nodeForm").reset();
    $("nodeInsecure").checked = true;
  }
  markChanged();
  render();
}

function buildNodeFromForm() {
  const type = $("nodeType").value;
  const tag = $("nodeTag").value.trim();
  const upMbps = $("nodeUp").value ? Number($("nodeUp").value) : null;
  const downMbps = $("nodeDown").value ? Number($("nodeDown").value) : null;
  if ((upMbps !== null && (!Number.isFinite(upMbps) || upMbps <= 0)) || (downMbps !== null && (!Number.isFinite(downMbps) || downMbps <= 0))) {
    throw new Error("Mbps must be a positive number");
  }
  const existing = editingNodeTag ? getNode(editingNodeTag) : null;
  const base = existing && existing.outbound.type === type ? structuredClone(existing.outbound) : {};
  const duplicate = nodeTags().some((item) => item === tag && item !== editingNodeTag);
  if (!tag || duplicate) {
    throw new Error(t("duplicateNode"));
  }
  const outbound = {
    ...base,
    type,
    tag,
    server: $("nodeServer").value.trim(),
    server_port: Number($("nodePort").value || 443),
    tls: {
      ...(base.tls || {}),
      enabled: true,
      server_name: $("nodeSni").value.trim() || $("nodeServer").value.trim(),
      insecure: $("nodeInsecure").checked,
    },
  };
  const secret = $("nodeSecret").value.trim();
  const obfsPassword = $("nodeObfs").value.trim();
  const publicKey = $("nodePublicKey").value.trim();
  const shortId = $("nodeShortId").value.trim();
  if (type === "hysteria2") {
    delete outbound.uuid;
    outbound.password = secret;
    if (upMbps !== null) outbound.up_mbps = upMbps;
    else delete outbound.up_mbps;
    if (downMbps !== null) outbound.down_mbps = downMbps;
    else delete outbound.down_mbps;
    if (obfsPassword) {
      outbound.obfs = { ...(base.obfs || {}), type: "salamander", password: obfsPassword };
    } else {
      delete outbound.obfs;
    }
  } else {
    delete outbound.password;
    delete outbound.up_mbps;
    delete outbound.down_mbps;
    delete outbound.obfs;
    outbound.uuid = secret;
    outbound.packet_encoding = outbound.packet_encoding || "xudp";
    outbound.tcp_fast_open = outbound.tcp_fast_open !== false;
    outbound.tls.utls = outbound.tls.utls || { enabled: true, fingerprint: "chrome" };
    if (upMbps !== null || downMbps !== null) {
      outbound.multiplex = outbound.multiplex || { enabled: true, protocol: "h2mux", padding: false };
      outbound.multiplex.brutal = outbound.multiplex.brutal || { enabled: true };
      outbound.multiplex.brutal.enabled = true;
      if (upMbps !== null) outbound.multiplex.brutal.up_mbps = upMbps;
      else delete outbound.multiplex.brutal.up_mbps;
      if (downMbps !== null) outbound.multiplex.brutal.down_mbps = downMbps;
      else delete outbound.multiplex.brutal.down_mbps;
    } else if (outbound.multiplex?.brutal) {
      delete outbound.multiplex.brutal.up_mbps;
      delete outbound.multiplex.brutal.down_mbps;
    }
    if (publicKey) {
      outbound.tls.reality = { ...(base.tls?.reality || {}), enabled: true, public_key: publicKey };
      if (shortId) outbound.tls.reality.short_id = shortId;
      else delete outbound.tls.reality.short_id;
    } else {
      delete outbound.tls.reality;
    }
  }
  return { enabled: existing?.enabled ?? true, outbound };
}

async function addNode(event) {
  event.preventDefault();
  let node;
  try {
    node = buildNodeFromForm();
  } catch (error) {
    setStatus(error.message, "bad");
    return;
  }
  if (editingNodeTag) {
    const index = state.nodes.findIndex((item) => item.outbound.tag === editingNodeTag);
    if (index >= 0) state.nodes[index] = node;
    if (state.groups?.proxy?.default === editingNodeTag) {
      state.groups.proxy.default = node.outbound.tag;
    }
  } else {
    state.nodes.push(node);
  }
  editingNodeTag = node.outbound.tag;
  editingNodeSnapshot = stableNodeString(node);
  nodeEditChanged = false;
  event.target.reset();
  $("nodeInsecure").checked = true;
  selectNode(node.outbound.tag);
  markChanged();
  render();
  await save();
}

function removeEntry(target) {
  state.lists[active] = (state.lists[active] || []).filter(
    (item) => !(item.type === target.type && item.value === target.value),
  );
  render();
  markChanged();
}

function addEntry(event) {
  event.preventDefault();
  const type = $("typeInput").value;
  const value = $("valueInput").value.trim().toLowerCase().replace(/\.$/, "");
  if (!value) return;
  const exists = (state.lists[active] || []).some((item) => item.type === type && item.value === value);
  if (!exists) state.lists[active].push({ type, value });
  $("valueInput").value = "";
  render();
  markChanged();
}

async function save() {
  syncDraftSettings();
  if (!dirty) {
    setStatus(t("noChanges"));
    return;
  }
  setBusy(true);
  setStatus(t("savingWithCheck"));
  try {
    const result = await api("/api/save", {
      method: "POST",
      body: JSON.stringify({ lists: state.lists, nodes: state.nodes, groups: state.groups }),
    });
    state = result.state;
    maintenance = result.maintenance || maintenance;
    await loadProxyInfo(true);
    if (editingNodeTag && getNode(editingNodeTag)) {
      editingNodeSnapshot = stableNodeString(buildNodeFromForm());
      nodeEditChanged = false;
    }
    setDirty(false);
    render();
    if (result.tproxySync && result.tproxySync.code !== 0) {
      setStatus(`${t("savedAndRestarted")}；${t("tproxySyncFailed")}`, "bad");
    } else {
      setStatus(`${t("savedAndRestarted")}；${t("delayUpdated")}`, "ok");
      window.alert(t("savedAlert"));
    }
  } catch (error) {
    setStatus(error.message || t("changesBlocked"), "bad");
  } finally {
    setBusy(false);
  }
}

async function restart() {
  setBusy(true);
  pulseActionButton("restartSingboxBtn", "restartingSingbox");
  setStatus(t("restartingSingbox"));
  try {
    const result = await api("/api/restart", { method: "POST", body: "{}" });
    state = result.state;
    await loadProxyInfo(false);
    render();
    const checkResult = result.check;
    const restartResult = result.restart;
    if (checkResult.code !== 0) {
      finishActionButton("restartSingboxBtn", "actionFailed", "failed", "restartSingbox");
      setStatus(checkResult.stderr || t("checkFailed"), "bad");
      return;
    }
    if (restartResult.code !== 0) {
      finishActionButton("restartSingboxBtn", "actionFailed", "failed", "restartSingbox");
      setStatus(restartResult.stderr || t("restartFailed"), "bad");
      return;
    }
    finishActionButton("restartSingboxBtn", "actionDone", "done", "restartSingbox");
    setStatus(t("singboxRestarted"), "ok");
  } catch (error) {
    finishActionButton("restartSingboxBtn", "actionFailed", "failed", "restartSingbox");
    setStatus(error.message, "bad");
  } finally {
    setBusy(false);
  }
}

async function restartTproxy() {
  setBusy(true);
  pulseActionButton("restartTproxyBtn", "restartingTproxy");
  setStatus(t("restartingTproxy"));
  try {
    const result = await api("/api/tproxy/restart", { method: "POST", body: "{}" });
    maintenance = result.maintenance || maintenance;
    if (result.state) state = result.state;
    render();
    if (result.restart?.code !== 0) {
      finishActionButton("restartTproxyBtn", "actionFailed", "failed", "restartTproxy");
      setStatus(result.restart?.stderr || t("tproxyRestartFailed"), "bad");
      return;
    }
    finishActionButton("restartTproxyBtn", "actionDone", "done", "restartTproxy");
    setStatus(t("tproxyRestarted"), "ok");
  } catch (error) {
    finishActionButton("restartTproxyBtn", "actionFailed", "failed", "restartTproxy");
    setStatus(`${t("tproxyRestartFailed")} ${error.message}`, "bad");
  } finally {
    setBusy(false);
  }
}

async function restartUi() {
  setBusy(true);
  pulseActionButton("restartUiBtn", "restartingUi");
  setStatus(t("restartingUi"));
  try {
    await api("/api/ui/restart", { method: "POST", body: "{}" });
    setStatus(t("uiRestartScheduled"), "ok");
    const result = await waitForUiReconnect();
    if (result) {
      maintenance = result.maintenance || maintenance;
      if (result.state) state = result.state;
      render();
      finishActionButton("restartUiBtn", "actionDone", "done", "restartUi");
      setStatus(t("uiRestartReady"), "ok");
    } else {
      finishActionButton("restartUiBtn", "actionDone", "done", "restartUi");
      setStatus(t("uiRestartManualRefresh"), "ok");
    }
  } catch (error) {
    finishActionButton("restartUiBtn", "actionFailed", "failed", "restartUi");
    setStatus(error.message, "bad");
  } finally {
    setBusy(false);
  }
}

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    active = tab.dataset.list;
    $("searchInput").value = "";
    setStatus(t("ready"));
    render();
    if (active === "maintenance") refreshMaintenance();
  });
});

$("addForm").addEventListener("submit", addEntry);
$("nodeForm").addEventListener("submit", addNode);
$("nodeForm").addEventListener("input", syncNodeFormState);
$("nodeForm").addEventListener("change", syncNodeFormState);
$("nodeCancel").addEventListener("click", clearNodeForm);
$("searchInput").addEventListener("input", render);
$("typeInput").addEventListener("change", updateValueHint);
$("saveBtn").addEventListener("click", save);
$("logoutBtn").addEventListener("click", logout);
$("refreshDelayBtn").addEventListener("click", refreshDelays);
$("refreshMaintenanceBtn").addEventListener("click", refreshMaintenance);
$("restartSingboxBtn").addEventListener("click", restart);
$("restartTproxyBtn").addEventListener("click", restartTproxy);
$("restartUiBtn").addEventListener("click", restartUi);
$("syncTproxyBtn").addEventListener("click", syncTproxy);
$("exportBackupBtn").addEventListener("click", exportBackup);
$("importBackupBtn").addEventListener("click", chooseBackupFile);
$("backupFileInput").addEventListener("change", importBackupFromFile);
$("updateRulesBtn").addEventListener("click", updateRuleSets);
$("brandLink").addEventListener("click", goNodes);
$("brandLink").addEventListener("keydown", (event) => {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    goNodes();
  }
});

function markChanged() {
  setDirty(true);
  setStatus(t("changed"));
}

function syncNodeSettingsFromForm() {
  state.groups.auto = state.groups.auto || {};
  state.groups.auto.url = $("autoUrl").value.trim();
  state.groups.auto.interval = $("autoInterval").value.trim();
  state.groups.auto.tolerance = Number($("autoTolerance").value || 0);
  state.groups.fakeip = state.groups.fakeip || {};
  state.groups.fakeip.inet4_range = $("fakeipV4").value.trim();
  state.groups.fakeip.inet6_range = $("fakeipV6").value.trim();
  state.groups.proxy = state.groups.proxy || {};
  if (!$("proxyDefault").classList.contains("hidden") && $("proxyDefault").value) {
    state.groups.proxy.default = $("proxyDefault").value;
  }
}

function syncNodeSettingsChanged() {
  syncNodeSettingsFromForm();
  markChanged();
}

function syncDraftSettings() {
  if (active !== "nodes") return;
  syncNodeSettingsFromForm();
}

["autoUrl", "autoInterval", "autoTolerance", "fakeipV4", "fakeipV6"].forEach((id) => {
  $(id).addEventListener("input", syncNodeSettingsChanged);
  $(id).addEventListener("change", syncNodeSettingsChanged);
});
$("proxyDefault").addEventListener("change", () => {
  syncNodeSettingsChanged();
  render();
});
$("langSelect").addEventListener("change", () => {
  lang = $("langSelect").value;
  localStorage.setItem("ruleUiLang", lang);
  render();
  setStatus(t("ready"));
});
$("tokenBtn").addEventListener("click", () => {
  token = $("tokenInput").value.trim();
  localStorage.setItem("ruleUiToken", token);
  load();
});
$("tokenInput").addEventListener("keydown", (event) => {
  if (event.key === "Enter") $("tokenBtn").click();
});

applyLanguage();
setStatus(t("ready"));
updateButtons();
load();
setInterval(refreshMeta, 5000);
