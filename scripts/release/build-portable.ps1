#Requires -Version 5.1
<#
.SYNOPSIS
  组装 AIFriends Windows 便携发布包。

.DESCRIPTION
  产出一个解压即用的 ZIP 包，内含：
  - 嵌入式 Python 3.12（embed 发行版，用户机器无需安装 Python）
  - 全部后端依赖（pip --target 安装进包内 site-packages）
  - Django 后端源码（含 Vite 构建好的前端产物 backend/static/frontend/）
  - start.bat 双击入口、run_server.py 初始化逻辑、README.txt 说明

  前置条件：
  1. 已在 frontend/ 下执行 npm run build（产物写入 backend/static/frontend/）；
  2. 构建机已安装 Python 3.12 并可运行 python -m pip（用于把依赖装进包内）；
  3. 建议用 PowerShell 7（pwsh）运行，避免旧版 Compress-Archive 的限制。

.EXAMPLE
  pwsh -File scripts/release/build-portable.ps1 -Version v1.0.0
#>
[CmdletBinding()]
param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
    [string]$WorkDir = '',
    [string]$PythonVersion = '3.12.10',
    [string]$Version = 'dev'
)

$ErrorActionPreference = 'Stop'

if (-not $WorkDir) {
    $WorkDir = Join-Path $env:TEMP ("AIFriends-portable-{0}" -f (Get-Date -Format 'yyyyMMddHHmmss'))
}
$PkgName = "AIFriends-windows-x64-$Version"
$PkgRoot = Join-Path $WorkDir $PkgName

function Step($Message) { Write-Host "==> $Message" -ForegroundColor Cyan }

# ---------- 0. 前置检查 ----------
$BackendDir = Join-Path $ProjectRoot 'backend'
$FrontendIndex = Join-Path $BackendDir 'static\frontend\index.html'

Step '检查前端构建产物...'
if (-not (Test-Path $FrontendIndex)) {
    throw "未找到 $FrontendIndex。请先在 frontend/ 下执行 npm run build。"
}

# ---------- 1. 工作目录 ----------
Step '创建工作目录...'
if (Test-Path $WorkDir) { Remove-Item $WorkDir -Recurse -Force }
New-Item -ItemType Directory -Path $PkgRoot -Force | Out-Null

# ---------- 2. 嵌入式 Python ----------
# 嵌入版（embed）是官方提供的可重定位 Python：解压即用、不依赖注册表。
# 依赖中的 pyarrow/lancedb/onnxruntime 等只有平台 wheel，
# 因此整个组装必须在 Windows 上完成（无法从 Linux 交叉打包）。
$PyMinor = ($PythonVersion.Split('.')[0..1] -join '')   # 3.12.10 -> 312
Step "下载 Python $PythonVersion 嵌入版 (amd64)..."
$PythonZip = Join-Path $WorkDir 'python-embed.zip'
$PythonUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"
Invoke-WebRequest -Uri $PythonUrl -OutFile $PythonZip
$PythonDir = Join-Path $PkgRoot 'python'
Expand-Archive -Path $PythonZip -Destination $PythonDir -Force

# 嵌入版默认处于 ._pth 完全隔离模式，需要解锁包内 site-packages 才能导入第三方包。
Step '配置嵌入式 Python...'
$PthFile = Join-Path $PythonDir "python$PyMinor`._pth"
@(
    "python$PyMinor.zip"
    '.'
    'Lib\site-packages'
    'import site'
) | Set-Content -Path $PthFile -Encoding ascii

# ---------- 3. 依赖 ----------
# --target 模式：只把包落到指定目录，不污染构建机环境，也不生成 Scripts 入口
# （发布包用自己的 run_server.py 启动，不需要 pip 生成的脚本）。
Step '安装后端依赖到包内（约需几分钟）...'
$SitePackages = Join-Path $PythonDir 'Lib\site-packages'
python -m pip install --disable-pip-version-check --no-warn-script-location `
    --target $SitePackages -r (Join-Path $BackendDir 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw '安装 requirements.txt 依赖失败' }

# WSGI 服务器：uWSGI 没有 Windows 版，改用纯 Python 实现的 waitress。
python -m pip install --disable-pip-version-check --no-warn-script-location `
    --target $SitePackages waitress
if ($LASTEXITCODE -ne 0) { throw '安装 waitress 失败' }

# ---------- 4. 后端源码与前端产物 ----------
Step '复制后端源码与前端产物...'
$PkgBackend = Join-Path $PkgRoot 'backend'
robocopy $BackendDir $PkgBackend /E /NFL /NDL /NJH /NJS /NP `
    /XD __pycache__ .venv venv staticfiles .git `
    /XF db.sqlite3 .env .env.example *.pyc | Out-Null
# robocopy 退出码 0-7 都表示成功（1 = 有文件被复制），>=8 才是失败。
if ($LASTEXITCODE -ge 8) { throw "复制后端源码失败（robocopy 退出码 $LASTEXITCODE）" }
$global:LASTEXITCODE = 0

# ---------- 5. 启动器与说明 ----------
Step '写入启动脚本与说明文件...'
Copy-Item (Join-Path $PSScriptRoot 'run_server.py') $PkgRoot
Copy-Item (Join-Path $PSScriptRoot 'start.bat') $PkgRoot
Copy-Item (Join-Path $PSScriptRoot 'README-portable.md') (Join-Path $PkgRoot 'README.txt')

# ---------- 6. 压缩 ----------
Step '压缩发布包（约需几分钟）...'
$ZipPath = Join-Path $WorkDir "$PkgName.zip"
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
# 传入目录本身，让 ZIP 内保留顶层目录 AIFriends-windows-x64-<version>/
Compress-Archive -Path $PkgRoot -DestinationPath $ZipPath -CompressionLevel Fastest

$SizeMB = [math]::Round((Get-Item $ZipPath).Length / 1MB)
Step "完成：$ZipPath（$SizeMB MB）"

Write-Host "ZIP_PATH=$ZipPath"
if ($env:GITHUB_OUTPUT) {
    Add-Content -Path $env:GITHUB_OUTPUT -Value "zip-path=$ZipPath"
}
