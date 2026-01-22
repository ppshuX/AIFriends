#!/bin/bash
# AIFriends 前端部署脚本
# 功能：本地构建前端并上传到云服务器

# ==================== 配置区域 ====================
# 请根据实际情况修改以下配置

# 服务器配置
SERVER_USER="acs"                    # 服务器用户名
SERVER_HOST="tcserver"                # 服务器地址（可以是 IP 或域名）
SERVER_PORT="22"                      # SSH 端口（默认 22）
SERVER_PATH="~/AIFriends/backend/static/frontend"  # 服务器上的目标路径

# 本地路径配置（脚本所在目录为项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
BUILD_OUTPUT="$SCRIPT_DIR/backend/static/frontend"

# ==================== 脚本开始 ====================

echo "========================================"
echo "  AIFriends 前端部署脚本"
echo "========================================"
echo ""

# 1. 检查 Node.js 和 npm
echo "[1/4] 检查 Node.js 环境..."
if ! command -v node &> /dev/null; then
    echo "  ✗ 未找到 Node.js，请先安装 Node.js"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "  ✗ 未找到 npm，请先安装 npm"
    exit 1
fi

NODE_VERSION=$(node --version)
NPM_VERSION=$(npm --version)
echo "  ✓ Node.js: $NODE_VERSION"
echo "  ✓ npm: $NPM_VERSION"

# 2. 进入前端目录并构建
echo ""
echo "[2/4] 构建前端项目..."
cd "$FRONTEND_DIR" || exit 1

# 检查 node_modules 是否存在
if [ ! -d "node_modules" ]; then
    echo "  检测到未安装依赖，正在安装..."
    npm install
    if [ $? -ne 0 ]; then
        echo "  ✗ 依赖安装失败"
        exit 1
    fi
fi

# 执行构建
echo "  正在构建..."
npm run build

if [ $? -ne 0 ]; then
    echo "  ✗ 构建失败"
    exit 1
fi

echo "  ✓ 构建成功"

# 3. 检查构建产物
echo ""
echo "[3/4] 检查构建产物..."
if [ ! -d "$BUILD_OUTPUT" ]; then
    echo "  ✗ 构建产物不存在: $BUILD_OUTPUT"
    exit 1
fi

FILE_COUNT=$(find "$BUILD_OUTPUT" -type f | wc -l)
echo "  ✓ 找到 $FILE_COUNT 个文件"

# 4. 上传到服务器
echo ""
echo "[4/4] 上传到服务器..."
echo "  服务器: $SERVER_USER@$SERVER_HOST"
echo "  目标路径: $SERVER_PATH"
echo ""

# 使用 scp 上传
scp -r -P "$SERVER_PORT" "$BUILD_OUTPUT"/* "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/"

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "  ✓ 部署成功！"
    echo "========================================"
    echo ""
    echo "  文件已上传到: $SERVER_USER@$SERVER_HOST:$SERVER_PATH"
else
    echo ""
    echo "========================================"
    echo "  ✗ 部署失败"
    echo "========================================"
    echo ""
    echo "  可能的原因："
    echo "  1. SSH 连接失败（检查服务器地址和端口）"
    echo "  2. 未配置 SSH 密钥（需要输入密码或配置密钥）"
    echo "  3. 服务器路径不存在（需要在服务器上创建目录）"
    echo ""
    exit 1
fi

# 返回项目根目录
cd "$SCRIPT_DIR" || exit 1
