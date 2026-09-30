<script setup>
import SendIcon from "@/components/character/icons/SendIcon.vue";
import MicIcon from "@/components/character/icons/MicIcon.vue";
import {nextTick, onMounted, onUnmounted, ref, useTemplateRef} from "vue";
import streamApi from "@/js/http/streamApi.js";
import api from "@/js/http/api.js";
import Microphone from "@/components/character/chat_field/input_field/Microphone.vue";

const props = defineProps(['friendId'])
const emit = defineEmits(['pushBackMessage', 'addToLastMessage'])
const inputRef = useTemplateRef('input-ref')
const message = ref('')
let processId = 0
const showMic = ref(false)

let mediaSource = null;
let sourceBuffer = null;
let audioPlayer = new Audio(); // 全局播放器实例
let audioQueue = [];           // 待写入 Buffer 的二进制队列
let isUpdating = false;        // Buffer 是否正在写入

const initAudioStream = () => {
    audioPlayer.pause();
    audioQueue = [];
    isUpdating = false;

    mediaSource = new MediaSource();
    audioPlayer.src = URL.createObjectURL(mediaSource);

    mediaSource.addEventListener('sourceopen', () => {
        try {
            sourceBuffer = mediaSource.addSourceBuffer('audio/mpeg');
            sourceBuffer.addEventListener('updateend', () => {
                isUpdating = false;
                processQueue();
            });
        } catch (e) {
            console.error("MSE AddSourceBuffer Error:", e);
        }
    });

    audioPlayer.play().catch(e => console.error("等待用户交互以播放音频"));
};

const processQueue = () => {
    if (isUpdating || audioQueue.length === 0 || !sourceBuffer || sourceBuffer.updating) {
        return;
    }

    isUpdating = true;
    const chunk = audioQueue.shift();
    try {
        sourceBuffer.appendBuffer(chunk);
    } catch (e) {
        console.error("SourceBuffer Append Error:", e);
        isUpdating = false;
    }
};

const stopAudio = () => {
    audioPlayer.pause();
    audioQueue = [];
    isUpdating = false;

    if (mediaSource) {
        if (mediaSource.readyState === 'open') {
            try {
                mediaSource.endOfStream();
            } catch (e) {
            }
        }
        mediaSource = null;
    }

    if (audioPlayer.src) {
        URL.revokeObjectURL(audioPlayer.src);
        audioPlayer.src = '';
    }
};

const handleAudioChunk = (base64Data) => {  // 将语音片段添加到播放器队列中
    try {
        const binaryString = atob(base64Data);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }

        audioQueue.push(bytes);
        processQueue();
    } catch (e) {
        console.error("Base64 Decode Error:", e);
    }
};

onUnmounted(() => {
    audioPlayer.pause();
    audioPlayer.src = '';
    closeApiKeyDialog()
});

function focus() {
  inputRef.value.focus()
}

const DEFAULT_API_BASE = 'https://tokenhub.tencentmaas.com/v1'
const apiKeyDialogRef = useTemplateRef('api-key-dialog')
const apiKeyInputRef = useTemplateRef('api-key-input')
const apiKeyInput = ref('')
const apiBaseInput = ref('')
const apiKeyError = ref('')
const savingApiKey = ref(false)
let apiKeyConfigured = false

function openApiKeyDialog() {
  apiKeyError.value = ''
  const dialog = apiKeyDialogRef.value
  if (dialog && !dialog.open) dialog.showModal()
  nextTick(() => apiKeyInputRef.value?.focus())
}

function closeApiKeyDialog() {
  const dialog = apiKeyDialogRef.value
  if (dialog?.open) dialog.close()
}

let pendingApiKey = null
let statusReady = null

function waitForApiKey() {
  const ready = statusReady || Promise.resolve()
  return ready.then(() => {
    if (apiKeyConfigured) return true
    if (pendingApiKey) return pendingApiKey
    openApiKeyDialog()
    let resolvePromise
    pendingApiKey = new Promise((resolve) => {
      resolvePromise = resolve
    })
    pendingApiKey.resolve = resolvePromise
    return pendingApiKey
  })
}

function settleApiKey(ok) {
  const pending = pendingApiKey
  pendingApiKey = null
  pending?.resolve?.(ok)
}

onMounted(() => {
  statusReady = (async () => {
    try {
      const res = await api.get('/api/config/llm/')
      apiKeyConfigured = !!res.data.api_key_configured
    } catch (err) {
      apiKeyConfigured = false
    }
    if (!apiKeyConfigured) openApiKeyDialog()
  })()
})

async function saveApiKey() {
  const key = apiKeyInput.value.trim()
  if (!key || savingApiKey.value) return
  savingApiKey.value = true
  apiKeyError.value = ''
  try {
    const res = await api.post('/api/config/llm/', {
      api_key: key,
      api_base: apiBaseInput.value.trim(),
    })
    if (res.data.result === 'success' && res.data.api_key_configured) {
      apiKeyInput.value = ''
      apiKeyConfigured = true
      settleApiKey(true)
      closeApiKeyDialog()
      return
    }
    apiKeyError.value = res.data.result || '保存失败'
  } catch (err) {
    apiKeyError.value = err.response?.data?.result || '保存失败，请稍后重试'
  } finally {
    savingApiKey.value = false
  }
}

function cancelApiKey() {
  closeApiKeyDialog()
}

function onApiKeyDialogClose() {
  if (pendingApiKey) settleApiKey(false)
}

async function handleSend(event, audio_msg) {
  let content
  if (audio_msg) {
    content = audio_msg.trim()
  } else {
    content = message.value.trim()
  }
  if (!content) return

  const ready = await waitForApiKey()
  if (!ready) return

  initAudioStream()

  const curId = ++ processId
  message.value = ''

  emit('pushBackMessage', {role: 'user', content: content, id: crypto.randomUUID()})
  emit('pushBackMessage', {role: 'ai', content: '', id: crypto.randomUUID()})

  try {
    await streamApi('/api/friend/message/chat/', {
      body: {
        friend_id: props.friendId,
        message: content,
      },
      onmessage(data, isDone) {
        if (curId !== processId) return

        if (data.content) {
          emit('addToLastMessage', data.content)
        }
        if (data.audio) {
          handleAudioChunk(data.audio)
        }
      },
      onerror(err) {
      },
    })
  } catch (err) {
    if (err?.code === 'api_key_missing') {
      apiKeyConfigured = false
      emit('addToLastMessage', '请先配置 API Key，保存后重新发送。')
      openApiKeyDialog()
    }
  }
}

function close() {
  ++ processId
  showMic.value = false
  stopAudio()
  closeApiKeyDialog()
}

function handleStop() {
  ++ processId
  stopAudio()
}

defineExpose({
  focus,
  close,
})
</script>

<template>
  <form v-if="!showMic" @submit.prevent="handleSend" class="absolute bottom-4 left-2 h-12 w-86 flex items-center">
    <input
        ref="input-ref"
        v-model="message"
        class="input bg-black/30 backdrop-blur-sm text-white text-base w-full h-full rounded-2xl pr-20"
        type="text"
        placeholder="文本输入..."
    >
    <div @click="handleSend" class="absolute right-2 w-8 h-8 flex justify-center items-center cursor-pointer">
      <SendIcon />
    </div>
    <div @click="showMic = true" class="absolute right-10 w-8 h-8 flex justify-center items-center cursor-pointer">
      <MicIcon />
    </div>
  </form>
  <Microphone
      v-else
      @close="showMic = false"
      @send="handleSend"
      @stop="handleStop"
  />
  <Teleport to="body">
    <dialog ref="api-key-dialog" class="modal" @close="onApiKeyDialogClose">
      <div class="modal-box bg-base-100 text-base-content max-w-md">
        <h3 class="text-lg font-bold">配置 API Key</h3>
        <p class="py-2 text-sm leading-6">
          还没有配置大模型 API Key，暂时无法对话。请粘贴 TokenHub 或其他 OpenAI 兼容接口的密钥，保存后即可继续。
        </p>
        <form @submit.prevent="saveApiKey">
          <div class="text-sm mb-1">API Key</div>
          <input
              ref="api-key-input"
              v-model="apiKeyInput"
              type="password"
              autocomplete="off"
              spellcheck="false"
              class="input input-bordered w-full"
              placeholder="粘贴 API Key"
          >
          <div class="text-sm mt-3 mb-1">接口地址（可选）</div>
          <input
              v-model="apiBaseInput"
              type="text"
              autocomplete="off"
              spellcheck="false"
              class="input input-bordered w-full"
              :placeholder="DEFAULT_API_BASE"
          >
          <p v-if="apiKeyError" class="text-error text-sm mt-2">{{ apiKeyError }}</p>
          <div class="modal-action">
            <button type="button" class="btn btn-ghost" @click="cancelApiKey">取消</button>
            <button type="submit" class="btn btn-primary" :disabled="savingApiKey || !apiKeyInput.trim()">
              {{ savingApiKey ? '保存中...' : '保存并继续' }}
            </button>
          </div>
        </form>
      </div>
      <form method="dialog" class="modal-backdrop">
        <button type="submit">关闭</button>
      </form>
    </dialog>
  </Teleport>
</template>

<style scoped>

</style>