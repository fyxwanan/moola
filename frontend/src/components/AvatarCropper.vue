<script setup>
import { ref, reactive, computed, onBeforeUnmount } from 'vue';
import api from '../api';
import { X, Upload } from 'lucide-vue-next';

const props = defineProps({
  show: Boolean
});

const emit = defineEmits(['cropped', 'close']);

const fileInput = ref(null);
const sourceImage = ref(null);
const imageSrc = ref('');
const imageLoaded = ref(false);
const errorMsg = ref('');
const uploading = ref(false);

// Crop box bounding state (pixels)
const cropBox = reactive({
  x: 0,
  y: 0,
  size: 150
});

// Layout sizes
const containerWidth = ref(300);
const containerHeight = ref(300);
const naturalWidth = ref(0);
const naturalHeight = ref(0);

// Drag gestures
const isDragging = ref(false);
const isResizing = ref(false);
const dragStart = reactive({ x: 0, y: 0 });
const boxStart = reactive({ x: 0, y: 0, size: 150 });

const onFileChange = (e) => {
  const file = e.target.files[0];
  if (!file) return;
  if (!file.type.startsWith('image/')) {
    errorMsg.value = '请选择合法的图片文件';
    return;
  }
  
  errorMsg.value = '';
  const reader = new FileReader();
  reader.onload = (event) => {
    imageSrc.value = event.target.result;
    imageLoaded.value = false;
  };
  reader.readAsDataURL(file);
};

const triggerFileSelect = () => {
  fileInput.value.click();
};

const onImageLoad = (e) => {
  const img = e.target;
  naturalWidth.value = img.naturalWidth;
  naturalHeight.value = img.naturalHeight;
  
  const rect = img.getBoundingClientRect();
  containerWidth.value = rect.width;
  containerHeight.value = rect.height;
  
  // Square crop box setup (starts at 60% of minimum dimension)
  const initialSize = Math.min(rect.width, rect.height) * 0.6;
  cropBox.size = initialSize;
  cropBox.x = (rect.width - initialSize) / 2;
  cropBox.y = (rect.height - initialSize) / 2;
  
  imageLoaded.value = true;
};

// Drag cropbox positioning
const startDrag = (e) => {
  if (isResizing.value) return;
  isDragging.value = true;
  dragStart.x = e.clientX;
  dragStart.y = e.clientY;
  boxStart.x = cropBox.x;
  boxStart.y = cropBox.y;
  
  window.addEventListener('mousemove', onDrag);
  window.addEventListener('mouseup', stopDrag);
};

const onDrag = (e) => {
  if (!isDragging.value) return;
  const dx = e.clientX - dragStart.x;
  const dy = e.clientY - dragStart.y;
  
  let newX = boxStart.x + dx;
  let newY = boxStart.y + dy;
  
  // Boundary collisions
  newX = Math.max(0, Math.min(newX, containerWidth.value - cropBox.size));
  newY = Math.max(0, Math.min(newY, containerHeight.value - cropBox.size));
  
  cropBox.x = newX;
  cropBox.y = newY;
};

const stopDrag = () => {
  isDragging.value = false;
  window.removeEventListener('mousemove', onDrag);
  window.removeEventListener('mouseup', stopDrag);
};

// Resize cropbox dimension (uniform scale)
const startResize = (e) => {
  e.stopPropagation();
  isResizing.value = true;
  dragStart.x = e.clientX;
  dragStart.y = e.clientY;
  boxStart.size = cropBox.size;
  boxStart.x = cropBox.x;
  boxStart.y = cropBox.y;
  
  window.addEventListener('mousemove', onResize);
  window.addEventListener('mouseup', stopResize);
};

const onResize = (e) => {
  if (!isResizing.value) return;
  const dx = e.clientX - dragStart.x;
  
  let newSize = boxStart.size + dx;
  const maxSize = Math.min(
    containerWidth.value - boxStart.x,
    containerHeight.value - boxStart.y
  );
  
  newSize = Math.max(60, Math.min(newSize, maxSize));
  cropBox.size = newSize;
};

const stopResize = () => {
  isResizing.value = false;
  window.removeEventListener('mousemove', onResize);
  window.removeEventListener('mouseup', stopResize);
};

// Dynamic Circular Preview computed offsets
const previewStyle = computed(() => {
  return {
    width: '100px',
    height: '100px',
    borderRadius: '50%',
    overflow: 'hidden',
    position: 'relative',
    border: '3px solid var(--primary)',
    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
    backgroundColor: '#e2e8f0',
    flexShrink: 0
  };
});

const previewImgStyle = computed(() => {
  if (!imageLoaded.value) return {};
  const scale = 100 / cropBox.size;
  return {
    position: 'absolute',
    left: `-${cropBox.x * scale}px`,
    top: `-${cropBox.y * scale}px`,
    width: `${containerWidth.value * scale}px`,
    height: `${containerHeight.value * scale}px`,
    maxWidth: 'none',
    maxHeight: 'none'
  };
});

const handleCropAndUpload = async () => {
  if (!imageLoaded.value || !sourceImage.value) return;
  uploading.value = true;
  errorMsg.value = '';
  
  try {
    const scaleX = naturalWidth.value / containerWidth.value;
    const scaleY = naturalHeight.value / containerHeight.value;
    
    const cropX = cropBox.x * scaleX;
    const cropY = cropBox.y * scaleY;
    const cropSize = cropBox.size * Math.max(scaleX, scaleY);
    
    const canvas = document.createElement('canvas');
    canvas.width = 150;
    canvas.height = 150;
    const ctx = canvas.getContext('2d');
    
    ctx.drawImage(
      sourceImage.value,
      cropX, cropY, cropSize, cropSize,
      0, 0, 150, 150
    );
    
    const blob = await new Promise((resolve) => {
      canvas.toBlob((b) => resolve(b), 'image/jpeg', 0.9);
    });
    
    const formData = new FormData();
    formData.append('file', blob, 'avatar.jpg');
    
    const response = await api.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    
    emit('cropped', response.data.url);
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || '头像裁剪上传失败';
  } finally {
    uploading.value = false;
  }
};

onBeforeUnmount(() => {
  window.removeEventListener('mousemove', onDrag);
  window.removeEventListener('mouseup', stopDrag);
  window.removeEventListener('mousemove', onResize);
  window.removeEventListener('mouseup', stopResize);
});
</script>

<template>
  <div v-if="show" class="modal-backdrop" @click.self="emit('close')">
    <div class="modal-content avatar-cropper-content">
      <div class="modal-header d-flex justify-between align-center mb-16">
        <h3>修改头像</h3>
        <button class="close-btn" @click="emit('close')"><X :size="18" /></button>
      </div>

      <div class="cropper-body">
        <!-- 1. Drop zone / file selector -->
        <div v-if="!imageSrc" class="upload-dropzone" @click="triggerFileSelect">
          <Upload :size="36" class="text-muted mb-8" />
          <p>点击选择要上传的头像图片</p>
          <span class="text-muted" style="font-size: 11px;">支持 JPG、PNG 等格式图片</span>
        </div>

        <input 
          ref="fileInput" 
          type="file" 
          accept="image/*" 
          style="display: none" 
          @change="onFileChange"
        />

        <div v-if="imageSrc" class="crop-workspace-container">
          <!-- 2. Draggable and resizable workspace -->
          <div class="crop-area-wrapper">
            <img 
              ref="sourceImage" 
              :src="imageSrc" 
              class="crop-source-image" 
              @load="onImageLoad"
            />
            
            <div 
              v-if="imageLoaded"
              class="crop-overlay-box"
              :style="{
                left: `${cropBox.x}px`,
                top: `${cropBox.y}px`,
                width: `${cropBox.size}px`,
                height: `${cropBox.size}px`
              }"
              @mousedown="startDrag"
            >
              <!-- Circular dashed boundary inside square crop box -->
              <div class="crop-inner-circle"></div>
              <!-- Resize handle bottom right -->
              <div class="resize-handle" @mousedown="startResize"></div>
            </div>
          </div>

          <!-- 3. Circular Preview Pane -->
          <div class="crop-preview-pane">
            <h4 class="text-muted mb-8">圆形预览</h4>
            <div :style="previewStyle">
              <img v-if="imageLoaded" :src="imageSrc" :style="previewImgStyle" />
            </div>
          </div>
        </div>
      </div>

      <div v-if="errorMsg" class="error-msg-text mt-16 mb-8">{{ errorMsg }}</div>

      <div class="d-flex justify-between mt-24 gap-16">
        <button type="button" class="btn btn-secondary flex-1" @click="emit('close')">取消</button>
        <button 
          v-if="imageSrc"
          type="button" 
          class="btn btn-primary flex-1" 
          :disabled="!imageLoaded || uploading"
          @click="handleCropAndUpload"
        >
          {{ uploading ? '正在保存...' : '保存修改' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.avatar-cropper-content {
  max-width: 520px;
}

.close-btn {
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 4px;
}

.upload-dropzone {
  border: 2px dashed var(--panel-border);
  border-radius: var(--radius-md);
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: var(--transition-fast);
  background: var(--gray-100);
}
.upload-dropzone:hover {
  border-color: var(--primary-hover);
  background: var(--gray-200);
}

.crop-workspace-container {
  display: flex;
  gap: 20px;
  align-items: center;
  justify-content: center;
  margin-top: 12px;
}

.crop-area-wrapper {
  position: relative;
  max-width: 300px;
  max-height: 300px;
  background: #000;
  border-radius: var(--radius-md);
  overflow: hidden;
  user-select: none;
}

.crop-source-image {
  display: block;
  max-width: 300px;
  max-height: 300px;
  width: auto;
  height: auto;
}

.crop-overlay-box {
  position: absolute;
  border: 2px solid var(--primary);
  background: rgba(0, 0, 0, 0.35);
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.5); /* Dim area outside crop box */
  cursor: move;
}

.crop-inner-circle {
  width: 100%;
  height: 100%;
  border: 1px dashed rgba(255, 255, 255, 0.6);
  border-radius: 50%;
  pointer-events: none;
}

.resize-handle {
  position: absolute;
  right: -5px;
  bottom: -5px;
  width: 14px;
  height: 14px;
  background: var(--primary);
  border: 2px solid white;
  border-radius: 50%;
  cursor: se-resize;
  box-shadow: 0 2px 6px rgba(0,0,0,0.2);
}

.crop-preview-pane {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.crop-preview-pane h4 {
  font-size: 12px;
  font-weight: 700;
}

.flex-1 {
  flex: 1;
}

@media (max-width: 768px) {
  .crop-workspace-container {
    flex-direction: column;
    gap: 16px;
  }
}
</style>
