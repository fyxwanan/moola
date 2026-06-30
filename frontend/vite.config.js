import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  base: (process.env.ELECTRON === 'true' || process.env.CAPACITOR === 'true') ? './' : '/',
  server: {
    host: '0.0.0.0'
  },
  build: {
    rollupOptions: {
      onwarn(warning, defaultWarn) {
        if (warning.code === 'INVALID_ANNOTATION' || (warning.message && warning.message.includes('INVALID_ANNOTATION'))) {
          return;
        }
        defaultWarn(warning);
      }
    }
  }
})
