import React from 'react';
import {
  ArrowRight,
  FolderKanban,
  GitBranch,
  LockKeyhole,
  MessageSquareCode,
  ReceiptText,
  Server,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { CommandWindow, PageIntro, Reveal, SectionHeading } from '../components/ui';

const capabilities = [
  {
    icon: <FolderKanban size={16} className="feature-ledger__icon" />,
    title: 'Project hygiene — krud org',
    text: 'Run krud org in any directory. Krud detects your stack, finds missing structure, and proposes .gitignore, README, and folder scaffolding. Each action is previewed before you approve.',
  },
  {
    icon: <GitBranch size={16} className="feature-ledger__icon" />,
    title: 'Node.js + Python stack awareness',
    text: 'Krud detects package.json, requirements.txt, pyproject.toml, Cargo.toml and more. Every proposal is tailored to your actual stack — not a generic template.',
  },
  {
    icon: <MessageSquareCode size={16} className="feature-ledger__icon" />,
    title: 'Natural-language command proposals',
    text: 'Describe the outcome in plain language. Krud returns a reviewable command plan with rationale and risk level attached so you know exactly what will happen before it runs.',
  },
  {
    icon: <LockKeyhole size={16} className="feature-ledger__icon" />,
    title: 'Approval-gated execution',
    text: 'Nothing runs silently. Every proposal pauses for your decision — run now, queue for the daemon, or skip. Destructive commands are flagged as high risk.',
  },
  {
    icon: <Server size={16} className="feature-ledger__icon" />,
    title: 'Background daemon for long jobs',
    text: 'Queue tasks to the local daemon and keep your foreground shell free. Results are captured and readable when you come back.',
  },
  {
    icon: <ReceiptText size={16} className="feature-ledger__icon" />,
    title: 'Persistent session memory',
    text: 'Sessions and command history stay attached so the next question starts with context. No blank-slate restarts mid-problem.',
  },
];

export default function Features() {
  return (
    <>
      <PageIntro
        eyebrow="Features"
        title="Built for the indie dev who lives in a terminal."
        description="Krud owns two moments in your workflow: cleaning up a project before you start (krud org) and moving fast when you're deep in a problem (krud chat). Everything else supports those two moments."
        aside={
          <div className="meta-panel">
            <p>
              Designed for solo builders on Node.js and Python — the indie dev sweet spot.
              No team features gate the core workflow. No enterprise overhead.
            </p>
          </div>
        }
      />

      <section className="section-block">
        <div className="shell">
          <div className="feature-ledger">
            {capabilities.map(({ icon, title, text }, index) => (
              <Reveal key={title} delay={index * 0.06} className="feature-ledger__item">
                <span className="feature-ledger__index">0{index + 1}</span>
                <strong className="feature-ledger__title">
                  {icon}
                  {title}
                </strong>
                <p>{text}</p>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section className="section-block">
        <div className="shell split-section">
          <Reveal>
            <SectionHeading
              eyebrow="krud org"
              title="The command nobody else built."
              description="Every competitor activates when you're already writing code. krud org activates when you're starting a project, cleaning up a repo, or coming back to a side project after three months of chaos."
            />
            <ul className="detail-list">
              <li>Runs without a chat session — lower friction than any competitor.</li>
              <li>Generates stack-specific .gitignore files with OS, editor, and dependency ignores.</li>
              <li>Scaffolds README.md with placeholder sections so you start with a front door.</li>
              <li>Proposes missing standard directories (src/, tests/) when clearly absent.</li>
            </ul>
          </Reveal>

          <Reveal delay={0.1}>
            <CommandWindow
              title="krud org — Node.js project"
              label="hygiene scan"
              lines={[
                { kind: 'command', text: 'krud org' },
                { kind: 'agent', text: 'Stack: Node.js. Scanning top-level structure...' },
                { kind: 'output', text: 'Missing: .gitignore, README.md' },
                { kind: 'success', text: 'Write .gitignore? [y/N]: y  →  Created (node_modules/, .env, dist/)' },
              ]}
              footer="Stack detected. File previewed. Written on approval."
            />
          </Reveal>
        </div>
      </section>

      <section className="section-block">
        <div className="shell split-section is-reverse">
          <Reveal>
            <SectionHeading
              eyebrow="krud chat"
              title="Plain language. Reviewable plan. Your decision."
              description="When you're deep in a problem, you don't want to reconstruct the exact command from memory. Describe the outcome — Krud gives you a plan you can approve, queue, or skip."
            />
            <ul className="detail-list">
              <li>Risk levels (low / medium / high) attached to every proposal.</li>
              <li>Inspection-first — safe read commands proposed before write commands.</li>
              <li>Errors become diagnosis, not just raw logs.</li>
            </ul>
          </Reveal>

          <Reveal delay={0.1}>
            <CommandWindow
              title="krud chat"
              label="command plan"
              lines={[
                { kind: 'prompt', text: 'why is my Python script running out of memory' },
                { kind: 'agent', text: 'Checking process memory and any obvious leaks in the code path...' },
                { kind: 'output', text: 'ps aux | grep python && tracemalloc snapshot' },
                { kind: 'success', text: 'Risk: low. Approve to run, queue, or skip.' },
              ]}
              footer="The explanation is the product. The shell output is just evidence."
            />
          </Reveal>
        </div>
      </section>

      <section className="section-block">
        <div className="shell">
          <Reveal className="cta-band">
            <SectionHeading
              eyebrow="Try it"
              title="Install, run krud org on a real project, and see what it finds."
              description="Five minutes is enough to know whether Krud belongs in your daily workflow. No configuration. No team setup. Just you and the terminal."
            />
            <div className="cta-band__actions">
              <Link to="/docs" className="button button-primary">
                Installation guide
                <ArrowRight size={15} />
              </Link>
              <Link to="/pricing" className="button button-secondary">
                See plans
              </Link>
            </div>
          </Reveal>
        </div>
      </section>
    </>
  );
}
