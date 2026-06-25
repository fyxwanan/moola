<script setup>
import { AlertCircle, HelpCircle } from 'lucide-vue-next';

const props = defineProps({
  show: { type: Boolean, required: true },
  title: { type: String, default: '提示' },
  message: { type: String, default: '' },
  type: { type: String, default: 'confirm' }, // 'confirm', 'alert', 'danger'
  confirmText: { type: String, default: '确定' },
  cancelText: { type: String, default: '取消' }
});

const emit = defineEmits(['confirm', 'cancel', 'close']);

const handleConfirm = () => {
  emit('confirm');
};

const handleCancel = () => {
  emit('cancel');
  emit('close');
};
</script>

<template>
  <div v-if="show" class="modal-backdrop" @click.self="handleCancel">
    <div class="modal-content confirm-modal-box">
      <div class="confirm-modal-header d-flex align-center gap-12 mb-16">
        <div class="confirm-icon-box" :class="type">
          <AlertCircle v-if="type === 'danger' || type === 'alert'" :size="20" />
          <HelpCircle v-if="type === 'confirm'" :size="20" />
        </div>
        <h3>{{ title }}</h3>
      </div>
      
      <p class="confirm-message mb-24">{{ message }}</p>
      
      <div class="confirm-actions d-flex justify-end gap-12">
        <button 
          v-if="type === 'confirm' || type === 'danger'" 
          type="button" 
          class="btn btn-secondary py-8 px-16" 
          @click="handleCancel"
        >
          {{ cancelText }}
        </button>
        <button 
          type="button" 
          :class="[
            'btn', 
            type === 'danger' ? 'btn-danger' : 'btn-primary',
            'py-8',
            'px-16'
          ]" 
          @click="handleConfirm"
        >
          {{ confirmText }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.confirm-modal-box {
  max-width: 400px;
  border-radius: var(--radius-md);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
  border: 1px solid var(--panel-border);
}

.confirm-modal-header h3 {
  font-size: 18px;
  margin: 0;
}

.confirm-icon-box {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.confirm-icon-box.danger {
  background: rgba(255, 71, 87, 0.1);
  color: var(--danger);
}

.confirm-icon-box.confirm {
  background: rgba(255, 210, 30, 0.15);
  color: var(--warning);
}

.confirm-icon-box.alert {
  background: rgba(255, 210, 30, 0.15);
  color: var(--warning);
}

.confirm-message {
  font-size: 14px;
  color: var(--color-text);
  line-height: 1.6;
}

.py-8 {
  padding-top: 8px !important;
  padding-bottom: 8px !important;
}

.px-16 {
  padding-left: 16px !important;
  padding-right: 16px !important;
}

.justify-end {
  display: flex;
  justify-content: flex-end;
}
</style>
