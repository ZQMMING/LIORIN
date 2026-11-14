import type { PageName } from './components/navigation/BottomNav'

export type RoutePage = PageName | 'not-found'

const paths: Record<PageName, string> = {
  today: '/', guide: '/guide', insights: '/insights', me: '/me', more: '/more',
}

export function pageForPath(pathname: string): RoutePage {
  const path = pathname === '/' ? '/' : pathname.replace(/\/+$/, '')
  return (Object.entries(paths).find(([, value]) => value === path)?.[0] as PageName | undefined) ?? 'not-found'
}

export function pathForPage(page: PageName): string {
  return paths[page]
}
