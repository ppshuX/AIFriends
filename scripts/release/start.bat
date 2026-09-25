@echo off
chcp 65001 >nul
title AIFriends
pushd "%~dp0"
".\python\python.exe" ".\run_server.py"
if errorlevel 1 (
    echo.
    echo 启动遇到错误。请截取上方信息反馈给项目维护者。
    pause
)
popd
