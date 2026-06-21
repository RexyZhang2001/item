# WhatsApp 双向与 publish3.0 内嵌 Web 前端交接

更新日期：2026-06-21  
仓库：`/Users/tianxiangzhao/item`

## 当前状态

- `agent-toolbox`、`chitung-center`、`chitung-frontend` 已打通 WhatsApp 双向基础链路。
- 本机已编译并配置 `wacli`，当前 WhatsApp 账号已登录。
- WhatsApp 群组、消息搜索已不再强依赖旧的 `whatsapp-archive:8787`，可自动回退到 `wacli` 本地数据库。
- `chitong-lingxun/publish3.0` 已新增 WPF WebView2 内嵌页，用于打开当前 Vue Web 前端。

## WhatsApp 数据位置

当前本机配置在 `agent-toolbox/.env`（该文件被 `.gitignore` 忽略，不会提交）：

```env
WACLI_BIN=/Users/tianxiangzhao/item/chitong-lingxun/runtime/bin/wacli
WACLI_WORKDIR=/Users/tianxiangzhao/item/chitong-lingxun/runtime/wacli-workdir
WACLI_STORE_DIR=/Users/tianxiangzhao/item/chitong-lingxun/runtime/store
```

主要数据文件：

```text
/Users/tianxiangzhao/item/chitong-lingxun/runtime/store/wacli.db
/Users/tianxiangzhao/item/chitong-lingxun/runtime/store/session.db
```

`wacli.db` 存消息、群组、联系人、全文搜索索引。`session.db` 存 WhatsApp 登录态。

## WhatsApp 后端能力

工具箱新增/增强：

- `whatsapp_auth_start`：启动二维码或手机号配对登录。
- `whatsapp_auth_status`：读取登录状态；若已登录，会返回 `authenticated`。
- `whatsapp_auth_stop`：停止当前登录/同步进程，不退出账号。
- `whatsapp_auth_logout`：退出账号，需要 `confirmed=true`。
- `whatsapp_groups_wacli`：从本地 `wacli` 列群。
- `whatsapp_groups_refresh`：实时刷新已加入群组并写入本地库。
- `whatsapp_send_text_confirmed`：人工确认后通过 `wacli send text --to ... --message ...` 发送消息。
- `whatsapp_search`：先调旧 archive；失败时自动 fallback 到 `wacli messages search`。

中台新增/增强：

- `POST /api/whatsapp/auth/start`
- `POST /api/whatsapp/auth/status`
- `POST /api/whatsapp/auth/stop`
- `POST /api/whatsapp/auth/logout`
- `POST /api/whatsapp/groups`
- `POST /api/whatsapp/groups/refresh`
- `POST /api/whatsapp/search`
- `POST /api/whatsapp/send`
- `POST /api/whatsapp/ingest-search`

前端页面：

```text
chitung-frontend/src/pages/WhatsAppOpsPage.vue
```

页面支持：

- 生成二维码登录。
- 香港手机号配对码登录。
- 停止/退出登录。
- 刷新群组。
- 搜索消息。
- 把 WhatsApp 搜索结果转入中台工作流。
- 选择真实群组并确认发送 WhatsApp 消息。

## 退出登录与刷新群组

“停止”与“退出登录”不同：

- 停止：只停止当前登录/同步进程，不解绑 WhatsApp。
- 退出登录：执行 `wacli auth logout`，会使当前设备登录态失效，需要重新扫码。

新建群看不到时：

1. 在页面点“刷新群组”。
2. 或命令行执行：

```bash
WACLI_STORE_DIR=/Users/tianxiangzhao/item/chitong-lingxun/runtime/store \
/Users/tianxiangzhao/item/chitong-lingxun/runtime/bin/wacli groups refresh
```

## publish3.0 内嵌 Web 前端

WPF 项目：

```text
chitong-lingxun/publish3.0/source/WacliDesktop
```

新增/修改：

- `WacliDesktop.csproj`：新增 `Microsoft.Web.WebView2`；配置 `Assets/ChitungWeb/**/*` 为 Content。
- `Views/ChitungWebView.xaml`
- `Views/ChitungWebView.xaml.cs`
- `HomeWindow.xaml`：新增入口“赤瞳网页版”。
- `HomeWindow.xaml.cs`：入口打开 `ModuleShellWindow("赤瞳网页版", new ChitungWebView(), 1320, 860)`。
- `copy-chitung-web.ps1`：构建并复制 `chitung-frontend/dist` 到 WPF 资源目录。

本地复制目标：

```text
chitong-lingxun/publish3.0/source/WacliDesktop/Assets/ChitungWeb
```

注意：`Assets/ChitungWeb` 是构建产物，默认不建议长期手工维护；需要更新时运行：

```powershell
cd chitong-lingxun\publish3.0\source
powershell -ExecutionPolicy Bypass -File .\copy-chitung-web.ps1
```

## 验证结果

已完成：

- `chitung-frontend` build 通过。
- `WacliDesktop/Assets/ChitungWeb/index.html` 已能通过本地静态服务渲染。
- `/api/whatsapp/groups` 返回真实群组。
- `/api/whatsapp/search` 可从 `wacli` 本地库返回消息。
- `whatsapp_send_text_confirmed` dry-run 使用正确参数：`--to` / `--message`。

限制：

- 当前开发机是 macOS，无法直接运行 `net8.0-windows` WPF/WebView2 桌面窗口。
- 本机没有 `dotnet`，因此未在 macOS 上执行 WPF 编译。
- Windows 机器运行前需要安装 .NET 8 Desktop Runtime / WebView2 Runtime（通常 Windows 11 已有 WebView2）。

## 不要提交的内容

不要提交：

- `agent-toolbox/.env`
- `chitung-center/.env`
- `chitung-frontend/.env`
- `chitong-lingxun/runtime/store/*.db`
- `chitong-lingxun/runtime/tools/go`
- `chitong-lingxun/runtime/src/wacli`
- `chitong-lingxun/publish3.0/source/WacliDesktop/Assets/ChitungWeb`（可由脚本再生成，除非明确需要把构建产物纳入仓库）

## 后续建议

1. 在 Windows 上执行 WPF 编译并打开“赤瞳网页版”模块确认 WebView2 正常。
2. 若需要离线分发，把 `Assets/ChitungWeb` 纳入发布包，但不必纳入源码仓库。
3. 为 WhatsApp 同步增加“同步状态/进度”UI，例如读取 `messages_synced` 或 `wacli auth status`。
4. 将 `wacli` store 路径做成系统设置项，避免写死在 `.env`。
