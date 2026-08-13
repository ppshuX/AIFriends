from pathlib import Path

from django.contrib.auth.models import User
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.db import transaction

from web.models.character import Character, Voice
from web.models.friend import SystemPrompt
from web.models.user import UserProfile


ASSET_ROOT = Path(__file__).resolve().parents[2] / 'demo_assets'
OFFICIAL_USERNAME = 'aifriends-official'

VOICES = (
    {'name': '智小悟（腾讯云）', 'voice_id': 'tencent:502006'},
    {'name': '智小柔（腾讯云）', 'voice_id': 'tencent:502001'},
    {'name': '智小敏（腾讯云）', 'voice_id': 'tencent:502003'},
    {'name': '暖心阿灿（腾讯云）', 'voice_id': 'tencent:602004'},
)

CHARACTERS = (
    {
        'slug': 'lin-che',
        'name': '林澈',
        'voice_id': 'tencent:502006',
        'profile': (
            '你是林澈，一位冷静、耐心的学习搭档。你擅长把复杂问题拆成清晰步骤，'
            '先确认目标和已有基础，再用例子、提问和小结帮助用户真正理解。你会指出不确定之处，'
            '不会假装掌握不存在的信息，也不会替用户完成作弊性质的任务。'
        ),
    },
    {
        'slug': 'wan-qing',
        'name': '晚晴',
        'voice_id': 'tencent:502001',
        'profile': (
            '你是晚晴，一位温暖、细腻的生活陪伴者。你会先认真倾听和复述用户的感受，'
            '再提供温和、具体、可执行的小建议。你不随意评判，不做医疗或心理诊断；'
            '遇到可能的危机时，会鼓励用户及时联系可信任的人或专业支持。'
        ),
    },
    {
        'slug': 'xing-yao',
        'name': '星遥',
        'voice_id': 'tencent:502003',
        'profile': (
            '你是星遥，一位充满活力的创意搭档。你擅长快速发散点子、寻找意外连接，'
            '也会帮助用户把灵感收敛成可以马上尝试的方案。回答有节奏、有画面感，'
            '但不会用大量空洞口号淹没用户；需要事实依据时会明确区分创意与事实。'
        ),
    },
    {
        'slug': 'yuan-chuan',
        'name': '远川',
        'voice_id': 'tencent:602004',
        'profile': (
            '你是远川，一位沉稳、务实的职业发展教练。你会通过追问目标、约束和优先级，'
            '帮助用户分析选择、准备沟通并制定下一步行动。你尊重用户自己做决定，'
            '不承诺求职或晋升结果，也不会把推测包装成确定结论。'
        ),
    },
)

SYSTEM_PROMPTS = (
    {
        'title': '回复',
        'order_number': 100,
        'prompt': (
            '你正在扮演用户选择的 AI 角色。请始终遵循角色性格，结合对话上下文自然回复。'
            '默认使用简体中文，除非用户明确要求其他语言。回答应真诚、清晰、避免重复；'
            '不要声称自己拥有真实世界中的身体、经历或已经完成未实际执行的操作。\n'
        ),
    },
    {
        'title': '记忆',
        'order_number': 100,
        'prompt': (
            '请根据原始记忆和最近对话更新一段简洁的长期记忆。只保留用户明确表达、'
            '且对未来交流有帮助的稳定偏好、目标和背景；不要保存口令、密钥、身份证件、'
            '精确住址等敏感信息，也不要推断用户未明确说明的敏感属性。只输出更新后的记忆正文。'
        ),
    },
)


class Command(BaseCommand):
    help = '幂等创建 AIFriends 官方演示角色、腾讯云音色和系统提示词'

    def handle(self, *args, **options):
        asset_paths = self._install_assets()

        with transaction.atomic():
            author, created = User.objects.get_or_create(
                username=OFFICIAL_USERNAME,
                defaults={'is_active': False},
            )
            if created:
                author.set_unusable_password()
                author.save(update_fields=['password'])

            profile, _ = UserProfile.objects.update_or_create(
                user=author,
                defaults={
                    'photo': asset_paths['default_avatar'],
                    'profile': 'AIFriends 官方演示角色',
                },
            )

            voices = {}
            for voice_data in VOICES:
                voice, _ = Voice.objects.update_or_create(
                    voice_id=voice_data['voice_id'],
                    defaults={'name': voice_data['name']},
                )
                voices[voice.voice_id] = voice

            for character_data in CHARACTERS:
                slug = character_data['slug']
                Character.objects.update_or_create(
                    author=profile,
                    name=character_data['name'],
                    defaults={
                        'voice': voices[character_data['voice_id']],
                        'profile': character_data['profile'],
                        'photo': asset_paths[f'{slug}_avatar'],
                        'background_image': asset_paths[f'{slug}_background'],
                    },
                )

            for prompt_data in SYSTEM_PROMPTS:
                SystemPrompt.objects.update_or_create(
                    title=prompt_data['title'],
                    order_number=prompt_data['order_number'],
                    defaults={'prompt': prompt_data['prompt']},
                )

        self.stdout.write(self.style.SUCCESS(
            '演示内容已就绪：4 个腾讯云音色、4 个角色、2 条系统提示词。'
        ))

    def _install_assets(self):
        assets = {
            'default_avatar': (
                ASSET_ROOT / 'default-avatar.png',
                'user/photos/default.png',
            ),
        }
        for character in CHARACTERS:
            slug = character['slug']
            assets[f'{slug}_avatar'] = (
                ASSET_ROOT / 'characters' / f'{slug}-avatar.webp',
                f'character/photos/demo/{slug}.webp',
            )
            assets[f'{slug}_background'] = (
                ASSET_ROOT / 'characters' / f'{slug}-background.webp',
                f'character/background_images/demo/{slug}.webp',
            )

        installed = {}
        for key, (source_path, storage_path) in assets.items():
            if not source_path.is_file():
                raise FileNotFoundError(f'演示资源不存在：{source_path}')
            if default_storage.exists(storage_path):
                default_storage.delete(storage_path)
            with source_path.open('rb') as source:
                installed[key] = default_storage.save(
                    storage_path,
                    File(source, name=source_path.name),
                )
        return installed
