import React from 'react'
import InfoCard from './InfoCard'

interface YijingCardProps {
  hexagramName: string
  yaoName: string
  onOpen?: () => void
  premiumOnly?: boolean
  isPremium?: boolean
}

/**
 * Yijing Card — Section 18 of LIORIN spec
 */
const YijingCard: React.FC<YijingCardProps> = ({
  hexagramName,
  yaoName,
  onOpen,
  premiumOnly,
  isPremium,
}) => {
  if (premiumOnly && !isPremium) {
    return null
  }

  return (
    <InfoCard
      label="YIJING"
      title={`${hexagramName} · ${yaoName}`}
      text="卦辞与爻辞的原典依据，供深入研读。"
      actionLabel="查看易经"
      onAction={onOpen}
    />
  )
}

export default YijingCard
