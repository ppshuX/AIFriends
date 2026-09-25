#Requires -Version 5.1
<#
.SYNOPSIS
  组装 AIFriends Windows 便携发布包，并（可选）编译 Inno Setup 安装包。

.DESCRIPTION
  产出一个解压即用的 ZIP 包，内含：
  - 嵌入式 Python 3.12（embed 发行版，用户机器无需安装 Python）
  - 全部后端依赖（pip --target 安装进包内 site-packages）
  - Django 后端源码（含 Vite 构建好的前端产物 backend/static/frontend/）
  - start.bat 双击入口、run_server.py 初始化逻辑、README.txt 说明

  若本机已安装 Inno Setup 6（ISCC.exe），会额外产出同版本的 .exe 安装包
  （选择安装目录、开始菜单快捷方式、可选桌面快捷方式、可卸载）。

  前置条件：
  1. 已在 frontend/ 下执行 npm run build（产物写入 backend/static/frontend/）；
  2. 构建机已安装 Python 3.12 并可运行 python -m pip（用于把依赖装进包内）；
  3. 建议用 PowerShell 7（pwsh）运行，避免旧版 Compress-Archive 的限制；
  4. CI 发布需先安装 Inno Setup（choco install innosetup -y）。

.EXAMPLE
  pwsh -File scripts/release/build-portable.ps1 -Version v1.0.0
#>
[CmdletBinding()]
param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
    [string]$WorkDir = '',
    [string]$PythonVersion = '3.12.10',
    [string]$Version = 'dev',
    [switch]$SkipInstaller
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
    # Django 项目包在 ..\backend\backend；加入后 import backend 才能解析
    '..\backend'
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

# ---------- 7. Inno Setup 安装包 ----------
# 与 ZIP 共用同一 $PkgRoot，保证安装后的文件布局与便携包一致。
$ExePath = $null
if (-not $SkipInstaller) {
    Step '查找 Inno Setup 编译器 (ISCC.exe)...'
    $IsccCandidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
        "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
    )
    $Iscc = $IsccCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1

    if (-not $Iscc) {
        if ($env:GITHUB_ACTIONS -eq 'true') {
            throw '未找到 ISCC.exe。请在 workflow 中先执行 choco install innosetup -y。'
        }
        Write-Host '未找到 ISCC.exe，跳过安装包编译（本地可用 -SkipInstaller 显式跳过）。' -ForegroundColor Yellow
    } else {
        # VersionInfoVersion 需要纯数字 x.y.z[.w]；从 tag 去掉前缀 v 与后缀 -smoke 等。
        $VersionInfo = ($Version -replace '^v', '') -replace '-.*$', ''
        if ($VersionInfo -notmatch '^\d+(\.\d+){1,3}$') {
            $VersionInfo = '0.0.0'
        }

        $IssFile = Join-Path $PSScriptRoot 'aifriends.iss'
        if (-not (Test-Path $IssFile)) {
            throw "未找到 Inno 脚本：$IssFile"
        }

        Step "用 Inno Setup 编译安装包（AppVersion=$Version, VersionInfo=$VersionInfo）..."
        # 路径用正斜杠，避免 Inno 预处理器把 \t \n 等当成转义。
        $SourceDirDef = ($PkgRoot -replace '\\', '/')
        $OutputDirDef = ($WorkDir -replace '\\', '/')
        & $Iscc `
            "/DMyAppVersion=$Version" `
            "/DMyAppVersionInfo=$VersionInfo" `
            "/DSourceDir=$SourceDirDef" `
            "/DOutputDir=$OutputDirDef" `
            $IssFile
        if ($LASTEXITCODE -ne 0) { throw "ISCC 编译失败（退出码 $LASTEXITCODE）" }

        $ExePath = Join-Path $WorkDir "$PkgName-setup.exe"
        if (-not (Test-Path $ExePath)) {
            throw "ISCC 未产出预期安装包：$ExePath"
        }
        $ExeSize = (Get-Item $ExePath).Length
        if ($ExeSize -lt 1MB) {
            throw "安装包过小（$ExeSize bytes），疑似编译异常"
        }
        $ExeSizeMB = [math]::Round($ExeSize / 1MB)
        Step "安装包完成：$ExePath（$ExeSizeMB MB）"

        Write-Host "EXE_PATH=$ExePath"
        if ($env:GITHUB_OUTPUT) {
            Add-Content -Path $env:GITHUB_OUTPUT -Value "exe-path=$ExePath"
        }
    }
}