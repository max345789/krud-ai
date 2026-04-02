import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, FolderKanban, ShieldCheck, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import heroArt from '../assets/hero.png';
import { INSTALL_COMMAND } from '../content/site';
import { CommandWindow, CopyCommand, Reveal, SectionHeading } from '../components/ui';

const heroLines = [
  { kind: 'command', text: 'krud org' },
  { kind: 'agent', text: 'Scanning project — detected Node.js + Python...' },
  { kind: 'output', text: 'No .gitignore found. No README found. Proposing 2 actions.' },
  { kind: 'success', text: 'Write .gitignore? [y/N]: y  →  Created. Write README.md? [y/N]: y  →  Created.' },
];

const whyLines = [
  {
    title: 'Built for solo builders',
    text: 'Every other CLI agent is designed for teams or enterprise. Krud is made for the indie dev working alone — no ticket system, no standup, just you and the terminal.',
  },
  {
    title: 'Project hygiene as a first-class feature',
    text: 'Run krud org on any project and get a stack-aware hygiene report: missing .gitignore, missing README, folder structure gaps. Fixed in one session.',
  },
  {
    title: 'Ask in plain language',
    text: 'When you need to move fast, describe the outcome. Krud turns it into a reviewable command plan so you skip the docs rabbit hole.',
  },
];

const systemFacts = [
  'Stack detection across Node.js, Python, Rust, Go and more',
  'Project hygiene scan that runs without a chat session',
  'Approval-gated shell commands — nothing runs silently',
];

const orgLines = [
  { kind: 'command', text: 'krud org' },
  { kind: 'agent', text: 'Stack: Node.js + Python. 3 hygiene actions found.' },
  { kind: 'output', text: 'create .gitignore  ·  create README.md  ·  mkdir src/' },
  { kind: 'success', text: 'Each action previewed before you approve. Nothing written without asking.' },
];

const chatLines = [
  { kind: 'prompt', text: 'my express server keeps crashing overnight, where do I start' },
  { kind: 'agent', text: 'Checking logs and the process manager for the last crash...' },
  { kind: 'output', text: 'pm2 logs --lines 100 && pm2 show app' },
  { kind: 'success', text: 'Ready to run. Approve, queue for the daemon, or skip.' },
];

export default function Home() {
  const MotionDiv = motion.div;

  return (
    <>
      <section className="hero-shell hero-shell--fullbleed">
        <div className="hero-bleed">
          <div className="shell hero-grid">
            <Reveal className="hero-copy">
              <p className="hero-kicker">
                <Sparkles size={14} />
                The CLI agent built for indie devs
              </p>
              <p className="hero-brand">KRUD AI</p>
              <h1>Your project. Your stack. Your terminal.</h1>
              <p className="hero-lead">
                Krud is the CLI agent made for solo builders on Node.js and Python.
                Run <code>krud org</code> to fix project hygiene in seconds. Ask in plain
                language when you need to move fast. Nothing runs without your approval.
              </p>

              <div className="hero-actions">
                <CopyCommand command={INSTALL_COMMAND} label="Install" />
                <div className="button-row">
                  <Link to="/pricing" className="button button-primary">
                    Start free trial
                    <ArrowRight size={15} />
                  </Link>
                  <Link to="/docs" className="button button-secondary">
                    Read docs
                  </Link>
                </div>
              </div>

              <div className="hero-proof">
                {systemFacts.map((item) => (
                  <div key={item} className="hero-proof__item">
                    <span />
                    <p>{item}</p>
                  </div>
                ))}
              </div>
            </Reveal>

            <Reveal className="hero-stage" delay={0.08}>
              <div className="hero-stage__surface">
                <div className="hero-stage__poster" aria-hidden="true">
                  <img src={heroArt} alt="" className="hero-stage__glyph" />
                  <div className="hero-stage__wash" />
                  <p className="hero-stage__poster-label">indie dev. solo stack. clean projects.</p>
                </div>

                <div className="hero-stage__overlay">
                  <div className="hero-stage__caption-row">
                    <p className="hero-stage__caption">KRUD project hygiene</p>
                    <span className="hero-stage__signal">krud org</span>
                  </div>
                  <CommandWindow
                    title="krud org — project scan"
                    label="hygiene"
                    lines={heroLines}
                    footer="Stack detected. Files proposed. You decide what gets written."
                  />
                </div>
              </div>
            </Reveal>
          </div>
        </div>
      </section>

      <section className="section-block">
        <div className="shell editorial-section">
          <Reveal>
            <SectionHeading
              eyebrow="Why Krud"
              title="Every major CLI agent was built for teams. Krud was built for you."
              description="The gap isn't AI in the terminal — it's an AI terminal tool that actually fits how a solo builder works: fast context switches, messy repos, no team to ask."
            />
          </Reveal>

          <div className="workflow-grid">
            {whyLines.map((item, index) => (
              <Reveal key={item.title} delay={index * 0.08} className="workflow-step">
                <span className="workflow-step__index">0{index + 1}</span>
                <h3>{item.title}</h3>
                <p>{item.text}</p>
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
              title="Project hygiene in one command."
              description="Run krud org on any directory. Krud detects your stack, scans for missing structure, and proposes exactly what's needed — .gitignore, README, folders. You approve each file before it's written."
            />
            <ul className="detail-list">
              <li>Stack detection from package.json, requirements.txt, Cargo.toml and more.</li>
              <li>Generates stack-specific .gitignore files — not a generic template.</li>
              <li>Works standalone — no chat session needed. Runs in under 10 seconds.</li>
            </ul>
            <div className="button-row">
              <Link to="/features" className="button button-secondary">
                <FolderKanban size={15} />
                See all features
              </Link>
            </div>
          </Reveal>

          <Reveal delay={0.1}>
            <CommandWindow
              title="krud org"
              label="project scan"
              lines={orgLines}
              footer="The .gitignore knows your stack. The README has a placeholder. Done."
            />
          </Reveal>
        </div>
      </section>

      <section className="section-block">
        <div className="shell split-section is-reverse">
          <Reveal>
            <SectionHeading
              eyebrow="krud chat"
              title="Ask for the outcome. Skip the docs rabbit hole."
              description="When you're deep in a problem, describe what you need. Krud returns a reviewable command plan with rationale and risk level — nothing runs silently."
            />
            <ul className="detail-list">
              <li>Risk-aware approvals — destructive commands always pause for confirmation.</li>
              <li>Queue long jobs to the background daemon without losing your foreground shell.</li>
              <li>Session history means the next question picks up where you left off.</li>
            </ul>
          </Reveal>

          <Reveal delay={0.1}>
            <CommandWindow
              title="krud chat"
              label="command plan"
              lines={chatLines}
              footer="Plain language in. Reviewable shell plan out."
            />
          </Reveal>
        </div>
      </section>

      <section className="section-block">
        <div className="shell">
          <Reveal className="cta-band">
            <div className="cta-band__copy">
              <p className="section-eyebrow">Get started</p>
              <h2>Install it, point it at a real project, and run krud org.</h2>
              <p>
                The best proof is immediate: one command on a real project and you'll
                know whether Krud earns a place in your daily workflow.
              </p>
            </div>
            <div className="cta-band__actions">
              <Link to="/docs" className="button button-primary">
                Installation guide
                <ArrowRight size={15} />
              </Link>
              <Link to="/features" className="button button-secondary">
                See what it does
              </Link>
            </div>
            <MotionDiv
              className="cta-band__seal"
              initial={{ opacity: 0, scale: 0.92 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true, amount: 0.5 }}
              transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
            >
              <ShieldCheck size={18} />
              Nothing runs without your approval
            </MotionDiv>
          </Reveal>
        </div>
      </section>
    </>
  );
}
