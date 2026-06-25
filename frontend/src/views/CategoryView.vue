<script setup>
import { ref, onMounted, computed } from 'vue';
import api from '../api';
import ConfirmModal from '../components/ConfirmModal.vue';
import * as LucideIcons from 'lucide-vue-next';
import { Plus, Trash2, HelpCircle } from 'lucide-vue-next';

// Reusable Confirm Modal State
const confirmModal = ref({
  show: false,
  title: '提示',
  message: '',
  type: 'confirm', // 'confirm', 'alert', 'danger'
  onConfirm: null,
  onCancel: null
});

const triggerConfirm = (options) => {
  confirmModal.value = {
    show: true,
    title: options.title || '提示',
    message: options.message || '',
    type: options.type || 'confirm',
    onConfirm: () => {
      confirmModal.value.show = false;
      if (options.onConfirm) options.onConfirm();
    },
    onCancel: () => {
      confirmModal.value.show = false;
      if (options.onCancel) options.onCancel();
    }
  };
};

const triggerAlert = (message, title = '提示', callback = null) => {
  confirmModal.value = {
    show: true,
    title,
    message,
    type: 'alert',
    onConfirm: () => {
      confirmModal.value.show = false;
      if (callback) callback();
    },
    onCancel: () => {
      confirmModal.value.show = false;
      if (callback) callback();
    }
  };
};

// Available icons to pick
const availableIcons = [
  'Utensils', 'Coffee', 'Pizza', 'Beer', 'Wine', 'Apple', 'ShoppingBag',
  'Shirt', 'Crown', 'Gem', 'Gift', 'Car', 'Plane', 'Bike', 'Bus', 'Train',
  'Compass', 'Gamepad2', 'Tv', 'Camera', 'Music', 'Smile', 'Heart', 'Home',
  'Droplet', 'Zap', 'Flame', 'Wifi', 'Scissors', 'HeartPulse', 'Stethoscope',
  'Pills', 'Baby', 'Cat', 'Dog', 'Briefcase', 'GraduationCap', 'BookOpen',
  'Award', 'TrendingUp', 'Wallet', 'Banknote', 'Coins', 'CreditCard', 'PiggyBank',
  'Settings', 'Key', 'Percent', 'Sparkles', 'Umbrella', 'HelpCircle'
];

// Available colors to pick
const availableColors = [
  '#EF4444', '#EC4899', '#3B82F6', '#8B5CF6', '#F59E0B', 
  '#06B6D4', '#10B981', '#6366F1', '#EC4899', '#6B7280'
];

const categories = ref([]);
const loading = ref(false);
const showAddModal = ref(false);

// Form fields
const formName = ref('');
const formType = ref('expense');
const formIcon = ref('HelpCircle');
const formColor = ref('#6366F1');
const errorMsg = ref('');
const submitting = ref(false);

const fetchCategories = async () => {
  loading.value = true;
  try {
    const response = await api.get('/categories');
    categories.value = response.data;
  } catch (err) {
    console.error('Error fetching categories:', err);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchCategories();
});

const systemCategories = computed(() => categories.value.filter(c => c.owner_id === null));
const customCategories = computed(() => categories.value.filter(c => c.owner_id !== null));

const handleCreate = async () => {
  if (!formName.value.trim()) {
    errorMsg.value = '分类名称不能为空';
    return;
  }
  
  submitting.value = true;
  errorMsg.value = '';
  
  try {
    const response = await api.post('/categories', {
      name: formName.value.trim(),
      type: formType.value,
      icon: formIcon.value,
      color: formColor.value
    });
    
    categories.value.push(response.data);
    showAddModal.value = false;
    
    // Reset form
    formName.value = '';
    formType.value = 'expense';
    formIcon.value = 'HelpCircle';
    formColor.value = '#6366F1';
  } catch (err) {
    errorMsg.value = typeof err === 'string' ? err : (err.response?.data?.detail || '创建分类失败');
  } finally {
    submitting.value = false;
  }
};

const handleDelete = (id) => {
  triggerConfirm({
    title: '确认删除分类',
    message: '确定要删除这个自定义分类吗？关联的账单可能仍保留该分类 ID。',
    type: 'danger',
    onConfirm: async () => {
      try {
        await api.delete(`/categories/${id}`);
        categories.value = categories.value.filter(c => c.id !== id);
      } catch (err) {
        triggerAlert(err.response?.data?.detail || '删除分类失败', '错误');
      }
    }
  });
};

const getIconComponent = (iconName) => {
  return LucideIcons[iconName] || HelpCircle;
};
</script>

<template>
  <div class="category-view-container">
    <div class="view-header d-flex justify-between align-center mb-24">
      <div>
        <h2 class="view-title">分类管理</h2>
        <p class="text-muted">管理您的记账类别，包含预置类别和自定义类别</p>
      </div>
      <button class="btn btn-primary header-add-btn" @click="showAddModal = true">
        <Plus :size="18" />
        <span>添加自定义分类</span>
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>正在加载分类列表...</p>
    </div>

    <div v-else class="categories-grid">
      <!-- Custom User Categories Section -->
      <section class="category-section mb-24">
        <div class="category-section-header">
          <h3 class="section-title">我的自定义分类 ({{ customCategories.length }})</h3>
          <button class="btn btn-primary section-add-btn" @click="showAddModal = true" title="添加自定义分类">
            <Plus :size="16" />
            <span>添加自定义分类</span>
          </button>
        </div>
        <div class="cards-wrapper">
          <div v-if="customCategories.length === 0" class="empty-card glass-card text-center text-muted">
            您还没有创建自定义分类，点击右上角按钮添加一个吧！
          </div>
          
          <div v-else class="badges-grid">
            <div 
              v-for="cat in customCategories" 
              :key="cat.id" 
              class="glass-card category-item-card"
              :style="{ borderLeft: `4px solid ${cat.color}`, '--border-color': cat.color }"
            >
              <div class="d-flex align-center gap-16">
                <div class="icon-circle" :style="{ backgroundColor: `${cat.color}20`, color: cat.color }">
                  <component :is="getIconComponent(cat.icon)" :size="20" />
                </div>
                <div>
                  <div class="category-name font-semibold">{{ cat.name }}</div>
                  <div class="category-type text-muted">{{ cat.type === 'expense' ? '支出' : '收入' }}</div>
                </div>
              </div>
              <button class="btn-delete" @click="handleDelete(cat.id)" title="删除分类">
                <Trash2 :size="16" />
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Prebuilt Categories Section -->
      <section class="category-section">
        <h3 class="section-title">系统默认分类 ({{ systemCategories.length }})</h3>
        <div class="badges-grid">
          <div 
            v-for="cat in systemCategories" 
            :key="cat.id" 
            class="glass-card category-item-card system-category"
            :style="{ borderLeft: `4px solid ${cat.color}`, '--border-color': cat.color }"
          >
            <div class="d-flex align-center gap-16">
              <div class="icon-circle" :style="{ backgroundColor: `${cat.color}15`, color: cat.color }">
                <component :is="getIconComponent(cat.icon)" :size="20" />
              </div>
              <div>
                <div class="category-name font-semibold">{{ cat.name }}</div>
                <div class="category-type text-muted">{{ cat.type === 'expense' ? '支出' : '收入' }}</div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- Add Category Modal -->
    <div v-if="showAddModal" class="modal-backdrop" @click.self="showAddModal = false">
      <div class="modal-content">
        <h3 class="mb-24">新建自定义分类</h3>
        
        <form @submit.prevent="handleCreate">
          <div class="form-group">
            <label for="name">分类名称</label>
            <el-input 
              id="name" 
              v-model="formName" 
              placeholder="例如：宠物、送礼等" 
              maxlength="15"
              clearable
            />
          </div>

          <div class="form-group">
            <label>分类类型</label>
            <div class="radio-group-tabs">
              <button 
                type="button" 
                class="tab-btn" 
                :class="{ active: formType === 'expense' }"
                @click="formType = 'expense'"
              >
                支出分类
              </button>
              <button 
                type="button" 
                class="tab-btn" 
                :class="{ active: formType === 'income' }"
                @click="formType = 'income'"
              >
                收入分类
              </button>
            </div>
          </div>

          <div class="form-group">
            <label>选择图标</label>
            <div class="icons-picker">
              <button 
                v-for="iconName in availableIcons" 
                :key="iconName"
                type="button"
                class="picker-icon-btn"
                :class="{ active: formIcon === iconName }"
                :style="formIcon === iconName ? { backgroundColor: formColor + '30', borderColor: formColor, color: formColor } : {}"
                @click="formIcon = iconName"
              >
                <component :is="getIconComponent(iconName)" :size="18" />
              </button>
            </div>
          </div>

          <div class="form-group">
            <label>选择颜色</label>
            <div class="colors-picker">
              <button 
                v-for="color in availableColors" 
                :key="color"
                type="button"
                class="picker-color-btn"
                :class="{ active: formColor === color }"
                :style="{ backgroundColor: color, border: formColor === color ? '3px solid white' : 'none' }"
                @click="formColor = color"
              ></button>
            </div>
          </div>

          <div v-if="errorMsg" class="error-msg-text mb-16">{{ errorMsg }}</div>

          <div class="d-flex justify-between mt-24 gap-16">
            <el-button class="flex-1" @click="showAddModal = false">取消</el-button>
            <el-button type="primary" class="flex-1" native-type="submit" :loading="submitting">
              确认创建
            </el-button>
          </div>
        </form>
      </div>
    </div>
    <!-- Reusable Confirm Modal -->
    <ConfirmModal
      :show="confirmModal.show"
      :title="confirmModal.title"
      :message="confirmModal.message"
      :type="confirmModal.type"
      @confirm="confirmModal.onConfirm"
      @cancel="confirmModal.onCancel"
    />
  </div>
</template>

<style scoped>
.category-view-container {
  max-width: 1000px;
  margin: 0 auto;
}

.view-title {
  font-size: 28px;
  margin-bottom: 4px;
}

.category-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.category-section-header .section-title {
  margin-bottom: 0;
}

.section-title {
  font-size: 16px;
  color: var(--color-text-muted);
  margin-bottom: 16px;
}

.section-add-btn {
  display: none;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.1);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 1s infinite linear;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.badges-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

.category-item-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-radius: var(--radius-md);
}

.icon-circle {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.category-name {
  font-size: 15px;
}

.category-type {
  font-size: 11px;
}

.btn-delete {
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  transition: var(--transition-fast);
}

.btn-delete:hover {
  background: rgba(244, 63, 94, 0.15);
  color: var(--danger);
}

.system-category {
  opacity: 0.85;
}

/* Modals inputs */
.radio-group-tabs {
  display: flex;
  background: rgba(255, 255, 255, 0.05);
  border-radius: var(--radius-md);
  padding: 4px;
  border: 1px solid var(--panel-border);
}

.tab-btn {
  flex: 1;
  background: none;
  border: none;
  color: var(--color-text-muted);
  font-family: inherit;
  font-weight: 600;
  padding: 10px;
  border-radius: calc(var(--radius-md) - 4px);
  cursor: pointer;
  transition: var(--transition-fast);
}

.tab-btn.active {
  background: var(--primary);
  color: white;
  box-shadow: 0 4px 10px var(--primary-glow);
}

.icons-picker {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 10px;
  max-height: 160px;
  overflow-y: auto;
  padding: 4px;
}

.picker-icon-btn {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--panel-border);
  color: var(--color-text-muted);
  height: 44px;
  border-radius: var(--radius-md);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition-fast);
}

.picker-icon-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--color-text);
}

.picker-icon-btn.active {
  border-width: 2px;
}

.colors-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.picker-color-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
  transition: var(--transition-fast);
}

.picker-color-btn:hover {
  transform: scale(1.15);
}

.error-msg-text {
  color: var(--danger);
  font-size: 13px;
  text-align: center;
}

.flex-1 {
  flex: 1;
}

.empty-card {
  padding: 40px;
  border-radius: var(--radius-md);
}

@media (max-width: 768px) {
  .view-header {
    display: block;
    margin-bottom: 16px;
  }

  .header-add-btn {
    display: none !important;
  }

  .category-section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    width: 100%;
  }

  .section-add-btn {
    display: inline-flex !important;
    padding: 0;
    border-radius: 50%;
    width: 32px;
    height: 32px;
    min-width: 32px;
    align-items: center;
    justify-content: center;
  }

  .section-add-btn span {
    display: none !important;
  }

  .badges-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  /* Centered vertical layout for category cards on mobile */
  .category-item-card {
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    position: relative;
    padding: 16px 8px !important;
    gap: 8px !important;
    border-left: none !important;
    border-top: 4px solid var(--border-color, #ffd21e) !important;
  }

  .category-item-card .d-flex {
    flex-direction: column !important;
    align-items: center !important;
    gap: 8px !important;
  }

  .category-item-card .category-name {
    font-size: 14px;
    font-weight: 700;
  }

  .category-item-card .category-type {
    font-size: 11px;
    margin-top: 2px;
  }

  .category-item-card .btn-delete {
    position: absolute !important;
    top: 4px;
    right: 4px;
    padding: 4px;
    border-radius: 50%;
    background: rgba(254, 226, 226, 0.8) !important;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  /* Compact Modal overrides for mobile H5 */
  .modal-content {
    max-height: 85vh;
    overflow-y: auto;
    padding: 16px 20px;
  }

  .form-group {
    margin-bottom: 12px;
  }

  .icons-picker {
    grid-template-columns: repeat(6, 1fr);
    gap: 8px;
    max-height: 110px;
  }

  .picker-icon-btn {
    height: 36px;
    border-radius: var(--radius-sm);
  }

  .colors-picker {
    gap: 8px;
  }

  .picker-color-btn {
    width: 22px;
    height: 22px;
  }
}
</style>
