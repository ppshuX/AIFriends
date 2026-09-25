"""AIFriends Windows 便携包启动入口。

首次运行会自动完成：
1. 生成 .env（两个独立的 >=50 字符随机签名密钥，满足启动校验）
2. 执行数据库迁移；db.sqlite3 不存在时额外导入官方演示角色
3. 用 waitress 在 127.0.0.1:8000 托管整个应用（含前端静态资源与媒体文件）

数据目录策略：
- 若包内 backend/ 可写（解压到任意目录的便携用法），状态直接写在 backend/
- 若不可写（例如安装到 Program Files），改用 %LOCALAPPDATA%\\AIFriends\\
- 也可手动设置环境变量 AIFRIENDS_DATA_DIR 覆盖上述逻辑

用法：
    python run_server.py              # 完整启动并自动打开浏览器
    python run_server.py --no-browser # 启动但不打开浏览器
    python run_server.py --init-only  # 只做首次初始化，不启动服务（构建冒烟用）
"""

import argparse
import os
import secrets
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


def _dir_is_writable(path: Path) -> bool:
    """探测目录是否可写（Program Files 等受保护目录会失败）。"""
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ('.aifriends_write_probe_' + str(os.getpid()))
        probe.write_text('ok', encoding='utf-8')
        probe.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def resolve_data_dir() -> Path:
    """解析可写数据目录：显式覆盖 > 包内 backend > LocalAppData。"""
    override = os.environ.get('AIFRIENDS_DATA_DIR', '').strip()
    if override:
        data = Path(override).expanduser()
        data.mkdir(parents=True, exist_ok=True)
        return data.resolve()

    if _dir_is_writable(BACKEND_DIR):
        return BACKEND_DIR.resolve()

    local_app = os.environ.get('LOCALAPPDATA')
    if not local_app:
        local_app = str(Path.home() / 'AppData' / 'Local')
    data = Path(local_app) / 'AIFriends'
    data.mkdir(parents=True, exist_ok=True)
    return data.resolve()


def apply_data_dir(data_dir: Path) -> None:
    """把数据目录写入环境变量，供 Django settings 在 setup 前读取。"""
    os.environ['AIFRIENDS_DATA_DIR'] = str(data_dir)
    (data_dir / 'media').mkdir(parents=True, exist_ok=True)


def ensure_env(env_file: Path):
    """首次运行时生成本机专属的 .env。

    backend/backend/env.py 要求 DJANGO_SECRET_KEY 与 JWT_SIGNING_KEY 互不相同
    且均不少于 50 个字符，secrets.token_urlsafe(64) 恒满足该约束。
    """
    if env_file.exists():
        return
    log(f'首次运行：正在生成配置文件 {env_file} ...')
    content = ENV_TEMPLATE.format(
        django_secret=secrets.token_urlsafe(64),
        jwt_secret=secrets.token_urlsafe(64),
        host=HOST,
        port=PORT,
    )
    env_file.write_text(content, encoding='utf-8')


def _prepare_django():
    """让嵌入式 Python 能导入 backend.*（._pth 隔离模式下 cwd 不够）。"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    backend = str(BACKEND_DIR)
    if backend not in sys.path:
        sys.path.insert(0, backend)


def run_manage(*args):
    """在进程内执行 manage 命令。

    不能用子进程直接跑 manage.py：嵌入版 Python 的 ._pth 会忽略 PYTHONPATH，
    子进程里找不到名为 backend 的包（ModuleNotFoundError）。
    """
    _prepare_django()
    prev = os.getcwd()
    try:
        os.chdir(BACKEND_DIR)
        import django
        django.setup()
        from django.core.management import call_command

        cmd, *rest = args
        kwargs = {}
        positional = []
        for item in rest:
            if item in ('--noinput', '--no-input'):
                kwargs['interactive'] = False
            elif item.startswith('--'):
                key = item.lstrip('-').replace('-', '_')
                kwargs[key] = True
            else:
                positional.append(item)
        call_command(cmd, *positional, **kwargs)
    finally:
        os.chdir(prev)


def initialize(data_dir: Path):
    env_file = data_dir / '.env'
    db_file = data_dir / 'db.sqlite3'
    ensure_env(env_file)
    fresh_db = not db_file.exists()
    # migrate 幂等：首次建库；用户覆盖升级解压时也能补齐新增迁移
    log('检查数据库迁移 ...')
    run_manage('migrate', '--noinput')
    if fresh_db:
        log('首次运行：导入官方演示角色 ...')
        run_manage('seed_demo_content')


def serve(open_browser):
    _prepare_django()
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
    data_dir = resolve_data_dir()
    apply_data_dir(data_dir)
    log(f'数据目录：{data_dir}')
    initialize(data_dir)
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
            input('\\n按回车键关闭窗口...')
        raise
