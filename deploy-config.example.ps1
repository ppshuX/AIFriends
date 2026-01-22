# 部署配置文件示例
# 复制此文件为 deploy-config.ps1 并修改配置（deploy-config.ps1 会被 .gitignore 忽略）

# 服务器配置
$SERVER_USER = "acs"                    # 服务器用户名
$SERVER_HOST = "tcserver"                # 服务器地址（可以是 IP 或域名，例如：123.456.789.0 或 example.com）
$SERVER_PORT = "22"                      # SSH 端口（默认 22）
$SERVER_PATH = "~/AIFriends/backend/static/frontend"  # 服务器上的目标路径
