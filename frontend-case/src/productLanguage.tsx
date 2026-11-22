import { createContext, useContext, useState, type ReactNode } from 'react'

export const productLanguages = ['en', 'zh-Hans', 'zh-Hant'] as const
export type ProductLanguage = (typeof productLanguages)[number]
const key = 'liorin-product-b-language'
const LanguageContext = createContext<{ locale: ProductLanguage; choose: (locale: ProductLanguage) => void } | null>(null)

export function useProductLanguage() {
  return useContext(LanguageContext)
}

export function ProductLanguageProvider({ enabled, children }: { enabled: boolean; children: ReactNode }) {
  const [locale, setLocale] = useState<ProductLanguage>(() => {
    if (!enabled) return 'en'
    try {
      const saved = sessionStorage.getItem(key)
      return productLanguages.find(candidate => candidate === saved) ?? 'en'
    } catch { return 'en' }
  })
  const choose = (next: ProductLanguage) => {
    setLocale(next)
    try { sessionStorage.setItem(key, next) } catch { /* optional browser storage */ }
  }
  return <LanguageContext.Provider value={enabled ? { locale, choose } : null}>{children}</LanguageContext.Provider>
}
