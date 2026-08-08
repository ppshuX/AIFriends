import importlib
import os
from unittest.mock import patch

from django.test import SimpleTestCase


AI_MODULES = (
    "web.documents.utils.custom_embeddings",
    "web.documents.utils.insert_documents",
    "web.views.friend.message.chat.chat",
    "web.views.friend.message.chat.graph",
    "web.views.friend.message.memory.graph",
    "web.views.create.character.voice.custom.create_voice",
    "web.views.create.character.voice.custom.delete_voice",
    "web.views.create.character.voice.custom.list_voice",
)


class AIIntegrationSmokeTests(SimpleTestCase):
    def test_ai_integration_modules_import_without_remote_calls(self):
        for module_name in AI_MODULES:
            with self.subTest(module=module_name):
                self.assertIsNotNone(importlib.import_module(module_name))

    def test_chat_and_memory_graphs_compile_without_remote_calls(self):
        with patch.dict(
            os.environ,
            {"API_KEY": "test-only-key", "API_BASE": "http://127.0.0.1:9/v1"},
            clear=False,
        ):
            from web.views.friend.message.chat.graph import ChatGraph
            from web.views.friend.message.memory.graph import MemoryGraph

            self.assertIsNotNone(ChatGraph.create_app())
            self.assertIsNotNone(MemoryGraph.create_app())
