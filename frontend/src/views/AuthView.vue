<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';

const router = useRouter();
const authStore = useAuthStore();

const isLoginMode = ref(true);
const username = ref('');
const password = ref('');
const confirmPassword = ref('');
const errorMsg = ref('');
const loading = ref(false);

const toggleMode = () => {
  isLoginMode.value = !isLoginMode.value;
  errorMsg.value = '';
  username.value = '';
  password.value = '';
  confirmPassword.value = '';
};

const handleSubmit = async () => {
  if (!username.value || !password.value || (!isLoginMode.value && !confirmPassword.value)) {
    errorMsg.value = '请填写所有必填字段';
    return;
  }
  
  if (!isLoginMode.value) {
    if (password.value.length < 6) {
      errorMsg.value = '密码长度不能少于 6 位';
      return;
    }
    if (password.value !== confirmPassword.value) {
      errorMsg.value = '两次输入的密码不一致';
      return;
    }
  }
  
  loading.value = true;
  errorMsg.value = '';
  
  try {
    if (isLoginMode.value) {
      await authStore.login(username.value, password.value);
    } else {
      await authStore.register(username.value, password.value, '');
    }
    router.push('/');
  } catch (err) {
    errorMsg.value = err;
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="auth-container">
    <div class="glass-card auth-card">
      <div class="auth-header">
        <div class="logo">💰</div>
        <h2>{{ isLoginMode ? '欢迎回来 Moola' : '开启记账之旅' }}</h2>
        <p class="text-muted">
          {{ isLoginMode ? '精细管理个人及团队财务账单' : '三步建立起你的协作记账账户' }}
        </p>
      </div>

      <el-form label-position="top" @submit.prevent="handleSubmit" class="auth-form">
        <el-form-item label="用户名" required>
          <el-input
            v-model="username"
            placeholder="输入用户名"
            clearable
            autocomplete="username"
          />
        </el-form-item>

        <el-form-item label="密码" required>
          <el-input
            v-model="password"
            type="password"
            show-password
            placeholder="输入密码 (至少6位)"
            autocomplete="new-password"
          />
        </el-form-item>

        <el-form-item v-if="!isLoginMode" label="确认密码" required>
          <el-input
            v-model="confirmPassword"
            type="password"
            show-password
            placeholder="请再次输入密码"
            autocomplete="new-password"
          />
        </el-form-item>

        <div v-if="errorMsg" class="error-alert">
          <span>⚠️</span> {{ errorMsg }}
        </div>

        <el-button type="primary" native-type="submit" class="w-full mt-24" :loading="loading" style="width: 100%;">
          {{ isLoginMode ? '立即登录' : '注册并登录' }}
        </el-button>
      </el-form>
      <div class="auth-toggle text-center mt-24">
        <span>{{ isLoginMode ? '还没有账户？' : '已经有账户？' }}</span>
        <button class="toggle-link" @click="toggleMode">
          {{ isLoginMode ? '创建账户' : '前往登录' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-container {
  min-height: 100vh;
  min-height: 100dvh;
  width: 100vw;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.auth-card {
  width: 100%;
  max-width: 440px;
  padding: 40px;
}

.auth-header {
  text-align: center;
  margin-bottom: 32px;
}

.auth-header .logo {
  font-size: 48px;
  margin-bottom: 12px;
}

.auth-header h2 {
  font-size: 24px;
  margin-bottom: 8px;
}

.error-alert {
  background: rgba(244, 63, 94, 0.15);
  border: 1px solid rgba(244, 63, 94, 0.3);
  padding: 12px;
  border-radius: var(--radius-md);
  color: var(--danger);
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
}

.auth-toggle {
  display: flex;
  justify-content: center;
  gap: 6px;
  font-size: 14px;
}

.toggle-link {
  background: none;
  border: none;
  color: var(--primary);
  font-weight: 600;
  cursor: pointer;
  padding: 0;
  font-family: inherit;
}

.toggle-link:hover {
  text-decoration: underline;
}

.w-full {
  width: 100%;
}

.mt-24 {
  margin-top: 24px;
}

.text-center {
  text-align: center;
}
</style>
