import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const lanTest = process.env.LIORIN_LAN_TEST === '1'
const localPreview = process.env.LIORIN_LOCAL_PREVIEW === '1'
if (lanTest && process.env.VITE_LIORIN_LAN_TEST !== '1') {
  throw new Error('LAN 测试需同时设置 VITE_LIORIN_LAN_TEST=1 以启用同源 API 代理')
}
if (localPreview && process.env.VITE_LIORIN_LOCAL_PREVIEW !== '1') {
  throw new Error('本机预览需同时设置 VITE_LIORIN_LOCAL_PREVIEW=1 以启用同源 API 代理')
}

export default defineConfig({
  plugins: [react()],
  server: {
    // 仅在明确设置 LIORIN_LAN_TEST=1 时开放内网预览；后端仍只监听 loopback。
    host: lanTest ? '0.0.0.0' : '127.0.0.1',
    port: 5173,
    open: false,
    proxy: (lanTest || localPreview) ? {
      '/v1': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/health': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    } : undefined,
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
  }
})
