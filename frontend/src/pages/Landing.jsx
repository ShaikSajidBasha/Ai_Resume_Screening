import { Link } from 'react-router-dom'
import { ScanSearch, Target, ListChecks, Sparkles, History, ShieldCheck, FileSearch } from 'lucide-react'

const features = [
  { icon: ScanSearch, title: 'Multi-agent resume analysis', body: 'Ten specialized AI agents each examine one dimension of your resume — parsing, ATS formatting, skills, keywords, experience, and writing quality — instead of one generic AI pass.' },
  { icon: Target, title: 'Job match scoring', body: 'See exactly how your resume lines up against a specific job description, with skill, keyword, experience, and education scores broken out separately.' },
  { icon: ListChecks, title: 'ATS compatibility check', body: 'Catch the formatting and structural issues that trip up applicant tracking systems, before a recruiter ever opens your file.' },
  { icon: Sparkles, title: 'Skill gap detection', body: "Know precisely which required and preferred skills are missing from your resume — and which ones you already have." },
  { icon: ShieldCheck, title: 'Honest recommendations', body: "Prioritized, grounded suggestions. The system won't tell you to claim a skill or experience you don't have." },
  { icon: History, title: 'Analysis history', body: 'Every analysis is saved, so you can track how your resume improves across different roles over time.' },
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-paper">
      <header className="max-w-6xl mx-auto px-8 py-6 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileSearch size={22} className="text-teal" />
          <span className="font-display text-lg text-ink">Screenline</span>
        </div>
        <div className="flex items-center gap-6">
          <Link to="/login" className="text-sm text-slate-650 hover:text-ink transition-colors">Log in</Link>
          <Link to="/register" className="text-sm px-4 py-2 rounded-md bg-ink text-paper hover:bg-ink-800 transition-colors">
            Create account
          </Link>
        </div>
      </header>

      <section className="max-w-6xl mx-auto px-8 pt-16 pb-24 grid md:grid-cols-2 gap-12 items-center">
        <div>
          <h1 className="font-display text-5xl leading-[1.1] text-ink">
            See your resume the way a screening system does.
          </h1>
          <p className="mt-6 text-lg text-slate-650 max-w-md">
            Screenline runs your resume through ten specialized AI agents against a real job
            description, then hands you a transparent, deterministic score — not a black box.
          </p>
          <div className="mt-8 flex items-center gap-4">
            <Link to="/register" className="px-5 py-3 rounded-md bg-teal text-paper text-sm hover:bg-teal/90 transition-colors">
              Analyze your resume
            </Link>
            <Link to="/login" className="px-5 py-3 rounded-md border border-ink/15 text-sm text-ink hover:border-ink/30 transition-colors">
              Log in
            </Link>
          </div>
          <p className="mt-6 text-xs text-slate-650 max-w-md">
            AI-generated scores are estimates for resume optimization and should not be treated
            as a final hiring decision.
          </p>
        </div>

        <div className="bg-ink rounded-md p-8 text-paper">
          <div className="flex items-center justify-between mb-6">
            <span className="text-sm text-white/50">Sample screening result</span>
            <span className="text-xs px-2.5 py-1 rounded-sm bg-teal/20 text-teal border border-teal/30">Moderate Match</span>
          </div>
          <div className="grid grid-cols-3 gap-4 text-center mb-6">
            {[['ATS', 82], ['Match', 76], ['Overall', 79]].map(([label, val]) => (
              <div key={label} className="rounded-sm bg-white/5 py-4">
                <div className="font-display text-3xl tabular-nums">{val}</div>
                <div className="text-xs text-white/50 mt-1">{label}</div>
              </div>
            ))}
          </div>
          <div className="space-y-2">
            {[['Skill match', 78], ['Keyword match', 71], ['Experience match', 85]].map(([label, val]) => (
              <div key={label}>
                <div className="flex justify-between text-xs text-white/60 mb-1">
                  <span>{label}</span><span className="tabular-nums">{val}%</span>
                </div>
                <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
                  <div className="h-full bg-signal rounded-full" style={{ width: `${val}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-8 pb-24">
        <div className="grid md:grid-cols-3 gap-x-8 gap-y-10">
          {features.map(({ icon: Icon, title, body }) => (
            <div key={title}>
              <Icon size={20} className="text-teal mb-3" />
              <h3 className="font-display text-lg text-ink mb-2">{title}</h3>
              <p className="text-sm text-slate-650 leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-ink/10 py-8">
        <p className="text-center text-xs text-slate-650">
          Screenline is a decision-support tool for resume optimization, not an automated hiring system.
        </p>
      </footer>
    </div>
  )
}
