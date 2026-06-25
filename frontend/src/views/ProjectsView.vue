<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '../api';
import { useAuthStore } from '../stores/auth';
import { Plus, FolderKanban, Users, Crown, ChevronRight } from 'lucide-vue-next';

const router = useRouter();
const authStore = useAuthStore();
const currentUserId = authStore.user?.id;

const projects = ref([]);
const loading = ref(false);
const showCreateModal = ref(false);

// Form
const formName = ref('');
const formDescription = ref('');
const errorMsg = ref('');
const submitting = ref(false);

const fetchProjects = async () => {
  loading.value = true;
  try {
    const response = await api.get('/projects');
    projects.value = response.data;
  } catch (err) {
    console.error('Error fetching projects:', err);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchProjects();
});

const handleCreate = async () => {
  if (!formName.value.trim()) {
    errorMsg.value = '项目名称不能为空';
    return;
  }
  
  submitting.value = true;
  errorMsg.value = '';
  
  try {
    const response = await api.post('/projects', {
      name: formName.value.trim(),
      description: formDescription.value.trim()
    });
    
    projects.value.unshift(response.data);
    showCreateModal.value = false;
    
    // Reset Form
    formName.value = '';
    formDescription.value = '';
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || '创建项目失败';
  } finally {
    submitting.value = false;
  }
};

const goToProject = (id) => {
  router.push(`/projects/${id}`);
};
</script>

<template>
  <div class="projects-view-container">
    <div class="shayu-view-header mb-24">
      <div>
        <h2 class="view-title">项目记账</h2>
        <p class="text-muted">与您的朋友、家人或同事共同管理多账套协同记账项目</p>
      </div>
      <button class="btn btn-primary create-project-btn" @click="showCreateModal = true">
        <Plus :size="18" />
        <span>创建新项目</span>
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>正在加载项目套账...</p>
    </div>

    <div v-else>
      <div v-if="projects.length === 0" class="empty-state glass-card text-center text-muted">
        <FolderKanban :size="48" class="mb-16 text-muted" style="opacity: 0.5" />
        <p class="mb-16">您还没有参与任何共享记账项目</p>
        <button class="btn btn-primary" @click="showCreateModal = true">
          立即创建共享项目
        </button>
      </div>

      <div v-else class="projects-grid">
        <div 
          v-for="project in projects" 
          :key="project.id" 
          class="glass-card project-card interactive" 
          @click="goToProject(project.id)"
        >
          <div class="project-header d-flex justify-between align-start mb-16">
            <div class="project-icon-box">
              <FolderKanban :size="24" class="text-primary" />
            </div>
            
            <span v-if="project.owner_id === currentUserId" class="badge-owner">
              <Crown :size="12" />
              <span>所有者</span>
            </span>
            <span v-else class="badge-member">
              成员
            </span>
          </div>

          <h3 class="project-name mb-8">{{ project.name }}</h3>
          <p class="project-desc text-muted mb-24">{{ project.description || '暂无描述' }}</p>

          <div class="project-footer d-flex justify-between align-center">
            <div class="members-count d-flex align-center gap-8 text-muted">
              <Users :size="16" />
              <span>{{ project.members?.length || 0 }} 名成员</span>
            </div>
            
            <div class="go-arrow">
              <ChevronRight :size="18" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Project Modal -->
    <div v-if="showCreateModal" class="modal-backdrop" @click.self="showCreateModal = false">
      <div class="modal-content">
        <h3 class="mb-24">新建协作记账项目</h3>
        
        <form @submit.prevent="handleCreate">
          <div class="form-group">
            <label for="p-name">项目名称</label>
            <el-input 
              id="p-name" 
              v-model="formName" 
              placeholder="如：家庭日常、合租账单、毕业旅行" 
              maxlength="50"
              clearable
            />
          </div>

          <div class="form-group">
            <label for="p-desc">项目描述 (选填)</label>
            <el-input 
              id="p-desc" 
              v-model="formDescription" 
              type="textarea"
              placeholder="简要说明此项目的记账用途..."
              :rows="3"
              maxlength="200"
              show-word-limit
            />
          </div>

          <div v-if="errorMsg" class="error-msg-text mb-16">{{ errorMsg }}</div>

          <div class="d-flex justify-between mt-24 gap-16">
            <el-button class="flex-1" @click="showCreateModal = false">取消</el-button>
            <el-button type="primary" class="flex-1" native-type="submit" :loading="submitting">
              确认创建
            </el-button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.projects-view-container {
  max-width: 1000px;
  margin: 0 auto;
}

.view-title {
  font-size: 28px;
  margin-bottom: 4px;
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

.empty-state {
  padding: 80px 40px;
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.project-card {
  padding: 24px;
  border-radius: var(--radius-lg);
  cursor: pointer;
}

.project-icon-box {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  background: rgba(99, 102, 241, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
}

.badge-owner {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: rgba(245, 158, 11, 0.15);
  color: var(--warning);
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 700;
}

.badge-member {
  display: inline-flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.08);
  color: var(--color-text-muted);
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.project-name {
  font-size: 18px;
}

.project-desc {
  font-size: 14px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  height: 40px;
}

.go-arrow {
  color: var(--color-text-muted);
  transition: transform var(--transition-fast);
}

.project-card:hover .go-arrow {
  transform: translateX(4px);
  color: var(--primary);
}

.error-msg-text {
  color: var(--danger);
  font-size: 13px;
  text-align: center;
}

.flex-1 {
  flex: 1;
}

textarea.input-control {
  resize: vertical;
}

@media (max-width: 768px) {
  .projects-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
}
</style>
