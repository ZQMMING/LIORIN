import React from 'react'
import './support-pages.css'

const sections = [
  { number: '01', title: '从时间开始', text: '公共页面展示当日历法信息。个人内容需要先建立资料，并由后端完成计算。' },
  { number: '02', title: '看清依据', text: '传统判断应有对应的规则和来源。不同体系各自保留解释，不以投票生成统一结论。' },
  { number: '03', title: '保留边界', text: '资料不完整或依据不足时，应明确说明。传统解释可用于思考，不代表对未来事件的保证。' },
]

export default function GuidePage() {
  return <div className="support-page">
    <header className="support-header"><span className="support-eyebrow">THE GUIDE / 使用指南</span><h1>理解时间，<br />也理解它的边界。</h1><p>一份简明的阅读方式，帮助你分辨时间事实、传统解释与个人选择。</p></header>
    <div className="support-list">{sections.map((item) => <section className="support-row" key={item.number}><span className="support-number">{item.number}</span><div><h2>{item.title}</h2><p>{item.text}</p></div></section>)}</div>
    <aside className="support-note"><span>ABOUT LIORIN</span><p>以清晰的来源与适用条件，呈现传统时间文化。</p></aside>
  </div>
}
