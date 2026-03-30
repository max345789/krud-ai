import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Bot } from 'lucide-react';
import { Link } from 'react-router-dom';
import heroArt from '../assets/hero.png';
import { INSTALL_COMMAND } from '../content/site';
import { CommandWindow, CopyCommand, Reveal, SectionHeading } from '../components/ui';

const heroLines = [
  { kind: 'command', text: 'krud chat' },
  { kind: 'prompt', text: 'audit why the staging daemon stopped processing jobs' },
  { kind: 'agent', text: 'Checking launchd status, local queue, and recent logs...' },
  { kind: 'output', text: 'launchctl print gui/501/in.dabcloud.krudd | rg "state|last exit"' },
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
    title: 'Say what you need',
    text: 'Start with the outcome in plain language. Krud handles the shell recall so you can stay with the real problem.',
  },
  {
    title: 'Pause at the edge',
    text: 'Inspection can stay fast. Risky work stops at a review boundary so the operator keeps final control.',
  },
  {
    title: 'Keep the receipt',
    text: 'The result comes back as a readable explanation with enough history to continue later without guessing.',
  },
];

const productFacts = [
  {
    title: 'Device-code auth',
    text: 'Sign in from the terminal with a browser checkpoint instead of pasted tokens or extension handshakes.',
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

const stageDetails = [
  {
    title: 'For on-call fixes',
    text: 'A calmer first response when the system is loud and the operator should not have to be.',
  },
  {
    title: 'For repeatable runbooks',
    text: 'Queue long work into the daemon and keep the terminal free for the next call.',
  },
  {
    title: 'For human memory',
    text: 'Keep enough trail to return tomorrow without rebuilding the whole context from scratch.',
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
              For people who still love the shell
            </p>
            <h1>The terminal, but with memory, restraint, and a pulse.</h1>
            <p className="hero-lead">
              Ask for the outcome in plain language. Krud plans the commands, pauses before
              damage, and keeps a readable trail when the work actually matters.
            </p>

            <div className="hero-actions">
              <CopyCommand command={INSTALL_COMMAND} label="Install Krud" />
              <div className="button-row">
                <Link to="/docs" className="button button-primary">
                  Read the docs
                  <ArrowRight size={15} />
                </Link>
                <Link to="/billing" className="button button-secondary">
                  Start a plan
                </Link>
              </div>
            </div>

            <div className="hero-notes">
              <span className="status-pill">Mac-first CLI</span>
              <span className="status-pill">Human approval before risky moves</span>
              <span className="status-pill">Rust CLI + daemon + FastAPI control plane</span>
            </div>

            <div className="hero-signal-row">
              {stageDetails.map((item) => (
                <div key={item.title} className="hero-signal">
                  <span>{item.title}</span>
                  <p>{item.text}</p>
                </div>
              ))}
            </div>
          </Reveal>

          <Reveal className="hero-stage" delay={0.1}>
            <div className="hero-stage__surface">
              <div className="hero-stage__art" aria-hidden="true">
                <img src={heroArt} alt="" className="hero-stage__glyph" />
                <span className="hero-stage__caption">
                  built for the long way home from a broken deploy
                </span>
              </div>

              <CommandWindow
                title="krud operator session"
                label="live"
                lines={heroLines}
                footer="Command proposals, usage budgets, and session history stay visible after the answer."
              />

              <MotionDiv
                className="hero-stage__meta"
                initial={{ opacity: 0, y: 18 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              >
                <p className="story-kicker">Tonight&apos;s rhythm</p>
                <ul className="hero-stage__list">
                  <li>
                    <strong>Ask once.</strong>
                    <span>Let the product translate intent into shell-safe moves.</span>
                  </li>
                  <li>
                    <strong>Review before damage.</strong>
                    <span>Approval stays part of the experience, not a patch on top.</span>
                  </li>
                  <li>
                    <strong>Keep the trail.</strong>
                    <span>Readable receipts matter when the next shift picks the work back up.</span>
                  </li>
                </ul>
              </MotionDiv>
            </div>
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
              title="Three beats, one rhythm."
              description="Describe the outcome, review the plan, then read the receipt. Every useful part of the product supports that same cadence."
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
              title="Confidence grows when the product pauses at the right moment."
              description="Krud is designed around approvals and readable proposals. The point is not to feel magical. The point is to feel dependable."
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
              footer="The sharpest interface choice is often the moment where the human stays in control."
            />
          </Reveal>
        </div>
      </section>

      <section className="section-block">
        <div className="shell split-section is-reverse">
          <Reveal>
            <SectionHeading
              eyebrow="Background work"
              title="Let the long jobs keep moving after you close the lid."
              description="The daemon path matters because terminal UX is not only about command generation. It is about staying responsive while the work continues."
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
              title="Proof, not posture."
              description="The backend and CLI already support the claims on this page, which means the interface can stay calm and specific instead of decorative."
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
              title="This site now reflects the product that actually exists."
              description="The strongest public surface is the one that respects the truth of the repo: CLI, daemon, device auth, billing, and release metadata all belong to the same story."
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
              title="Install it, point it at something messy, and see if it earns a place in your shell."
              description="The fastest path is still the clearest one: install, run krud login, approve the device, and ask for something that would normally cost you ten minutes of shell recall."
            />
            <div className="cta-band__actions">
              <Link to="/docs" className="button button-primary">
                Open installation guide
              </Link>
              <Link to="/features" className="button button-secondary">
                See the capability map
              </Link>
            </div>
          </Reveal>
        </div>
      </section>
    </>
  );
}
