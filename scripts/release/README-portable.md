# AIFriends Windows 便携包

一个下载即用的本地演示包：解压后双击 `start.bat`，浏览器自动打开
http://127.0.0.1:8000/ 即可使用，**无需安装 Python、Node.js 或任何其他环境**。

首次启动会自动完成：

1. 生成 `.env`（随机签名密钥 + 默认配置）；
2. 创建 SQLite 数据库并导入 4 个官方演示角色与 4 个腾讯云音色；
3. 启动本地服务并打开浏览器。

按 `Ctrl+C` 或直接关闭窗口即可停止服务。

**数据目录**：优先写在包内 `backend/`（解压到任意可写目录时）；若安装目录不可写
（例如装到 `Program Files`），则自动改用 `%LOCALAPPDATA%\AIFriends\`
（`.env`、`db.sqlite3`、`media/`）。启动日志会打印一行「数据目录：...」。
便携解压用法下删除整个文件夹即可完全卸载；安装版还可一并删除上述 AppData 目录。

## 使用步骤

1. 解压本文件夹到任意可写目录（路径中可以含中文）；
2. 双击 `start.bat`，等待出现“服务已启动”提示；
3. 在页面中注册一个账号，即可浏览演示角色、创建自己的角色。

## 开启 AI 对话（可选）

不配置密钥时，登录、角色管理、历史记录等页面均可正常使用，但**发起对话会失败**，
这是预期行为。如需完整体验，用记事本编辑数据目录下的 `.env`
（路径见启动日志「数据目录：...」，便携解压时通常是 `backend/.env`）：

```dotenv
# 角色对话与长期记忆（腾讯云 TokenHub，OpenAI 兼容）
API_KEY=你的密钥

# 语音输入（阿里云 DashScope 实时 ASR）
WSS_URL=你的WebSocket地址

# 角色语音回复（腾讯云流式 TTS，演示角色使用 tencent: 音色）
TENCENT_TTS_APP_ID=你的AppId
TENCENT_TTS_SECRET_ID=你的SecretId
TENCENT_TTS_SECRET_KEY=你的SecretKey
```

保存后重新双击 `start.bat` 生效。

## 常见问题

- **安装到 Program Files 后提示权限不足**：v0.0.6 起会自动把可写状态放到
  `%LOCALAPPDATA%\AIFriends\`，一般无需以管理员运行。若仍报错，请查看启动日志中的
  「数据目录」一行。
- **双击后窗口一闪而过**：说明启动报错，可在命令行中执行
  `python\python.exe run_server.py` 查看完整错误。
- **提示端口被占用**：说明 8000 端口已有程序（可能是上一次启动未关闭），
  关闭旧窗口后重试。
- **浏览器没有自动打开**：手动访问 http://127.0.0.1:8000/ 即可。
- **杀毒软件告警**：本包由 GitHub Actions 自动构建，包含嵌入式 Python 与
  数百个依赖文件，个别杀软可能误报，可选择信任或放弃使用。
- **安全提示**：本包以本地演示模式运行（监听 127.0.0.1），请勿直接暴露到
  公网；`.env` 中生成的密钥仅限本机使用。

## 技术说明

本包由仓库 `scripts/release/build-portable.ps1` 组装，在 GitHub Actions 的
Windows 构建机上自动完成并通过启动冒烟测试。详见项目仓库 README 的
“Windows 便携包”一节。