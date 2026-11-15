import React from 'react'
import InfoCard from './InfoCard'

interface ZiweiCardProps {
  onOpen?: () => void
  premiumOnly?: boolean
  isPremium?: boolean
}

/**
 * Ziwei Card — Section 19 of LIORIN spec
 */
const ZiweiCard: React.FC<ZiweiCardProps> = ({ onOpen, premiumOnly, isPremium }) => {
  if (premiumOnly && !isPremium) {
    return null
  }

  return (
    <InfoCard
      label="ZIWEI"
      title="今日个人状态"
      text="紫微斗数视角下的今日能量态势。"
      actionLabel="查看紫微"
      onAction={onOpen}
    />
  )
}

export default ZiweiCard
