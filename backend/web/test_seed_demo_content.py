import tempfile
from io import StringIO
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from PIL import Image

from web.models.character import Character, Voice
from web.models.friend import SystemPrompt
from web.models.user import UserProfile


class DemoAssetTests(SimpleTestCase):
    def test_character_assets_have_expected_dimensions(self):
        asset_dir = Path(__file__).resolve().parent / 'demo_assets/characters'

        for avatar in asset_dir.glob('*-avatar.webp'):
            with Image.open(avatar) as image:
                self.assertEqual(image.size, (512, 512))
        for background in asset_dir.glob('*-background.webp'):
            with Image.open(background) as image:
                self.assertEqual(image.size, (900, 1500))

        self.assertEqual(len(list(asset_dir.glob('*-avatar.webp'))), 4)
        self.assertEqual(len(list(asset_dir.glob('*-background.webp'))), 4)


class SeedDemoContentTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.settings_override.enable()

    def tearDown(self):
        self.settings_override.disable()
        self.media_dir.cleanup()

    def test_command_is_repeatable_and_restores_demo_content(self):
        call_command('seed_demo_content', stdout=StringIO())
        call_command('seed_demo_content', stdout=StringIO())

        author = User.objects.get(username='aifriends-official')
        self.assertFalse(author.has_usable_password())
        self.assertEqual(
            UserProfile.objects.filter(user=author).count(),
            1,
        )
        self.assertEqual(
            set(Voice.objects.values_list('voice_id', flat=True)),
            {
                'tencent:502006',
                'tencent:502001',
                'tencent:502003',
                'tencent:602004',
            },
        )
        self.assertEqual(
            set(Character.objects.values_list('name', flat=True)),
            {'林澈', '晚晴', '星遥', '远川'},
        )
        self.assertEqual(SystemPrompt.objects.count(), 2)

        default_avatar = Path(self.media_dir.name) / 'user/photos/default.png'
        self.assertTrue(default_avatar.is_file())
        for character in Character.objects.all():
            self.assertTrue(
                (Path(self.media_dir.name) / character.photo.name).is_file()
            )
            self.assertTrue(
                (Path(self.media_dir.name) / character.background_image.name).is_file()
            )
