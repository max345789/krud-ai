import React from 'react';
import {
  ArrowRight,
  Command,
  LockKeyhole,
  ReceiptText,
  ScanSearch,
  Server,
  Waypoints,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { CommandWindow, PageIntro, Reveal, SectionHeading } from '../components/ui';

const capabilities = [
  {
    icon: <Command size={16} style={{ marginRight: '0.5rem', verticalAlign: 'text-bottom' }} />,
    title: 'Natural-language command proposals',
    text: 'Describe the outcome in product language. Krud turns it into shell work without asking you to translate the request first.',
  },
  {
    icon: <ScanSearch size={16} style={{ marginRight: '0.5rem', verticalAlign: 'text-bottom' }} />,
    title: 'Readable output summaries',
    text: 'After execution, the assistant reads the result and gives the next useful interpretation instead of stopping at stdout.',
  },
  {
    icon: <LockKeyhole size={16} style={{ marginRight: '0.5rem', verticalAlign: 'text-bottom' }} />,
    title: 'Risk-aware approvals',
    text: 'Potentially destructive actions stay reviewable. Approval is a first-class part of the experience, not an afterthought.',
  },
  {
    icon: <Waypoints size={16} style={{ marginRight: '0.5rem', verticalAlign: 'text-bottom' }} />,
    title: 'Queued background execution',
    text: 'Foreground work can move into the daemon queue when the task should continue after the prompt disappears.',
  },
  {
    icon: <Server size={16} style={{ marginRight: '0.5rem', verticalAlign: 'text-bottom' }} />,
    title: 'Account, billing, and release control plane',
    text: 'The backend already exposes device auth, subscription checks, release metadata, and chat session orchestration.',
  },
  {
    icon: <ReceiptText size={16} style={{ marginRight: '0.5rem', verticalAlign: 'text-bottom' }} />,
    title: 'Persistent operator trail',
    text: 'Sessions, token usage, and command history stay attached so the next interaction starts with context instead of guesswork.',
  },
];

export default function Features() {
  return (
    <>
      <PageIntro
        eyebrow="Capabilities"
        title="Everything the product does to keep operators calm under pressure."
        description="Krud is not trying to replace the shell. It is trying to make the shell feel steadier: clearer plans, safer approvals, stronger memory, and a control plane that backs the story up."
        aside={
          <div className="meta-panel">
            <p>
              The product already spans a Rust CLI, a background daemon, and a FastAPI
              control plane. The public site should feel like those pieces belong to the
              same instrument.
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
                <strong>
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
              eyebrow="Context aware"
              title="Describe it once. Let the product carry the syntax."
              description="The site should communicate the operational value clearly: Krud absorbs shell recall so the operator can stay focused on the result."
            />
            <ul className="detail-list">
              <li>Shell-aware command planning keeps the operator out of documentation rabbit holes.</li>
              <li>Device-code auth makes terminal sign-in feel native instead of bolted on.</li>
              <li>The surface stays text-first, with just enough structure to orient the next action.</li>
            </ul>
          </Reveal>

          <Reveal delay={0.1}>
            <CommandWindow
              title="planning example"
              label="translation"
              lines={[
                { kind: 'prompt', text: 'compress the logs folder and upload it to S3' },
                { kind: 'agent', text: 'Generating a shell-safe archive command and upload step...' },
                { kind: 'output', text: 'tar -czf logs.tar.gz ./logs && aws s3 cp logs.tar.gz s3://bucket/logs/' },
                { kind: 'success', text: 'Ready for approval and execution.' },
              ]}
            />
          </Reveal>
        </div>
      </section>

      <section className="section-block">
        <div className="shell split-section is-reverse">
          <Reveal>
            <SectionHeading
              eyebrow="Readable receipts"
              title="The result comes back in product language."
              description="People do not need another raw-terminal wrapper. They need a trustworthy explanation of what happened and what to do next."
            />
            <ul className="detail-list">
              <li>Outputs are summarized so the next step is obvious.</li>
              <li>Errors become diagnosis, not just logs.</li>
              <li>Session history means the agent can continue from the last operational state.</li>
            </ul>
          </Reveal>

          <Reveal delay={0.1}>
            <CommandWindow
              title="analysis example"
              label="receipt"
              lines={[
                { kind: 'prompt', text: 'why is nginx returning 502?' },
                { kind: 'agent', text: 'Checking upstream health and the recent error log...' },
                { kind: 'output', text: 'upstream connect() failed (111: Connection refused)' },
                { kind: 'success', text: 'The backend on :3000 is down. Restart it to clear the 502.' },
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
              eyebrow="Next step"
              title="Read the flow, then give it a real problem."
              description="The best feature proof is still firsthand use: install, log in, and ask for something that normally costs you ten minutes of shell recall."
            />
            <div className="cta-band__actions">
              <Link to="/docs" className="button button-primary">
                Installation and docs
                <ArrowRight size={15} />
              </Link>
              <Link to="/billing" className="button button-secondary">
                Billing and plans
              </Link>
            </div>
          </Reveal>
        </div>
      </section>
    </>
  );
}
