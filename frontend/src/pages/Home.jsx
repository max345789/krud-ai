import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Bot } from 'lucide-react';
import { Link } from 'react-router-dom';
import { CommandWindow, CopyCommand, Reveal, SectionHeading } from '../components/ui';

const installCommand = 'curl -fsSL https://install.krud.ai | sh';

const heroLines = [
  { kind: 'command', text: 'krud chat' },
  { kind: 'prompt', text: 'audit why the staging daemon stopped processing jobs' },
  { kind: 'agent', text: 'Checking launchd status, local queue, and recent logs...' },
  { kind: 'output', text: 'launchctl print gui/501/in.krud.ai | rg "state|last exit"' },
  { kind: 'success', text: 'Daemon stalled after a socket timeout. Restart queued safely.' },
];

const reviewLines = [
  { kind: 'prompt', text: 'prune docker images older than 30 days' },
  { kind: 'agent', text: 'Proposed destructive command detected. Approval required.' },
  { kind: 'output', text: 'docker image prune -a --filter "until=720h"' },
  { kind: 'success', text: 'User confirmed. 13.2 GB reclaimed. Summary written to history.' },
];

const daemonLines = [
  { kind: 'command', text: 'krud run "nightly content plan for all active clients"' },
  { kind: 'agent', text: 'Queued for krudd. You can close the terminal.' },
  { kind: 'output', text: 'sqlite3 ~/.krud/local.db "select id,status from local_tasks limit 3"' },
  { kind: 'success', text: 'Background daemon picked it up and streamed logs back into the session.' },
];

const workflow = [
  {
    title: 'State the outcome',
    text: 'Describe the result you need in plain language. Krud translates that request into shell actions with context.',
  },
  {
    title: 'Review the plan',
    text: 'Risky operations stop for confirmation. Safe tasks can run now or move into the daemon queue.',
  },
  {
    title: 'Read the receipt',
    text: 'Krud explains what happened, records usage, and keeps enough history to continue the thread later.',
  },
];

const productFacts = [
  {
    title: 'Device-code auth',
    text: 'Sign in from the terminal with browser approval. No pasted tokens or extension handshakes.',
  },
  {
    title: 'Approval before damage',
    text: 'Destructive commands stay gated. The product is designed around review, not blind execution.',
  },
  {
    title: 'Daemon queue',
    text: 'Long-running work can leave the foreground and continue through the local background daemon.',
  },
  {
    title: 'Release manifests',
    text: 'The CLI can discover signed release artifacts and pull the right binary for the current machine.',
  },
];

const proofItems = [
  {
    title: 'Local history and token accounting',
    text: 'Sessions, command proposals, and token budgets are tracked so the operator can decide with context.',
  },
  {
    title: 'FastAPI control plane',
    text: 'Account, billing, device auth, release metadata, and chat sessions already exist in the backend.',
  },
  {
    title: 'Rust CLI plus daemon',
    text: 'The product surface is not a mockup. It already has a CLI, a background process, and an installer path.',
  },
];

const tapeItems = [
  'krud chat "trace why nginx is returning 502"',
  'krud run "nightly deploy sanity checks"',
  'krud chat "find all containers using more than 1GB"',
  'krud status',
  'krud daemon install',
  'krud chat "summarize the last failed build"',
];

export default function Home() {
  const MotionDiv = motion.div;

  return (
    <>
      <section className="hero-shell">
        <div className="shell hero-grid">
          <Reveal className="hero-copy">
            <p className="hero-kicker">
              <Bot size={14} />
              Terminal-native operator loop
            </p>
            <h1>The terminal agent that gets real work done.</h1>
            <p className="hero-lead">
              Krud takes the full loop, not just autocomplete: plan the command, ask
              before risky changes, execute in context, read the output, and keep the
              trail visible.
            </p>

            <div className="hero-actions">
              <CopyCommand command={installCommand} label="Install Krud" />
              <div className="button-row">
                <Link to="/docs" className="button button-primary">
                  Read the docs
                  <ArrowRight size={15} />
                </Link>
                <Link to="/pricing" className="button button-secondary">
                  View pricing
                </Link>
              </div>
            </div>

            <div className="hero-notes">
              <span className="status-pill">Mac-first CLI</span>
              <span className="status-pill">Browser approval only when needed</span>
              <span className="status-pill">Rust CLI + daemon + FastAPI control plane</span>
            </div>
          </Reveal>

          <Reveal className="hero-stage" delay={0.1}>
            <CommandWindow
              title="krud operator session"
              label="live"
              lines={heroLines}
              footer="Command proposals, usage budgets, and session history stay visible after the answer."
            />
            <MotionDiv
              className="hero-stage__note"
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
            >
              <strong>Built for operators, not screenshots.</strong>
              <p>
                Device auth, daemon queueing, billing hooks, and release manifests are
                already part of the product surface.
              </p>
            </MotionDiv>
          </Reveal>
        </div>

        <div className="command-tape">
          <div className="command-tape__track">
            {[...tapeItems, ...tapeItems].map((item, index) => (
              <span key={`${item}-${index}`} className="command-tape__item">
                {item}
              </span>
            ))}
          </div>
        </div>
      </section>

      <section className="section-block">
        <div className="shell">
          <Reveal>
            <SectionHeading
              eyebrow="The loop"
              title="One product idea, end to end."
              description="Describe the outcome, review the command, then read a clean receipt. Every section of the product supports that same flow."
              align="center"
            />
          </Reveal>

          <div className="workflow-grid">
            {workflow.map((item, index) => (
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
              eyebrow="Risk handling"
              title="Risky work stays reviewable."
              description="Krud is designed around approvals and readable proposals. That makes the UI sharper, because the product never asks the operator to trust a black box."
            />
            <ul className="detail-list">
              <li>Destructive commands can stop for Y/N confirmation before execution.</li>
              <li>Command proposals carry rationale and risk level alongside the shell text.</li>
              <li>Results return as a readable summary, not just raw terminal noise.</li>
            </ul>
          </Reveal>

          <Reveal delay={0.1}>
            <CommandWindow
              title="approval boundary"
              label="review"
              lines={reviewLines}
              footer="The product respects the moment where a human should stay in control."
            />
          </Reveal>
        </div>
      </section>

      <section className="section-block">
        <div className="shell split-section is-reverse">
          <Reveal>
            <SectionHeading
              eyebrow="Background work"
              title="Foreground focus, background execution."
              description="The CLI can queue long-running tasks into the daemon so the workflow still feels fast even when the work is not."
            />
            <ul className="detail-list">
              <li>The daemon continues jobs while the terminal is free for the next decision.</li>
              <li>Local SQLite state keeps task history, session continuity, and status checks simple.</li>
              <li>The same product language works for ad-hoc fixes and repeatable operational jobs.</li>
            </ul>
          </Reveal>

          <Reveal delay={0.1}>
            <CommandWindow
              title="krudd queue"
              label="background"
              lines={daemonLines}
              footer="Queue now, inspect later, and keep the command trail attached to the session."
            />
          </Reveal>
        </div>
      </section>

      <section className="section-block">
        <div className="shell">
          <Reveal>
            <SectionHeading
              eyebrow="Product depth"
              title="The details already exist."
              description="The backend and CLI already support the product claims, so the UX can be crisp without pretending to do more than it does."
            />
          </Reveal>

          <div className="feature-ledger">
            {productFacts.map((item, index) => (
              <Reveal key={item.title} delay={index * 0.07} className="feature-ledger__item">
                <span className="feature-ledger__index">0{index + 1}</span>
                <strong>{item.title}</strong>
                <p>{item.text}</p>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section className="section-block">
        <div className="shell">
          <Reveal>
            <SectionHeading
              eyebrow="What is real"
              title="This is not a landing page for a concept."
              description="The site now speaks in product truths instead of filler proof. These are already represented in the codebase."
              align="center"
            />
          </Reveal>

          <div className="proof-grid">
            {proofItems.map((item, index) => (
              <Reveal key={item.title} delay={index * 0.08} className="proof-grid__item">
                <strong>{item.title}</strong>
                <p>{item.text}</p>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section className="section-block">
        <div className="shell">
          <Reveal className="cta-band">
            <SectionHeading
              eyebrow="Start here"
              title="Install it, log in from the terminal, and test the loop yourself."
              description="The fastest path is still the clearest one: install, run krud login, approve the device, and ask for something that would normally cost you ten minutes of shell recall."
            />
            <div className="cta-band__actions">
              <Link to="/docs" className="button button-primary">
                Open installation guide
              </Link>
              <Link to="/features" className="button button-secondary">
                See the full capability map
              </Link>
            </div>
          </Reveal>
        </div>
      </section>
    </>
  );
}
