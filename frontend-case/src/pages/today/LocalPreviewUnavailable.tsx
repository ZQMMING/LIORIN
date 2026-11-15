interface Props { onRetry: () => void }

/** 本机网页预览：后端不可用时的空状态，不提供模拟计算结果。 */
export default function LocalPreviewUnavailable({ onRetry }: Props) {
  return <section className="page-container" role="status" aria-label="本机预览状态">
    <p className="page-subtitle">LOCAL PREVIEW / 本机预览</p>
    <h1>页面已就绪，数据服务尚未连接。</h1>
    <p>你现在可以查看页面结构、导航和交互。公共今日内容需要本机后端正常启动；这里不会用模拟卦象或断语替代真实结果。</p>
    <p>请确认开发机上的 API `http://127.0.0.1:8000/health` 返回 JSON，然后点击重试。</p>
    <button type="button" onClick={onRetry}>重试连接</button>
  </section>
}
