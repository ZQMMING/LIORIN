import React from 'react'
import './support-pages.css'

export default function InsightsPage() {
  return <main className="support-page">
    <header className="support-header"><span className="support-eyebrow">INSIGHTS / 深入理解</span><h1>留一点空间，<br />给未来的发现。</h1><p>个人洞察尚未开放。我们会在数据与依据准备完成后，再呈现与你有关的内容。</p></header>
    <section className="support-empty" aria-labelledby="insights-empty-title">
      <div className="support-mark" aria-hidden="true"><i></i><i></i><i></i></div>
      <span className="support-eyebrow">COMING LATER</span>
      <h2 id="insights-empty-title">此处暂未开放</h2>
      <p>当前可以先查看公共今日信息。个人分析需要真实资料与已验证的计算结果。</p>
    </section>
    <aside className="support-note"><span>OUR APPROACH</span><p>每一种解释都应保留其来源、适用条件与不确定性。</p></aside>
  </main>
}
