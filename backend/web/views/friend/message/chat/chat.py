import json

from django.http import StreamingHttpResponse
from langchain_core.messages import AIMessage, BaseMessageChunk, HumanMessage, SystemMessage
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BaseRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from web.models.friend import Friend, Message, SystemPrompt
from web.views.friend.message.chat.graph import ChatGraph
from web.views.friend.message.memory.graph import update_memory


class SSERenderer(BaseRenderer):
    media_type = "text/event-stream"
    format = "txt"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data

def add_System_prompt(state, friend):
    msgs = state['messages']
    system_prompts = SystemPrompt.objects.filter(title='回复').order_by('old_number')
    prompt = ''
    for sp in system_prompts:
        prompt += sp.prompt
    prompt += f'\n【角色性格】\n{friend.character.profile}\n'
    prompt += f'\n【长期记忆】\n{friend.memory}\n'
    return {'messages': [SystemMessage(prompt)] + msgs}

def add_recent_message(state, friend):
    msgs = state['messages']
    message_raw = list(Message.objects.filter(friend=friend).order_by("-id")[:10])
    message_raw.reverse()
    history = []
    for m in message_raw:
        history.append(HumanMessage(m.user_message))
        history.append(AIMessage(m.output))
    return {'messages': msgs[:1] + history + msgs[1:]}


class MessageChatView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [SSERenderer]

    def post(self, request):
        friend_id = request.data.get("friend_id")
        raw_message = request.data.get("message", "")
        if friend_id is None:
            return Response({"result": "缺少 friend_id"})
        message = str(raw_message).strip()
        if not message:
            return Response({"result": "消息不能为空"})

        friends = Friend.objects.filter(pk=friend_id, me__user=request.user)
        if not friends.exists():
            return Response({"result": "好友不存在"})

        friend = friends.first()
        app = ChatGraph.create_app()
        inputs = {"messages": [HumanMessage(message)]}

        inputs = add_System_prompt(inputs, friend)
        inputs = add_recent_message(inputs, friend)

        def event_stream():
            full_output = ""
            full_usage = {}
            for msg, metadata in app.stream(inputs, stream_mode="messages"):
                _ = metadata
                if isinstance(msg, BaseMessageChunk):
                    if msg.content:
                        full_output += msg.content
                        payload = json.dumps({"content": msg.content}, ensure_ascii=False)
                        yield f"data: {payload}\n\n"
                    if hasattr(msg, "usage_metadata") and msg.usage_metadata:
                        full_usage = msg.usage_metadata

            yield "data: [DONE]\n\n"

            Message.objects.create(
                friend=friend,
                user_message=message[:500],
                input=json.dumps([m.model_dump() for m in inputs["messages"]], ensure_ascii=False)[:10000],
                output=full_output[:500],
                input_tokens=full_usage.get("input_tokens", 0),
                output_tokens=full_usage.get("output_tokens", 0),
                total_tokens=full_usage.get("total_tokens", 0),
            )
            if Message.objects.filter(friend=friend).count() % 1 == 0:
                update_memory(friend)

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        return response