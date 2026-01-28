from django.urls import path
from .views.index import index
from .views.user.account.get_user_info import GetUserInfo
from .views.user.account.logout import LogoutView
from .views.user.account.login import Login
from .views.user.account.register import Register
from .views.user.account.refresh_token import RefreshTokenView

urlpatterns = [
    path("api/user/account/login/", Login.as_view()),
    path("api/user/account/logout/", LogoutView.as_view()),
    path("api/user/account/register/", Register.as_view()),
    path("api/user/account/refresh_token/", RefreshTokenView.as_view()),
    path("api/user/account/get_user_info/", GetUserInfo.as_view()),
    path("", index, name="index"),
]
