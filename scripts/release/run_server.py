"""AIFriends Windows 便携包启动入口。

首次运行会自动完成：
1. 生成 backend/.env（两个独立的 >=50 字符随机签名密钥，满足启动校验）
2. 执行数据库迁移；db.sqlite3 不存在时额外导入官方演示角色
3. 用 waitress 在 127.0.0.1:8000 托管整个应用（含前端静态资源与媒体文件）

用法：
    python run_server.py              # 完整启动并自动打开浏览器
    python run_server.py --no-browser # 启动但不打开浏览器
    python run_server.py --init-only  # 只做首次初始化，不启动服务（构建冒烟用）
"""

import argparse
import os
import secrets
import subprocess
import sys
import threading
import traceback
import webbrowser
from pathlib import Path

HOST = '127.0.0.1'
PORT = 8000
THREADS = 8
HOME_URL = f'http://{HOST}:{PORT}/'

PKG_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PKG_ROOT / 'backend'
ENV_FILE = BACKEND_DIR / '.env'
DB_FILE = BACKEND_DIR / 'db.sqlite3'

# 注意：本模板用 str.format 注入占位符，除命名占位符外不要出现裸花括号。
ENV_TEMPLATE = """\
# AIFriends 本地运行配置（首次启动自动生成）
# 下面两个签名密钥由本机随机生成，仅用于本地演示，请勿分享或提交。
DJANGO_SECRET_KEY={django_secret}
JWT_SIGNING_KEY={jwt_secret}

# 本地演示模式：Django 直接托管前端静态资源与媒体文件，不要用于公网。
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS={host},localhost
DJANGO_CORS_ALLOWED_ORIGINS=http://{host}:{port}

# ===== 以下为 AI 功能配置（可选）=====
# 腾讯云 TokenHub（OpenAI 兼容）：填入 API_KEY 后即可开启角色对话与长期记忆
API_BASE=https://tokenhub.tencentmaas.com/v1
API_KEY=
# 阿里云 DashScope 实时语音识别（ASR）WebSocket 地址，开启语音输入时需要
WSS_URL=
VOICE_URL=
# 腾讯云流式语音合成（TTS）：角色音色为 tencent:<VoiceType> 时需要
TENCENT_TTS_APP_ID=
TENCENT_TTS_SECRET_ID=
TENCENT_TTS_SECRET_KEY=
"""


def log(message):
    print(f'[AIFriends] {message}', flush=True)


def ensure_env():
    """首次运行时生成本机专属的 .env。

    backend/backend/env.py 要求 DJANGO_SECRET_KEY 与 JWT_SIGNING_KEY 互不相同
    且均不少于 50 个字符，secrets.token_urlsafe(64) 恒满足该约束。
    """
    if ENV_FILE.exists():
        return
    log('首次运行：正在生成配置文件 backend/.env ...')
    content = ENV_TEMPLATE.format(
        django_secret=secrets.token_urlsafe(64),
        jwt_secret=secrets.token_urlsafe(64),
        host=HOST,
        port=PORT,
    )
    ENV_FILE.write_text(content, encoding='utf-8')


def run_manage(*args):
    result = subprocess.run(
        [sys.executable, 'manage.py', *args],
        cwd=BACKEND_DIR,
    )
    if result.returncode != 0:
        raise RuntimeError(f'manage.py {" ".join(args)} 失败，退出码 {result.returncode}')


def initialize():
    ensure_env()
    fresh_db = not DB_FILE.exists()
    # migrate 幂等：首次建库；用户覆盖升级解压时也能补齐新增迁移
    log('检查数据库迁移 ...')
    run_manage('migrate', '--noinput')
    if fresh_db:
        log('首次运行：导入官方演示角色 ...')
        run_manage('seed_demo_content')


def serve(open_browser):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    sys.path.insert(0, str(BACKEND_DIR))
    # 项目内多处使用相对路径（如 LanceDB 的 ./web/documents/lancedb_storage），
    # 约定进程工作目录与“在 backend 目录下运行”保持一致。
    os.chdir(BACKEND_DIR)
    from django.core.wsgi import get_wsgi_application
    from waitress import serve as waitress_serve

    application = get_wsgi_application()
    if open_browser:
        threading.Timer(2.5, lambda: webbrowser.open(HOME_URL)).start()
    log(f'服务已启动：{HOME_URL}（直接关闭本窗口即可停止服务）')
    waitress_serve(application, host=HOST, port=PORT, threads=THREADS)


def main():
    # Windows 下输出被重定向时默认使用本地代码页（GBK），统一切到 UTF-8
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(description='AIFriends 本地服务')
    parser.add_argument('--init-only', action='store_true',
                        help='只执行初始化，不启动服务')
    parser.add_argument('--no-browser', action='store_true',
                        help='启动服务但不自动打开浏览器')
    args = parser.parse_args()

    log('正在准备运行环境 ...')
    initialize()
    if args.init_only:
        log('初始化完成（--init-only）')
        return
    serve(open_browser=not args.no_browser)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log('已停止。')
    except Exception:
        traceback.print_exc()
        # 双击运行出错时留住窗口，方便看到错误信息
        if sys.stdin is not None and sys.stdin.isatty():
            input('\n按回车键关闭窗口...')
        raise
