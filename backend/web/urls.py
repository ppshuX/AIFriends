from django.urls import path, re_path

from .views.create.character.create import CreateCharacterView
from .views.create.character.get_single import GetSingleCharacterView
from .views.create.character.remove import RemoveCharacterView
from .views.create.character.update import UpdateCharacterView
from .views.index import index
from .views.user.account.get_user_info import GetUserInfo
from .views.user.account.logout import LogoutView
from .views.user.account.login import Login
from .views.user.account.register import Register
from .views.user.account.refresh_token import RefreshTokenView
from .views.user.profile.update import UpdateProfile

urlpatterns = [
    path("api/user/account/login/", Login.as_view()),
    path("api/user/account/logout/", LogoutView.as_view()),
    path("api/user/account/register/", Register.as_view()),
    path("api/user/account/refresh_token/", RefreshTokenView.as_view()),
    path("api/user/account/get_user_info/", GetUserInfo.as_view()),

    path('api/create/character/create/', CreateCharacterView.as_view()),
    path('api/create/character/update/', UpdateCharacterView.as_view()),
    path('api/create/character/remove/', RemoveCharacterView.as_view()),
    path('api/create/character/get_single/', GetSingleCharacterView.as_view()),
    path("", index, name="index"),
    path('api/user/profile/update/', UpdateProfile.as_view()),
    # 前端 history 模式：除 media/static/assets 外的任意路径都交给前端路由
    re_path(r"^(?!media/|static/|assets/).*$", index),
]
