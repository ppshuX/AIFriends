# 腾讯云流式语音合成接入指南

AIFriends 支持腾讯云“流式文本语音合成”接口，可以将大语言模型逐步生成的文字实时转换为 MP3 音频。现有阿里云音色仍然兼容，不需要迁移已有数据。

## 1. 开通服务

1. 在腾讯云控制台开通[语音合成服务](https://cloud.tencent.com/document/product/1073/94308)。
2. 创建用于服务端调用的 AppID、SecretID 和 SecretKey。
3. 不要使用前端代码、公开日志或 Git 仓库保存 SecretKey。

腾讯云服务器和语音合成是两个独立服务。项目部署在腾讯云服务器上，并不代表语音合成已经自动开通。

## 2. 配置环境变量

在后端 `.env` 或容器环境变量中配置：

```dotenv
TENCENT_TTS_APP_ID=你的数字 AppID
TENCENT_TTS_SECRET_ID=你的 SecretID
TENCENT_TTS_SECRET_KEY=你的 SecretKey
```

Docker 部署时应通过 `--env-file`、Compose 的 `env_file` 或云平台的密钥管理功能注入这些变量，不要把真实值写进镜像或 compose 文件。

大语言模型使用的 `API_KEY`、`API_BASE` 与腾讯云语音配置相互独立。仅配置腾讯云语音密钥，不能同时启用角色对话模型。

## 3. 配置音色

腾讯云预置音色在 `Voice.voice_id` 中使用以下格式：

```text
tencent:<VoiceType>
```

例如：

```text
tencent:502006
```

当前官方音色列表中适合角色聊天的部分音色：

| VoiceType | 音色名称 | 推荐场景 |
| --- | --- | --- |
| `502006` | 智小悟 | 聊天男声 |
| `502003` | 智小敏 | 聊天女声 |
| `602004` | 暖心阿灿 | 聊天男声 |
| `502001` | 智小柔 | 聊天女声 |

完整列表和试听入口见[腾讯云语音合成音色列表](https://cloud.tencent.com/document/product/1073/92668)。音色可用范围和价格可能调整，正式部署前应以腾讯云控制台显示为准。

兼容规则：

- `tencent:502006`：使用腾讯云流式语音合成。
- `aliyun:longanyang`：显式使用阿里云语音合成。
- `longanyang`：作为旧数据继续使用阿里云语音合成。

## 4. 本地验证

先安装后端依赖，再执行：

```powershell
cd backend
python manage.py test web.test_tencent_tts --verbosity 2
```

测试不访问腾讯云，也不需要真实密钥。它会验证：

- 音色提供商路由；
- HMAC-SHA1 签名和 WebSocket 地址；
- READY、FINAL 与错误事件；
- 大模型文本分片发送；
- MP3 二进制分片回传。

真实联调需要开通服务并配置密钥。腾讯云流式接口地址和协议说明见[流式文本语音合成文档](https://cloud.tencent.com/document/product/1073/108595)。

## 5. 当前边界

当前实现支持腾讯云数字 `VoiceType` 预置音色，不支持声音复刻返回的 `FastVoiceType`。声音复刻需要额外的音频采集、授权确认、训练、存储和费用管理，建议在隐私与内容合规流程完善后单独实现。

如果密钥疑似泄露，应立即在腾讯云控制台禁用或删除旧密钥，创建新密钥并更新服务器配置。
