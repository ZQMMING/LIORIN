import React, { useEffect, useRef, useState } from 'react'
import TimeOrbit from '../../components/hexagram/TimeOrbit'
import LoadingState from '../../components/feedback/LoadingState'
import ErrorState from '../../components/feedback/ErrorState'
import { playHeroAnimation, type HeroStageValue, BREATHING_CSS } from '../../animation/hero'
import type { RealPublicTodayView } from '../../view-models/publicToday'
import './RealPublicToday.css'

interface RealPublicTodayProps {
  view?: RealPublicTodayView | null
  isLoading?: boolean
  isError?: boolean
  onRetry?: () => void
}

export default function RealPublicToday({ view, isLoading = false, isError = false, onRetry }: RealPublicTodayProps) {
  const [heroStage, setHeroStage] = useState<HeroStageValue>(0 as HeroStageValue)
  const reducedMotion = useRef(window.matchMedia('(prefers-reduced-motion: reduce)').matches)
  useEffect(() => { playHeroAnimation(setHeroStage, reducedMotion.current) }, [])

  if (isLoading) return <LoadingState />
  if (isError || !view) return <ErrorState type="network" onRetry={onRetry} />

  return (
    <main className="today-editorial">
      <style>{BREATHING_CSS}</style>
      <div className="today-topline"><span>LIORIN / 今日</span><span>THE DAILY ALMANAC</span></div>
      <section className="today-intro" aria-labelledby="today-heading">
        <div className="today-intro-copy">
          <p className="today-kicker"><span className="today-dot" /> 今日 · {view.weekday}</p>
          <h1 id="today-heading">时间流转，<br /><em>今日自成一象。</em></h1>
          <p className="today-intro-description">循着节气与历法，留一点时间给自己。</p>
          <div className="today-date"><span>{view.dateLabel}</span><span>{view.lunarMonth}</span></div>
        </div>
        <div className="today-orbit" aria-label="河图洛书图形">
          <span className="today-orbit-label">HE TU · LUO SHU</span>
          <TimeOrbit stage={heroStage} reducedMotion={reducedMotion.current} />
          <span className="today-orbit-caption">一日一时 · 自有其序</span>
        </div>
      </section>

      <div className="today-section-heading"><span>01 / 今日历象</span><span>THE RHYTHM OF TODAY</span></div>
      <section className="today-calendar" aria-label="今日历象">
        <div className="today-hex">
          <p className="today-label">今日卦象 <span>DAILY HEXAGRAM</span></p>
          <div className="today-hex-name">{view.hexName}</div>
          <div className="today-hex-details">
            {view.hexUpper && view.hexLower && <span>上卦 {view.hexUpper} · 下卦 {view.hexLower}</span>}
            {view.movingLine && <span>动爻 {view.movingLine}</span>}
            {view.changedHex && <span>变卦 {view.changedHex}</span>}
          </div>
        </div>
        <div className="today-pillars">
          <p className="today-label">干支 <span>HEAVEN & EARTH</span></p>
          <div className="today-pillar-list">{view.pillars.map(p => (
            <div key={p.label} className="today-pillar"><span>{p.label}</span><strong>{p.name}</strong></div>
          ))}</div>
        </div>
      </section>

      <div className="today-section-heading"><span>02 / 日常参考</span><span>AT A GLANCE</span></div>
      <section className="today-detail-grid" aria-label="今日历法信息">
        <div className="today-yi-ji">
          <div className="today-advice"><p className="today-label">宜 <span>TRADITIONAL NOTES</span></p>
            {view.yi.length ? <ul>{view.yi.map((item, i) => <li key={i}>{item}</li>)}</ul> : <p className="today-empty">暂无数据</p>}</div>
          <div className="today-advice"><p className="today-label">忌 <span>TRADITIONAL NOTES</span></p>
            {view.ji.length ? <ul>{view.ji.map((item, i) => <li key={i}>{item}</li>)}</ul> : <p className="today-empty">暂无数据</p>}</div>
        </div>
        <div className="today-essentials"><p className="today-label">历法要点 <span>CALENDAR DETAILS</span></p>
          {view.essentials.map(row => <div className="today-detail-row" key={row.label}><span>{row.label}</span><strong>{row.value}</strong></div>)}
          {!view.essentials.length && <p className="today-empty">暂无数据</p>}
        </div>
      </section>
      <footer className="today-footer"><p>以传统历法为线索，留心自己的节奏。</p><span>trace: {view.traceId}</span></footer>
    </main>
  )
}
