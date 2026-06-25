<script setup>
import { ref, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { User, ShieldAlert, Key, LogOut, Mail, Camera } from 'lucide-vue-next';
import AvatarCropper from '../components/AvatarCropper.vue';
import UserAvatar from '../components/UserAvatar.vue';

const router = useRouter();
const authStore = useAuthStore();

const user = computed(() => authStore.user);
const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'; // FastAPI host

const nickname = ref('');
const email = ref('');
const theme = ref('system');
const showCropper = ref(false);

watch(() => authStore.user, (newUser) => {
  if (newUser) {
    nickname.value = newUser.nickname || '';
    email.value = newUser.email || '';
    theme.value = newUser.theme || 'system';
  }
}, { immediate: true });

const newPassword = ref('');
const confirmPassword = ref('');

const profileError = ref('');
const profileSuccess = ref('');
const passwordError = ref('');
const passwordSuccess = ref('');

const updatingProfile = ref(false);
const updatingPassword = ref(false);

const handleUpdateProfile = async () => {
  if (!nickname.value.trim()) {
    profileError.value = '昵称不能为空';
    return;
  }
  
  updatingProfile.value = true;
  profileError.value = '';
  profileSuccess.value = '';
  
  try {
    await authStore.updateProfile({ 
      nickname: nickname.value.trim(),
      email: email.value.trim(),
      theme: theme.value
    });
    profileSuccess.value = '个人信息修改成功！';
  } catch (err) {
    profileError.value = typeof err === 'string' ? err : '修改失败';
  } finally {
    updatingProfile.value = false;
  }
};

const handleUpdatePassword = async () => {
  if (!newPassword.value) {
    passwordError.value = '请输入新密码';
    return;
  }
  
  if (newPassword.value.length < 6) {
    passwordError.value = '密码长度不能少于 6 位';
    return;
  }
  
  if (newPassword.value !== confirmPassword.value) {
    passwordError.value = '两次输入的新密码不一致';
    return;
  }
  
  updatingPassword.value = true;
  passwordError.value = '';
  passwordSuccess.value = '';
  
  try {
    await authStore.updateProfile({ password: newPassword.value });
    passwordSuccess.value = '密码修改成功！';
    newPassword.value = '';
    confirmPassword.value = '';
  } catch (err) {
    passwordError.value = typeof err === 'string' ? err : '修改失败';
  } finally {
    updatingPassword.value = false;
  }
};

const handleAvatarCropped = async (avatarUrl) => {
  showCropper.value = false;
  profileError.value = '';
  profileSuccess.value = '';
  
  try {
    await authStore.updateProfile({ avatar_url: avatarUrl });
    profileSuccess.value = '头像更新成功！';
  } catch (err) {
    profileError.value = '保存头像链接失败，请重试';
  }
};

const handleLogout = async () => {
  await authStore.logout();
  router.push('/login');
};

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
};
</script>

<template>
  <div class="profile-view-container">
    <div class="view-header mb-24">
      <h2 class="view-title">个人信息</h2>
      <p class="text-muted">管理您的账号设置、昵称、邮箱和登录密码</p>
    </div>

    <div class="profile-grid">
      <!-- Left Column: User Summary Card & Nickname/Email settings -->
      <div class="flex-col-gap">
        <div class="glass-card user-large-card text-center">
          <!-- Avatar crop trigger container -->
          <div class="user-big-avatar-container" @click="showCropper = true" title="更换头像">
            <UserAvatar :user="user" :size="88" />
            <div class="avatar-edit-overlay">
              <Camera :size="20" />
            </div>
          </div>
          
          <h3 class="mt-16">{{ user?.nickname }}</h3>
          <p class="text-muted mb-16">@{{ user?.username }}</p>
          
          <div class="user-meta-info text-muted">
            <div>关联邮箱：{{ user?.email || '未绑定' }}</div>
            <div class="mt-8">注册时间：{{ formatDate(user?.created_at) }}</div>
          </div>
          
          <button class="btn btn-danger w-full mt-24 d-flex justify-center align-center" @click="handleLogout" style="width: 100%">
            <LogOut :size="18" />
            <span>退出登录</span>
          </button>
        </div>

        <div class="glass-card">
          <h3 class="card-title mb-24 d-flex align-center gap-8">
            <User :size="18" class="text-primary-hover" />
            <span>基本资料</span>
          </h3>
          
          <el-form label-position="top" @submit.prevent="handleUpdateProfile">
            <el-form-item label="用户名 (不可修改)">
              <el-input :value="user?.username" disabled />
            </el-form-item>

            <el-form-item label="显示昵称" required>
              <el-input 
                v-model="nickname" 
                placeholder="设置您的显示昵称"
                clearable
              />
            </el-form-item>

            <el-form-item label="电子邮箱 (选填)">
              <el-input 
                v-model="email" 
                type="email"
                placeholder="例如: user@example.com" 
                clearable
              />
            </el-form-item>

            <el-form-item label="外观主题">
              <el-select v-model="theme" placeholder="选择系统外观主题" class="w-full" style="width: 100%">
                <el-option label="明亮模式 (Light)" value="light" />
                <el-option label="暗黑模式 (Dark)" value="dark" />
                <el-option label="跟系统一致 (System)" value="system" />
              </el-select>
            </el-form-item>
            
            <div v-if="profileError" class="alert alert-error mb-16">{{ profileError }}</div>
            <div v-if="profileSuccess" class="alert alert-success mb-16">{{ profileSuccess }}</div>

            <el-button type="primary" native-type="submit" class="w-full mt-8" :loading="updatingProfile" style="width: 100%">
              保存资料
            </el-button>
          </el-form>
        </div>
      </div>

      <!-- Right Column: Password updating -->
      <div>
        <div class="glass-card">
          <h3 class="card-title mb-24 d-flex align-center gap-8">
            <Key :size="18" class="text-primary-hover" />
            <span>安全设置</span>
          </h3>
          
          <el-form label-position="top" @submit.prevent="handleUpdatePassword">
            <el-form-item label="新密码" required>
              <el-input 
                v-model="newPassword" 
                type="password" 
                show-password
                placeholder="设置新密码（至少6位）" 
              />
            </el-form-item>

            <el-form-item label="确认新密码" required>
              <el-input 
                v-model="confirmPassword" 
                type="password" 
                show-password
                placeholder="再次输入以确认新密码" 
              />
            </el-form-item>

            <div v-if="passwordError" class="alert alert-error mb-16">{{ passwordError }}</div>
            <div v-if="passwordSuccess" class="alert alert-success mb-16">{{ passwordSuccess }}</div>

            <el-button type="primary" native-type="submit" class="w-full mt-8" :loading="updatingPassword" style="width: 100%">
              修改密码
            </el-button>
          </el-form>
        </div>
      </div>
    </div>

    <!-- Interactive Avatar Cropper Modal -->
    <AvatarCropper 
      :show="showCropper" 
      @close="showCropper = false" 
      @cropped="handleAvatarCropped"
    />
  </div>
</template>

<style scoped>
.profile-view-container {
  max-width: 900px;
  margin: 0 auto;
}

.profile-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.flex-col-gap {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.user-large-card {
  padding: 30px;
}

/* Big avatar with hover camera overlay */
.user-big-avatar-container {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  position: relative;
  margin: 0 auto;
  cursor: pointer;
  border: 4px solid #ffffff;
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
  overflow: hidden;
}

.user-big-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-big-avatar-fallback {
  width: 100%;
  height: 100%;
  background: var(--primary);
  color: var(--primary-text);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 38px;
  font-weight: 800;
}

.avatar-edit-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.user-big-avatar-container:hover .avatar-edit-overlay {
  opacity: 1;
}

.user-meta-info {
  font-size: 13px;
  border-top: 1px solid var(--panel-border);
  padding-top: 16px;
}

.card-title {
  font-size: 18px;
}

.input-control.readonly {
  background: var(--gray-100);
  color: var(--color-text-muted);
  cursor: not-allowed;
  border-style: dashed;
}

.alert {
  padding: 12px;
  border-radius: var(--radius-md);
  font-size: 13px;
  margin-top: 16px;
}

.alert-error {
  background: rgba(255, 71, 87, 0.1);
  border: 1px solid rgba(255, 71, 87, 0.2);
  color: var(--danger);
}

.alert-success {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.2);
  color: var(--success);
}

@media (max-width: 768px) {
  .profile-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
}
</style>
