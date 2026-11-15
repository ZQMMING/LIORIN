import React from 'react'
import InfoCard from './InfoCard'

interface HeluoCardProps {
  onOpen?: () => void
  premiumOnly?: boolean
  isPremium?: boolean
}

/**
 * Heluo Card — Section 17 of LIORIN spec
 */
const HeluoCard: React.FC<HeluoCardProps> = ({ onOpen, premiumOnly, isPremium }) => {
  if (premiumOnly && !isPremium) {
    return null // Hidden for non-premium, shown as gate elsewhere
  }

  return (
    <InfoCard
      label="HELUO"
      title="今日流日"
      text="时间结构分析基于河洛数理，反映今日的气场流向。"
      actionLabel="查看河洛"
      onAction={onOpen}
    />
  )
}

export default HeluoCard
