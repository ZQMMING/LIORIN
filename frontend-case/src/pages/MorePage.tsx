import type { PageName } from '../components/navigation/BottomNav'
import './support-pages.css'

interface Props { onNavigate: (page: PageName) => void }

export default function MorePage({ onNavigate }: Props) {
  return <main className="support-page more-page">
    <header className="support-header">
      <span className="support-eyebrow">MORE / 更多</span>
      <h1>从这里，<br />找到需要的内容。</h1>
      <p>查看使用说明，或前往账户区域管理出生资料。</p>
    </header>
    <nav className="more-links" aria-label="更多功能">
      <button type="button" onClick={() => onNavigate('guide')}>
        <span><small>01 / GUIDE</small><strong>使用说明</strong><span>了解内容来源与使用边界</span></span><span aria-hidden="true">↗</span>
      </button>
      <button type="button" onClick={() => onNavigate('me')}>
        <span><small>02 / ACCOUNT</small><strong>账户与出生档案</strong><span>登录、填写或读取已存资料</span></span><span aria-hidden="true">↗</span>
      </button>
    </nav>
    <aside className="support-note"><span>COMING LATER</span><p>偏好设置、订阅与更多个人内容尚未开放。</p></aside>
  </main>
}
