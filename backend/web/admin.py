from django.contrib import admin
from .models.character import Character
from .models.user import UserProfile

# Register your models here.
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    raw_id_fields = ('user', )


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    raw_id_fields = ('author', )