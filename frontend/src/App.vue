<script setup>
import { onMounted, onUnmounted, computed, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from './stores/auth';
import { 
  LayoutDashboard, 
  Wallet, 
  FolderKanban, 
  Tags, 
  User, 
  LogOut,
  Settings,
  Sun,
  Moon,
  Monitor
} from 'lucide-vue-next';
import UserAvatar from './components/UserAvatar.vue';

const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();

const isAuthenticated = computed(() => authStore.isAuthenticated);
const currentUser = computed(() => authStore.user);

const dropdownOpen = ref(false);
const themeDropdownOpen = ref(false);

const toggleDropdown = (e) => {
  e.stopPropagation();
  dropdownOpen.value = !dropdownOpen.value;
  themeDropdownOpen.value = false;
};

const toggleThemeDropdown = (e) => {
  e.stopPropagation();
  themeDropdownOpen.value = !themeDropdownOpen.value;
  dropdownOpen.value = false;
};

const closeAllDropdowns = () => {
  dropdownOpen.value = false;
  themeDropdownOpen.value = false;
};

const currentTheme = computed(() => currentUser.value?.theme || 'system');

const activeIcon = computed(() => {
  const isDark = currentTheme.value === 'dark' || (currentTheme.value === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
  return isDark ? Moon : Sun;
});

const selectTheme = async (themeName) => {
  themeDropdownOpen.value = false;
  if (currentUser.value) {
    try {
      await authStore.updateProfile({ theme: themeName });
    } catch (err) {
      console.error('Failed to update theme:', err);
    }
  }
};

const applyTheme = (themeName) => {
  const isDark = themeName === 'dark' || (themeName === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
  if (isDark) {
    document.documentElement.setAttribute('data-theme', 'dark');
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.setAttribute('data-theme', 'light');
    document.documentElement.classList.remove('dark');
  }
};

watch(currentTheme, (newTheme) => {
  applyTheme(newTheme);
}, { immediate: true });

let systemThemeMedia;
const handleSystemThemeChange = () => {
  if (currentTheme.value === 'system') {
    applyTheme('system');
  }
};

onMounted(() => {
  authStore.init();
  authStore.fetchProfile();
  window.addEventListener('click', closeAllDropdowns);
  
  systemThemeMedia = window.matchMedia('(prefers-color-scheme: dark)');
  systemThemeMedia.addEventListener('change', handleSystemThemeChange);
});

onUnmounted(() => {
  window.removeEventListener('click', closeAllDropdowns);
  if (systemThemeMedia) {
    systemThemeMedia.removeEventListener('change', handleSystemThemeChange);
  }
});

const goToSettings = () => {
  dropdownOpen.value = false;
  router.push('/profile');
};

const handleLogout = async () => {
  dropdownOpen.value = false;
  await authStore.logout();
  router.push('/login');
};
</script>

<template>
  <div v-if="!isAuthenticated" class="auth-wrapper-full">
    <router-view />
  </div>
  
  <div v-else class="app-wrapper">
    <!-- Web Top Header -->
    <header class="app-header">
      <div class="header-left" @click="router.push('/')">
        <img src="/favicon.svg" alt="Moola Logo" class="header-logo" />
        <h1 class="header-title">Moola</h1>
      </div>
      
      <div class="header-right">
        <!-- Theme Selector -->
        <div class="theme-dropdown-container">
          <button class="theme-btn" @click="toggleThemeDropdown" title="切换主题">
            <component :is="activeIcon" :size="20" />
          </button>
          
          <transition name="dropdown">
            <div v-if="themeDropdownOpen" class="dropdown-menu theme-menu">
              <button class="dropdown-item" :class="{ 'active': currentTheme === 'light' }" @click="selectTheme('light')">
                <Sun :size="16" />
                <span>亮色</span>
              </button>
              <button class="dropdown-item" :class="{ 'active': currentTheme === 'dark' }" @click="selectTheme('dark')">
                <Moon :size="16" />
                <span>暗色</span>
              </button>
              <button class="dropdown-item" :class="{ 'active': currentTheme === 'system' }" @click="selectTheme('system')">
                <Monitor :size="16" />
                <span>系统</span>
              </button>
            </div>
          </transition>
        </div>

        <!-- User Selector -->
        <div class="user-dropdown-container">
          <button class="avatar-btn" @click="toggleDropdown">
            <UserAvatar :user="currentUser" :size="36" />
            <svg class="chevron-icon" :class="{ 'rotate': dropdownOpen }" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </button>
          
          <transition name="dropdown">
            <div v-if="dropdownOpen" class="dropdown-menu">
              <div class="dropdown-header">
                <div class="dropdown-user-nickname">{{ currentUser?.nickname }}</div>
                <div class="dropdown-user-username">@{{ currentUser?.username }}</div>
              </div>
              <div class="dropdown-divider"></div>
              <button class="dropdown-item" @click="goToSettings">
                <Settings :size="16" />
                <span>用户设置</span>
              </button>
              <button class="dropdown-item logout-item" @click="handleLogout">
                <LogOut :size="16" />
                <span>退出登录</span>
              </button>
            </div>
          </transition>
        </div>
      </div>
    </header>

    <!-- Desktop Sidebar Navigation -->
    <aside class="sidebar">
      <nav class="sidebar-menu">
        <router-link to="/" class="menu-item" active-class="active">
          <LayoutDashboard :size="20" />
          <span>总览</span>
        </router-link>
        <router-link to="/ledger" class="menu-item" active-class="active">
          <Wallet :size="20" />
          <span>个人记账</span>
        </router-link>
        <router-link to="/projects" class="menu-item" active-class="active">
          <FolderKanban :size="20" />
          <span>项目记账</span>
        </router-link>
        <router-link to="/categories" class="menu-item" active-class="active">
          <Tags :size="20" />
          <span>分类管理</span>
        </router-link>
      </nav>
    </aside>

    <!-- Mobile Bottom Navigation H5 -->
    <nav class="bottom-nav">
      <router-link to="/" class="bottom-nav-item" active-class="active">
        <LayoutDashboard :size="20" />
        <span>总览</span>
      </router-link>
      <router-link to="/ledger" class="bottom-nav-item" active-class="active">
        <Wallet :size="20" />
        <span>个人</span>
      </router-link>
      <router-link to="/projects" class="bottom-nav-item" active-class="active">
        <FolderKanban :size="20" />
        <span>项目</span>
      </router-link>
      <router-link to="/categories" class="bottom-nav-item" active-class="active">
        <Tags :size="20" />
        <span>分类</span>
      </router-link>
      <router-link to="/profile" class="bottom-nav-item" active-class="active">
        <User :size="20" />
        <span>我的</span>
      </router-link>
    </nav>

    <!-- Main Content Container -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.auth-wrapper-full {
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: var(--bg-app);
  background-image: var(--bg-gradient);
}

.logo-icon {
  font-size: 24px;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 10px var(--primary-glow);
}

.user-nickname {
  font-size: 14px;
  font-weight: 600;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-username {
  font-size: 12px;
}

.w-full {
  width: 100%;
}

/* Header Styles */
.app-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 70px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--panel-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  z-index: 200;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.01);
  transition: background-color var(--transition-fast), border-color var(--transition-fast);
}

[data-theme="dark"] .app-header {
  background: rgba(30, 30, 36, 0.85);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.header-logo {
  width: 32px;
  height: 32px;
  object-fit: contain;
}

.header-title {
  font-family: var(--font-heading);
  font-size: 22px;
  font-weight: 800;
  color: var(--color-text-dark);
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
}

.avatar-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 50%;
  transition: var(--transition-fast);
}

.avatar-btn:hover {
  background: rgba(0, 0, 0, 0.04);
}

[data-theme="dark"] .avatar-btn:hover {
  background: rgba(255, 255, 255, 0.04);
}

.chevron-icon {
  width: 14px;
  height: 14px;
  color: var(--color-text-muted);
  transition: transform var(--transition-fast);
}

.chevron-icon.rotate {
  transform: rotate(180deg);
}

/* Theme Selector */
.theme-dropdown-container {
  position: relative;
  margin-right: 12px;
}

.theme-btn {
  background: none;
  border: none;
  cursor: pointer;
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: var(--color-text);
  transition: var(--transition-fast);
}

.theme-btn:hover {
  background: rgba(0, 0, 0, 0.04);
  color: var(--color-text-dark);
}

[data-theme="dark"] .theme-btn:hover {
  background: rgba(255, 255, 255, 0.04);
  color: var(--color-text-dark);
}

.theme-menu {
  width: 130px !important;
}

/* User Dropdown */
.user-dropdown-container {
  position: relative;
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 200px;
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-md);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  z-index: 300;
  transition: background-color var(--transition-fast), border-color var(--transition-fast);
}

.dropdown-header {
  padding: 8px 12px;
  text-align: left;
}

.dropdown-user-nickname {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-dark);
}

.dropdown-user-username {
  font-size: 12px;
  color: var(--color-text-muted);
}

.dropdown-divider {
  height: 1px;
  background: var(--panel-border);
  margin: 4px 0;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  width: 100%;
  border: none;
  background: none;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text);
  cursor: pointer;
  transition: var(--transition-fast);
  text-align: left;
}

.dropdown-item:hover {
  background: var(--gray-100);
  color: var(--color-text-dark);
}

.dropdown-item.active {
  background: var(--primary-glow) !important;
  color: var(--primary-text) !important;
  font-weight: 600;
}

[data-theme="dark"] .dropdown-item.active {
  background: rgba(255, 210, 30, 0.2) !important;
  color: #ffd21e !important;
}

.dropdown-item.logout-item {
  color: var(--danger);
}

.dropdown-item.logout-item:hover {
  background: var(--danger-glow);
  color: var(--danger);
}

/* Dropdown Animation */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Responsive Overrides */
@media (max-width: 768px) {
  .app-header {
    display: none;
  }
}
</style>
