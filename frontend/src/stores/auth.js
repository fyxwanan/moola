import { defineStore } from 'pinia';
import api from '../api';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('moola_user')) || null,
    token: localStorage.getItem('moola_token') || null,
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.token,
  },
  
  actions: {
    init() {
      // Listen for sliding-window token updates from the Axios interceptor
      window.addEventListener('moola-token-refreshed', (event) => {
        this.token = event.detail;
      });
    },

    async login(username, password) {
      try {
        const response = await api.post('/auth/login', { username, password });
        const { access_token, user } = response.data;
        
        this.token = access_token;
        this.user = user;
        
        localStorage.setItem('moola_token', access_token);
        localStorage.setItem('moola_user', JSON.stringify(user));
        
        return user;
      } catch (error) {
        throw error.response?.data?.detail || '登录失败，请检查用户名或密码';
      }
    },
    
    async register(username, password, nickname) {
      try {
        const response = await api.post('/auth/register', { username, password, nickname });
        const { access_token, user } = response.data;
        
        this.token = access_token;
        this.user = user;
        
        localStorage.setItem('moola_token', access_token);
        localStorage.setItem('moola_user', JSON.stringify(user));
        
        return user;
      } catch (error) {
        throw error.response?.data?.detail || '注册失败，请换个用户名重试';
      }
    },
    
    async logout() {
      this.token = null;
      this.user = null;
      localStorage.removeItem('moola_token');
      localStorage.removeItem('moola_user');
    },
    
    async fetchProfile() {
      if (!this.token) return;
      try {
        const response = await api.get('/auth/me');
        this.user = response.data;
        localStorage.setItem('moola_user', JSON.stringify(response.data));
      } catch (error) {
        this.logout();
      }
    },
    
    async updateProfile(data) {
      try {
        const response = await api.put('/auth/me', data);
        this.user = response.data;
        localStorage.setItem('moola_user', JSON.stringify(response.data));
        return response.data;
      } catch (error) {
        throw error.response?.data?.detail || '修改个人信息失败';
      }
    }
  }
});
