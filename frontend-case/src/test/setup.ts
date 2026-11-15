// Vitest setup —— jest-dom matchers（官方 vitest 入口，自动扩展 expect 类型）
import '@testing-library/jest-dom/vitest'
import { afterEach, vi } from 'vitest'

// Each test starts at the public entry regardless of navigation in earlier tests.
afterEach(() => window.history.replaceState(null, '', '/'))

// jsdom 未实现 window.matchMedia（组件用 prefers-reduced-motion 判断动画降级）。
// 测试环境统一 mock，默认不开启 reduced motion；个别用例可覆盖返回值。
if (typeof window.matchMedia !== 'function') {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(), // 旧版 API
      removeListener: vi.fn(), // 旧版 API
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  })
}
