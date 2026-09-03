/** Renders the **bold** spans the narrative generator emits. No other markdown is used. */
export default function RichText({ text, className = '' }) {
  if (!text) return null
  const parts = String(text).split(/(\*\*[^*]+\*\*)/g)
  return (
    <span className={className}>
      {parts.map((p, i) =>
        p.startsWith('**') && p.endsWith('**')
          ? <strong key={i} className="font-bold text-wb-slateDk">{p.slice(2, -2)}</strong>
          : <span key={i}>{p}</span>)}
    </span>
  )
}
