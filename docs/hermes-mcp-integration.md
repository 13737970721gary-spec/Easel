# Easel ↔ Hermes 原生 MCP 接入

## 状态

- MCP server：`D:/Garyai/opensource/Easel/easel_mcp_server.py`
- 传输：本机 stdio
- Hermes 配置：`~/.hermes/config.yaml` 的 `mcp_servers.easel`
- MCP SDK：Easel `.venv` 中 `mcp 1.30.0`
- 已发现工具：28 个
- Easel Web：仍可保留在 `127.0.0.1:7860`，作为人工排查/扫码后台；MCP 不依赖 Web 端口

## 调用关系

```text
Hermes 任意 bot
  └─ mcp_easel_*
       └─ Easel MCP stdio server
            ├─ Easel outputs / profiles / skills
            ├─ 隔离浏览器登录态的只读检查
            ├─ analytics / schedule / ideas
            └─ 受控发布脚本（默认关闭）
```

这不是 Easel ACP 单 bot 连接，也不需要新建 `easel` bot；所有已授权的 Hermes bot 都可以发现同一组 MCP 工具。是否让某个 bot 实际调用，仍由该 bot 的工具集和任务边界决定。

## 工具分层

### 只读

`easel_status`、`easel_list_personas`、`easel_read_persona`、`easel_list_skills`、`easel_read_skill`、`easel_list_outputs`、`easel_read_output`、`easel_list_accounts`、`easel_login_status`、`easel_check_account`、`easel_fetch_analytics`、`easel_get_publish_policy`、`easel_plan_publish`、`easel_publish_status`、`easel_list_schedule`、`easel_schedule_context`、`easel_list_ideas`

### 受控写入

排期和选题的创建、更新、删除都必须先调用 `easel_request_write_confirmation`，再把一次性 `confirmation_id` 传给对应写工具。确认凭证与操作 payload 绑定，10 分钟过期且只能使用一次。

人工发布包同样先请求确认，再调用 `easel_export_manual_package`。导出包不会上传、不含登录凭据，也不代表发布成功。

### 高风险发布

`easel_request_publish_confirmation` 只生成发布摘要和一次性确认凭证，不启动发布。`easel_publish` 还要求：

1. 主机显式设置 `EASEL_MCP_ALLOW_PUBLISH=1`；
2. 提供与平台、标题、正文、素材完全匹配的未使用确认凭证；
3. 发布脚本返回退出码 0。

MCP 默认不满足第 1 条，因此真实发布默认被阻断。发布脚本退出码 0 也只表示已提交，`verified` 永远为 false，必须另行做平台读回对账，未知状态不改写为成功。

## 明确禁止

- 不暴露 cookie、密码、AppSecret、token、环境变量或原始凭据文件；
- 不提供任意 shell、任意 Python 或任意文件写入工具；
- 不通过 MCP 自动扫码、导入 cookie、删除浏览器 profile 或修改平台账号；
- 不把 Web API 的启动状态当作发布成功；
- 不开放局域网 HTTP MCP 端点；当前只用本机 stdio。

## 验收记录

```text
hermes mcp test easel
✓ Connected
✓ Tools discovered: 28

C:/Python314/python.exe -m pytest tests/test_easel_mcp_server.py -q
5 passed
```

独立 stdio client 已完成 initialize、tools/list、`easel_status`、`easel_plan_publish` 往返验证。
