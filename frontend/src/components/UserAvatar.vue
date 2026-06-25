<script setup>
import { computed } from 'vue';

const props = defineProps({
  user: {
    type: Object,
    default: null
  },
  size: {
    type: [Number, String],
    default: 40
  }
});

const getApiBase = () => {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  if (import.meta.env.PROD) {
    return '';
  }
  const hostname = window.location.hostname;
  return `http://${hostname}:8000`;
};
const apiBase = getApiBase();

const avatarUrl = computed(() => {
  if (props.user && props.user.avatar_url) {
    if (props.user.avatar_url.startsWith('http')) {
      return props.user.avatar_url;
    }
    return `${apiBase}${props.user.avatar_url}`;
  }
  return null;
});

const fallbackInfo = computed(() => {
  const name = props.user?.nickname || props.user?.username || props.user?.email || '?';
  const char = name.trim().charAt(0);
  
  const isChinese = /^[\u4e00-\u9fa5]$/.test(char);
  const isEnglish = /^[a-zA-Z]$/.test(char);
  
  let bgColor = '#a5b1c2'; // fallback background for other characters
  let label = char.toUpperCase();
  
  if (isChinese) {
    bgColor = '#ff9f43'; // warm orange-gold for Chinese characters
  } else if (isEnglish) {
    bgColor = '#54a0ff'; // soft blue for English letters (uppercase)
  }
  
  return {
    text: label,
    bgColor
  };
});
</script>

<template>
  <div 
    class="user-avatar-circle"
    :style="{
      width: size + 'px',
      height: size + 'px',
      fontSize: (size * 0.45) + 'px',
      backgroundColor: avatarUrl ? 'transparent' : fallbackInfo.bgColor
    }"
  >
    <img 
      v-if="avatarUrl" 
      :src="avatarUrl" 
      alt="avatar" 
      class="user-avatar-image"
    />
    <span v-else class="user-avatar-text">
      {{ fallbackInfo.text }}
    </span>
  </div>
</template>

<style scoped>
.user-avatar-circle {
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  user-select: none;
  font-weight: 700;
  color: #ffffff;
  flex-shrink: 0;
}

.user-avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-avatar-text {
  line-height: 1;
}
</style>
