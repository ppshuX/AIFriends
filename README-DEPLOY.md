# 前端部署脚本使用说明

## 📦 脚本说明

项目提供了自动化部署脚本，可以在本地构建前端并自动上传到云服务器。

## 🚀 使用方法

### Windows (PowerShell)

1. **配置服务器信息**（可选）
   
   如果需要自定义配置，可以创建 `deploy-config.ps1` 文件（已配置在 `.gitignore` 中，不会被提交）：
   ```powershell
   $SERVER_USER = "acs"
   $SERVER_HOST = "tcserver"  # 或使用 IP 地址，如 "123.456.789.0"
   $SERVER_PORT = "22"
   $SERVER_PATH = "~/AIFriends/backend/static/frontend"
   ```
   
   如果不创建配置文件，脚本会使用默认配置。

2. **执行部署脚本**
   ```powershell
   .\deploy-frontend.ps1
   ```

## 📋 脚本功能

脚本会自动执行以下步骤：

1. ✅ **检查环境**：验证 Node.js 和 npm 是否安装
2. ✅ **安装依赖**：如果 `node_modules` 不存在，自动安装依赖
3. ✅ **构建项目**：执行 `npm run build` 构建前端
4. ✅ **上传文件**：使用 `scp` 上传构建产物到服务器

## ⚙️ 配置说明

### 服务器配置

- `SERVER_USER`: 服务器用户名（默认：`acs`）
- `SERVER_HOST`: 服务器地址（默认：`tcserver`，可以是 IP 或域名）
- `SERVER_PORT`: SSH 端口（默认：`22`）
- `SERVER_PATH`: 服务器上的目标路径（默认：`~/AIFriends/backend/static/frontend`）

### SSH 连接

脚本使用 `scp` 命令上传文件，需要：

1. **配置 SSH 密钥**（推荐）
   ```bash
   # 在本地生成 SSH 密钥（如果还没有）
   ssh-keygen -t rsa -b 4096
   
   # 将公钥复制到服务器
   ssh-copy-id acs@tcserver
   ```

2. **或使用密码**：脚本执行时会提示输入服务器密码

## 🔧 故障排除

### 问题1：SSH 连接失败

**解决方案：**
- 检查服务器地址和端口是否正确
- 确认网络连接正常
- 检查防火墙设置

### 问题2：权限被拒绝

**解决方案：**
- 确保服务器上目标目录存在：`mkdir -p ~/AIFriends/backend/static/frontend`
- 检查目录权限：`chmod 755 ~/AIFriends/backend/static/frontend`
- 配置 SSH 密钥避免每次输入密码

### 问题3：构建失败

**解决方案：**
- 检查 Node.js 版本是否符合要求（>= 20.19.0 或 >= 22.12.0）
- 删除 `node_modules` 和 `package-lock.json` 后重新安装
- 检查 `vite.config.js` 配置是否正确

### 问题4：文件上传失败

**解决方案：**
- 确认服务器路径存在
- 检查磁盘空间是否充足
- 查看服务器日志：`tail -f /var/log/auth.log`

## 📝 注意事项

1. **首次使用**：确保服务器上已创建目标目录
   ```bash
   ssh acs@tcserver "mkdir -p ~/AIFriends/backend/static/frontend"
   ```

2. **构建产物**：构建产物会直接输出到 `backend/static/frontend/`，无需手动复制

3. **Git 忽略**：`deploy-config.ps1` 已在 `.gitignore` 中，不会提交到仓库

4. **安全建议**：不要在配置文件中硬编码密码，使用 SSH 密钥认证

## 🎯 快速开始

```powershell
# Windows
.\deploy-frontend.ps1

# Linux/Mac
./deploy-frontend.sh
```

就是这么简单！🚀
