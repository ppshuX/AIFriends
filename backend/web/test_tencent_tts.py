import asyncio
import json
from queue import Queue
from unittest.mock import AsyncMock
from urllib.parse import parse_qs, urlparse

from django.test import SimpleTestCase
from langchain_core.messages import AIMessageChunk

from web.views.friend.message.chat.chat import MessageChatView
from web.views.friend.message.chat.tts import (
    TencentTTSError,
    build_tencent_stream_url,
    parse_voice_reference,
    receive_tencent_audio,
    send_tencent_text,
    wait_for_tencent_ready,
)


class VoiceReferenceTests(SimpleTestCase):
    def test_tencent_prefix_selects_tencent_provider(self):
        self.assertEqual(
            parse_voice_reference('tencent:502006'),
            ('tencent', '502006'),
        )

    def test_legacy_voice_id_keeps_aliyun_provider(self):
        self.assertEqual(
            parse_voice_reference('longanyang'),
            ('aliyun', 'longanyang'),
        )


class TencentStreamUrlTests(SimpleTestCase):
    def test_builds_signed_streaming_url(self):
        url = build_tencent_stream_url(
            app_id='123456',
            secret_id='test-secret-id',
            secret_key='test-secret-key',
            voice_id='502006',
            session_id='session-123',
            timestamp=1700000000,
            expires_in=900,
            speed=1.25,
        )

        parsed = urlparse(url)
        query = parse_qs(parsed.query)

        self.assertEqual(parsed.scheme, 'wss')
        self.assertEqual(parsed.netloc, 'tts.cloud.tencent.com')
        self.assertEqual(parsed.path, '/stream_wsv2')
        self.assertEqual(query['Action'], ['TextToStreamAudioWSv2'])
        self.assertEqual(query['VoiceType'], ['502006'])
        self.assertEqual(query['Signature'], ['/hIkcnnMzaKxvAKG7Ao+Lw4BCgw='])

    def test_rejects_non_numeric_builtin_voice_id(self):
        with self.assertRaisesRegex(ValueError, '数字'):
            build_tencent_stream_url(
                app_id='123456',
                secret_id='test-secret-id',
                secret_key='test-secret-key',
                voice_id='not-a-number',
                session_id='session-123',
                timestamp=1700000000,
            )


class FakeWebSocket:
    def __init__(self, incoming=()):
        self.incoming = iter(incoming)
        self.sent = []

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.incoming)
        except StopIteration as exc:
            raise StopAsyncIteration from exc

    async def send(self, message):
        self.sent.append(json.loads(message))


class FakeChatApp:
    async def astream(self, inputs, stream_mode):
        self.inputs = inputs
        self.stream_mode = stream_mode
        yield AIMessageChunk(content='你好。'), {}
        yield AIMessageChunk(content='今天过得怎么样？'), {}


class TencentStreamingProtocolTests(SimpleTestCase):
    def test_waits_for_ready_event(self):
        ws = FakeWebSocket([
            json.dumps({'code': 0, 'ready': 0}),
            json.dumps({'code': 0, 'ready': 1}),
        ])

        asyncio.run(wait_for_tencent_ready(ws))

    def test_ready_error_raises_tencent_error(self):
        ws = FakeWebSocket([
            json.dumps({'code': 10003, 'message': '鉴权失败'}),
        ])

        with self.assertRaisesRegex(TencentTTSError, '鉴权失败'):
            asyncio.run(wait_for_tencent_ready(ws))

    def test_sends_llm_chunks_then_complete_instruction(self):
        ws = FakeWebSocket()
        mq = Queue()

        asyncio.run(send_tencent_text(
            FakeChatApp(),
            {'messages': []},
            mq,
            ws,
            'session-123',
        ))

        self.assertEqual(
            [message['action'] for message in ws.sent],
            ['ACTION_SYNTHESIS', 'ACTION_SYNTHESIS', 'ACTION_COMPLETE'],
        )
        self.assertEqual(ws.sent[0]['data'], '你好。')
        self.assertEqual(ws.sent[1]['data'], '今天过得怎么样？')
        self.assertEqual(mq.get_nowait(), {'content': '你好。'})
        self.assertEqual(mq.get_nowait(), {'content': '今天过得怎么样？'})

    def test_receives_audio_until_final_event(self):
        ws = FakeWebSocket([
            b'first-audio-chunk',
            json.dumps({'code': 0, 'heartbeat': 1, 'final': 0}),
            b'second-audio-chunk',
            json.dumps({'code': 0, 'final': 1}),
        ])
        mq = Queue()

        asyncio.run(receive_tencent_audio(mq, ws))

        self.assertEqual(
            mq.get_nowait(),
            {'audio': 'Zmlyc3QtYXVkaW8tY2h1bms='},
        )
        self.assertEqual(
            mq.get_nowait(),
            {'audio': 'c2Vjb25kLWF1ZGlvLWNodW5r'},
        )


class TTSProviderRoutingTests(SimpleTestCase):
    def test_tencent_voice_uses_tencent_stream(self):
        view = MessageChatView()
        view.run_aliyun_tts_tasks = AsyncMock()
        view.run_tencent_tts_tasks = AsyncMock()

        asyncio.run(view.run_tts_tasks(
            'app',
            'inputs',
            'queue',
            'tencent:502006',
        ))

        view.run_tencent_tts_tasks.assert_awaited_once_with(
            'app',
            'inputs',
            'queue',
            '502006',
        )
        view.run_aliyun_tts_tasks.assert_not_awaited()

    def test_legacy_voice_uses_aliyun_stream(self):
        view = MessageChatView()
        view.run_aliyun_tts_tasks = AsyncMock()
        view.run_tencent_tts_tasks = AsyncMock()

        asyncio.run(view.run_tts_tasks(
            'app',
            'inputs',
            'queue',
            'longanyang',
        ))

        view.run_aliyun_tts_tasks.assert_awaited_once_with(
            'app',
            'inputs',
            'queue',
            'longanyang',
        )
        view.run_tencent_tts_tasks.assert_not_awaited()
