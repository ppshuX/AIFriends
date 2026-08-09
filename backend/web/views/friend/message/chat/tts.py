import base64
import hashlib
import hmac
import json
import time
import uuid
from urllib.parse import urlencode

from langchain_core.messages import BaseMessageChunk


TENCENT_TTS_HOST = 'tts.cloud.tencent.com'
TENCENT_TTS_PATH = '/stream_wsv2'


class TencentTTSError(RuntimeError):
    pass


def parse_voice_reference(voice_id):
    if voice_id.startswith('tencent:'):
        return 'tencent', voice_id.removeprefix('tencent:')
    if voice_id.startswith('aliyun:'):
        return 'aliyun', voice_id.removeprefix('aliyun:')
    return 'aliyun', voice_id


def build_tencent_stream_url(
    *,
    app_id,
    secret_id,
    secret_key,
    voice_id,
    session_id,
    timestamp=None,
    expires_in=900,
    speed=1.25,
):
    if not str(voice_id).isdigit():
        raise ValueError('腾讯云预置音色 ID 必须为数字')

    timestamp = int(time.time()) if timestamp is None else int(timestamp)
    params = {
        'Action': 'TextToStreamAudioWSv2',
        'AppId': int(app_id),
        'Codec': 'mp3',
        'EnableSubtitle': False,
        'Expired': timestamp + int(expires_in),
        'SampleRate': 16000,
        'SecretId': secret_id,
        'SessionId': session_id,
        'Speed': speed,
        'Timestamp': timestamp,
        'VoiceType': int(voice_id),
        'Volume': 0,
    }
    canonical_query = '&'.join(
        f'{key}={params[key]}'
        for key in sorted(params)
    )
    sign_source = f'GET{TENCENT_TTS_HOST}{TENCENT_TTS_PATH}?{canonical_query}'
    digest = hmac.new(
        secret_key.encode('utf-8'),
        sign_source.encode('utf-8'),
        hashlib.sha1,
    ).digest()
    params['Signature'] = base64.b64encode(digest).decode('ascii')
    return f'wss://{TENCENT_TTS_HOST}{TENCENT_TTS_PATH}?{urlencode(params)}'


async def wait_for_tencent_ready(ws):
    async for message in ws:
        if isinstance(message, bytes):
            continue
        event = json.loads(message)
        _raise_for_tencent_error(event)
        if event.get('ready') == 1:
            return
    raise TencentTTSError('腾讯云语音连接在 READY 事件前关闭')


async def send_tencent_text(app, inputs, mq, ws, session_id):
    async for message, metadata in app.astream(inputs, stream_mode='messages'):
        if not isinstance(message, BaseMessageChunk) or not message.content:
            continue
        await ws.send(json.dumps({
            'session_id': session_id,
            'message_id': uuid.uuid4().hex,
            'action': 'ACTION_SYNTHESIS',
            'data': message.content,
        }, ensure_ascii=False))
        mq.put_nowait({'content': message.content})
        if getattr(message, 'usage_metadata', None):
            mq.put_nowait({'usage': message.usage_metadata})

    await ws.send(json.dumps({
        'session_id': session_id,
        'message_id': uuid.uuid4().hex,
        'action': 'ACTION_COMPLETE',
        'data': '',
    }))


async def receive_tencent_audio(mq, ws):
    async for message in ws:
        if isinstance(message, bytes):
            audio = base64.b64encode(message).decode('ascii')
            mq.put_nowait({'audio': audio})
            continue

        event = json.loads(message)
        _raise_for_tencent_error(event)
        if event.get('final') == 1:
            return
    raise TencentTTSError('腾讯云语音连接在 FINAL 事件前关闭')


def _raise_for_tencent_error(event):
    code = event.get('code', 0)
    if code != 0:
        message = event.get('message') or '未知错误'
        raise TencentTTSError(f'腾讯云语音合成失败（{code}）：{message}')
