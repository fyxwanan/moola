<script setup>
import { ref, watch, computed, nextTick } from 'vue';
import { ElMessage } from 'element-plus';
import {
  ZoomIn, ZoomOut, RotateCw, RefreshCw, Copy, Download,
  ChevronLeft, ChevronRight, X
} from 'lucide-vue-next';

const props = defineProps({
  show: { type: Boolean, required: true },
  images: { type: Array, required: true },
  initialIndex: { type: Number, default: 0 }
});

const emit = defineEmits(['close']);

const currentIndex = ref(0);
const zoom = ref(1);
const rotate = ref(0);
const scaleX = ref(1);
const scaleY = ref(1);

// Drag & Pan position state
const isDragging = ref(false);
const startX = ref(0);
const startY = ref(0);
const translateX = ref(0);
const translateY = ref(0);

// Touch gesture zoom state
const isPinching = ref(false);
const touchDistance = ref(0);
const initialTouchZoom = ref(1);

const reset = () => {
  zoom.value = 1;
  rotate.value = 0;
  scaleX.value = 1;
  scaleY.value = 1;
  translateX.value = 0;
  translateY.value = 0;
};

watch(() => props.show, (newVal) => {
  if (newVal) {
    currentIndex.value = props.initialIndex;
    reset();
    nextTick(() => {
      const backdrop = document.querySelector('.gallery-backdrop');
      if (backdrop) backdrop.focus();
    });
  }
});

// Computed transformation styles (disabling transitions during interactive dragging/pinching)
const imageStyle = computed(() => {
  const isInteracting = isDragging.value || isPinching.value;
  return {
    transform: `translate(${translateX.value}px, ${translateY.value}px) scale(${zoom.value}) rotate(${rotate.value}deg) scaleX(${scaleX.value}) scaleY(${scaleY.value})`,
    transition: isInteracting ? 'none' : 'transform 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
    maxWidth: '100%',
    maxHeight: '70dvh',
    objectFit: 'contain',
    userSelect: 'none',
    cursor: isDragging.value ? 'grabbing' : 'grab'
  };
});

const closeGallery = () => {
  emit('close');
};

const zoomIn = () => {
  if (zoom.value < 5) {
    zoom.value = parseFloat((zoom.value + 0.25).toFixed(2));
  }
};

const zoomOut = () => {
  if (zoom.value > 0.5) {
    zoom.value = parseFloat((zoom.value - 0.25).toFixed(2));
  }
};

const rotateCw = () => {
  rotate.value += 90;
};

const rotateCcw = () => {
  rotate.value -= 90;
};

const flipH = () => {
  scaleX.value = scaleX.value === 1 ? -1 : 1;
};

const flipV = () => {
  scaleY.value = scaleY.value === 1 ? -1 : 1;
};

const prevImage = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--;
    reset();
  }
};

const nextImage = () => {
  if (currentIndex.value < props.images.length - 1) {
    currentIndex.value++;
    reset();
  }
};

// Mouse Wheel Zoom
const handleWheel = (e) => {
  e.preventDefault();
  const step = 0.02; // Reduced from 0.1 for smoother, less sensitive zooming
  const direction = e.deltaY < 0 ? 1 : -1;
  const targetZoom = zoom.value + direction * step;
  zoom.value = Math.max(0.5, Math.min(5, parseFloat(targetZoom.toFixed(2))));
};

// Mouse / Touch Drag Start
const startDrag = (e) => {
  if (e.type === 'touchstart') {
    if (e.touches.length === 1) {
      isDragging.value = true;
      startX.value = e.touches[0].clientX - translateX.value;
      startY.value = e.touches[0].clientY - translateY.value;
    } else if (e.touches.length === 2) {
      // Initiate pinch zoom gesture
      isDragging.value = false;
      isPinching.value = true;
      initialTouchZoom.value = zoom.value;
      touchDistance.value = getTouchDistance(e.touches);
    }
  } else {
    e.preventDefault();
    isDragging.value = true;
    startX.value = e.clientX - translateX.value;
    startY.value = e.clientY - translateY.value;
  }
};

// Mouse / Touch Drag Move
const handleDrag = (e) => {
  if (isDragging.value) {
    if (e.type === 'touchmove' && e.touches.length === 1) {
      translateX.value = e.touches[0].clientX - startX.value;
      translateY.value = e.touches[0].clientY - startY.value;
    } else if (e.type === 'mousemove') {
      e.preventDefault();
      translateX.value = e.clientX - startX.value;
      translateY.value = e.clientY - startY.value;
    }
  } else if (isPinching.value && e.type === 'touchmove' && e.touches.length === 2) {
    e.preventDefault();
    const currentDistance = getTouchDistance(e.touches);
    if (touchDistance.value > 0) {
      const factor = currentDistance / touchDistance.value;
      // Dampen pinch zoom sensitivity by applying a 0.5 multiplier to the change factor
      const targetZoom = initialTouchZoom.value + (factor - 1) * initialTouchZoom.value * 0.5;
      zoom.value = Math.max(0.5, Math.min(5, parseFloat(targetZoom.toFixed(2))));
    }
  }
};

// Drag End
const endDrag = () => {
  isDragging.value = false;
  isPinching.value = false;
};

// Helper for Touch Pinch Distance
const getTouchDistance = (touches) => {
  const dx = touches[0].clientX - touches[1].clientX;
  const dy = touches[0].clientY - touches[1].clientY;
  return Math.sqrt(dx * dx + dy * dy);
};

const copyAddress = async () => {
  const url = props.images[currentIndex.value];
  try {
    await navigator.clipboard.writeText(url);
    ElMessage({
      message: '图片链接已复制到剪贴板',
      type: 'success',
      duration: 2000
    });
  } catch (err) {
    ElMessage.error('复制链接失败，请手动复制');
  }
};

const downloadImage = async () => {
  const url = props.images[currentIndex.value];
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error('Network response was not ok');
    const blob = await res.blob();
    const blobUrl = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = blobUrl;
    const filename = url.split('/').pop() || `record_image_${currentIndex.value + 1}`;
    a.download = filename.includes('.') ? filename : `${filename}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(blobUrl);
    
    ElMessage({
      message: '图片已开始下载',
      type: 'success',
      duration: 2000
    });
  } catch (err) {
    window.open(url, '_blank');
    ElMessage({
      message: '已在新窗口打开图片，请右键选择另存为',
      type: 'info',
      duration: 3000
    });
  }
};
</script>

<template>
  <Transition name="fade">
    <div 
      v-if="show && images.length > 0" 
      class="gallery-backdrop" 
      @click.self="closeGallery" 
      @keydown.esc="closeGallery" 
      @keydown.left="prevImage"
      @keydown.right="nextImage"
      tabindex="0"
    >
      <!-- Close Button (Top Right) -->
      <button class="gallery-close-btn" @click="closeGallery" title="关闭">
        <X :size="24" />
      </button>

      <!-- Main Content Area (Centered Image) -->
      <div 
        class="gallery-main-view" 
        @click.self="closeGallery"
        @wheel="handleWheel"
      >
        <div 
          class="image-transform-container" 
          @mousedown="startDrag"
          @mousemove="handleDrag"
          @mouseup="endDrag"
          @mouseleave="endDrag"
          @touchstart="startDrag"
          @touchmove="handleDrag"
          @touchend="endDrag"
        >
          <img 
            :src="images[currentIndex]" 
            :style="imageStyle" 
            class="gallery-image"
            alt="Preview"
            draggable="false"
          />
        </div>
      </div>

      <!-- Floating Bottom Toolbar -->
      <div class="gallery-toolbar-wrapper">
        <div class="gallery-toolbar">
          <!-- Navigation Section (Prev, Index, Next) -->
          <div class="nav-controls d-flex align-center">
            <button 
              class="toolbar-btn nav-btn" 
              :disabled="currentIndex === 0" 
              @click="prevImage" 
              title="上一张"
            >
              <ChevronLeft :size="20" />
            </button>
            <span class="indicator-text">{{ currentIndex + 1 }} / {{ images.length }}</span>
            <button 
              class="toolbar-btn nav-btn" 
              :disabled="currentIndex === images.length - 1" 
              @click="nextImage" 
              title="下一张"
            >
              <ChevronRight :size="20" />
            </button>
          </div>

          <div class="toolbar-divider"></div>

          <!-- Operations Section -->
          <div class="operation-controls d-flex align-center gap-8">
            <button class="toolbar-btn" @click="zoomIn" :disabled="zoom >= 5" title="放大">
              <ZoomIn :size="18" />
            </button>
            <button class="toolbar-btn" @click="zoomOut" :disabled="zoom <= 0.5" title="缩小">
              <ZoomOut :size="18" />
            </button>
            <button class="toolbar-btn" @click="rotateCcw" title="逆时针旋转 90°">
              <RotateCw :size="18" style="transform: scaleX(-1);" />
            </button>
            <button class="toolbar-btn" @click="rotateCw" title="顺时针旋转 90°">
              <RotateCw :size="18" />
            </button>
            
            <button class="toolbar-btn" @click="flipH" title="左右水平翻转">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="12" x2="12" y1="2" y2="22" stroke-dasharray="4" />
                <path d="M12 4l-8 8 8 8" />
                <path d="M12 4l8 8-8 8" />
              </svg>
            </button>
            <button class="toolbar-btn" @click="flipV" title="上下垂直翻转">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="2" x2="22" y1="12" y2="12" stroke-dasharray="4" />
                <path d="M4 12l8-8 8 8" />
                <path d="M4 12l8 8 8-8" />
              </svg>
            </button>
            <button class="toolbar-btn" @click="reset" title="重置视角">
              <RefreshCw :size="18" />
            </button>
            
            <div class="toolbar-divider"></div>
            
            <button class="toolbar-btn" @click="copyAddress" title="复制图片链接">
              <Copy :size="18" />
            </button>
            <button class="toolbar-btn" @click="downloadImage" title="下载图片">
              <Download :size="18" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.gallery-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(10, 10, 10, 0.95);
  backdrop-filter: blur(8px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 2100;
  outline: none;
}

.gallery-close-btn {
  position: absolute;
  top: 24px;
  right: 24px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #fff;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 2200;
}

.gallery-close-btn:hover {
  background: rgba(255, 71, 87, 0.2);
  border-color: rgba(255, 71, 87, 0.3);
  color: var(--danger);
  transform: rotate(90deg);
}

.gallery-main-view {
  flex-grow: 1;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 80px 24px;
  overflow: hidden;
}

.image-transform-container {
  display: flex;
  align-items: center;
  justify-content: center;
  max-width: 100%;
  max-height: 100%;
  touch-action: none; /* Prevents screen scrolling while dragging or pinching */
}

.gallery-image {
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Floating Bottom Control Bar wrapper */
.gallery-toolbar-wrapper {
  position: absolute;
  bottom: 40px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2200;
  width: auto;
  max-width: 90%;
}

.gallery-toolbar {
  display: flex;
  align-items: center;
  background: rgba(24, 24, 27, 0.85);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 30px;
  padding: 8px 16px;
  gap: 8px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.toolbar-divider {
  width: 1px;
  height: 24px;
  background: rgba(255, 255, 255, 0.15);
  margin: 0 4px;
}

.toolbar-btn {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.toolbar-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
  transform: translateY(-2px);
}

.toolbar-btn:active:not(:disabled) {
  transform: translateY(0);
}

.toolbar-btn:disabled {
  color: rgba(255, 255, 255, 0.25);
  cursor: not-allowed;
}

.nav-controls {
  gap: 4px;
}

.indicator-text {
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  padding: 0 8px;
  min-width: 48px;
  text-align: center;
  user-select: none;
}

/* Slide Fade Transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .gallery-close-btn {
    top: 16px;
    right: 16px;
    width: 36px;
    height: 36px;
  }
  
  .gallery-main-view {
    padding: 60px 12px 140px 12px;
  }
  
  .gallery-toolbar {
    flex-direction: column;
    border-radius: 20px;
    padding: 12px;
    gap: 8px;
    width: 280px;
  }
  
  .toolbar-divider {
    display: none;
  }
  
  .operation-controls {
    flex-wrap: wrap;
    justify-content: center;
    gap: 8px;
  }
  
  .gallery-toolbar-wrapper {
    bottom: 24px;
  }
}
</style>
