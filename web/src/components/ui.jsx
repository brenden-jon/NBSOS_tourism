import { ACTIONS } from '../lib/constants'

export function Hero({ eyebrow, title, lead, children, tone = 'dark' }) {
  return (
    <section className="relative overflow-hidden bg-wb-slateDk">
      <div className="absolute inset-0"
        style={{ backgroundImage:
          'linear-gradient(115deg, rgba(46,57,68,.97) 0%, rgba(46,57,68,.80) 45%, rgba(62,124,171,.55) 100%),' +
          'radial-gradient(circle at 88% 22%, rgba(127,162,58,.55) 0%, transparent 55%)' }} />
      <div className="absolute inset-0 opacity-[0.10]"
        style={{ backgroundImage:
          'repeating-linear-gradient(60deg, #fff 0 1px, transparent 1px 26px)' }} />
      <div className="wrap relative py-14 sm:py-20">
        {eyebrow && <div className="text-[11px] font-bold tracking-[0.16em] uppercase text-wb-yellow mb-3">{eyebrow}</div>}
        <h1 className="text-white font-bold leading-[1.15] text-[28px] sm:text-[40px] max-w-4xl">{title}</h1>
        {lead && <p className="mt-5 text-white/85 text-[16px] sm:text-[17px] leading-relaxed max-w-3xl">{lead}</p>}
        {children && <div className="mt-7">{children}</div>}
      </div>
    </section>
  )
}

export function Section({ eyebrow, title, lead, children, className = '', tint = false, id }) {
  return (
    <section id={id} className={`${tint ? 'bg-wb-wash' : 'bg-white'} ${className}`}>
      <div className="wrap py-12 sm:py-16">
        {eyebrow && <div className="eyebrow mb-2">{eyebrow}</div>}
        {title && <h2 className="h-section max-w-3xl">{title}</h2>}
        {lead && <p className="prose-wb mt-4 max-w-3xl text-[15.5px] text-wb-slate">{lead}</p>}
        {children && <div className={title || lead ? 'mt-8' : ''}>{children}</div>}
      </div>
    </section>
  )
}

export function Stat({ value, label, sub }) {
  return (
    <div className="card p-5">
      <div className="stat-num">{value}</div>
      <div className="stat-lbl">{label}</div>
      {sub && <div className="mt-2 text-[12px] text-wb-muted leading-snug">{sub}</div>}
    </div>
  )
}

export function ActionChip({ action, size = 'sm' }) {
  const a = ACTIONS[action]
  if (!a) return null
  return (
    <span className={`chip text-white ${size === 'lg' ? 'text-[12px] px-3 py-1.5' : ''}`}
      style={{ backgroundColor: a.color }}>{a.label}</span>
  )
}

export function ScoreBar({ label, value, color = '#3E7CAB', desc }) {
  const v = Math.max(0, Math.min(100, Number(value) || 0))
  return (
    <div className="group">
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-[12.5px] font-semibold text-wb-slateDk">{label}</span>
        <span className="text-[12.5px] font-bold tabular-nums" style={{ color }}>{v.toFixed(0)}</span>
      </div>
      <div className="mt-1 h-[7px] rounded-full bg-wb-line overflow-hidden">
        <div className="h-full rounded-full transition-[width] duration-500"
          style={{ width: `${v}%`, backgroundColor: color }} />
      </div>
      {desc && <p className="mt-1 text-[11px] leading-snug text-wb-muted">{desc}</p>}
    </div>
  )
}

export function Callout({ title, children, tone = 'blue' }) {
  const tones = {
    blue:  'border-l-wb-blue bg-wb-blue/[0.06]',
    green: 'border-l-wb-green bg-wb-green/[0.07]',
    amber: 'border-l-act-adapt bg-act-adapt/[0.08]',
    red:   'border-l-act-manage bg-act-manage/[0.06]',
  }
  return (
    <div className={`border-l-4 ${tones[tone]} rounded-r-md p-5`}>
      {title && <div className="font-bold text-[14px] text-wb-slateDk mb-2">{title}</div>}
      <div className="prose-wb text-[14px]">{children}</div>
    </div>
  )
}

export function Loading({ what = 'data' }) {
  return (
    <div className="flex items-center gap-3 text-wb-muted text-[13px] py-16 justify-center">
      <span className="inline-block w-4 h-4 rounded-full border-2 border-wb-line border-t-wb-blue animate-spin" />
      Loading {what}…
    </div>
  )
}

export function ErrorBox({ message }) {
  return (
    <div className="card p-6 border-act-manage/40 bg-act-manage/[0.05]">
      <div className="font-bold text-[14px] text-act-manage mb-1">Could not load data</div>
      <div className="text-[13px] text-wb-slate">{message}</div>
    </div>
  )
}
