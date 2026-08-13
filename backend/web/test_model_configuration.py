from unittest.mock import patch

from django.test import SimpleTestCase

from web.views.friend.message.chat.graph import ChatGraph
from web.views.friend.message.memory.graph import MemoryGraph


TOKENHUB_MODEL = 'deepseek-v4-flash-202605'


class TokenHubModelConfigurationTests(SimpleTestCase):
    @patch('web.views.friend.message.chat.graph.ChatOpenAI')
    def test_chat_uses_active_tokenhub_model(self, chat_openai):
        chat_openai.return_value.bind_tools.return_value = object()

        ChatGraph.create_app()

        self.assertEqual(
            chat_openai.call_args.kwargs['model'],
            TOKENHUB_MODEL,
        )

    @patch('web.views.friend.message.memory.graph.ChatOpenAI')
    def test_memory_uses_active_tokenhub_model(self, chat_openai):
        MemoryGraph.create_app()

        self.assertEqual(
            chat_openai.call_args.kwargs['model'],
            TOKENHUB_MODEL,
        )
