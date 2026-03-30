import React from 'react';
import { ArrowRight, Command, LockKeyhole } from 'lucide-react';
import { Link } from 'react-router-dom';
import { CommandWindow, PageIntro, Reveal, SectionHeading } from '../components/ui';

export default function Login() {
  return (
    <>
      <PageIntro
        eyebrow="Access"
        title="Keep sign-in honest: the terminal is the primary door."
        description="The old page implied a full web-login flow that does not actually exist here. This version makes the product path explicit instead of pushing users into dead-end forms."
        aside={
          <div className="meta-panel">
            <p>
              If you want access today, use the device-code flow from the CLI. That is the
              strongest and clearest product path in the repo.
            </p>
          </div>
        }
      />

      <section className="section-block">
        <div className="shell access-grid">
          <Reveal className="access-panel">
            <SectionHeading
              eyebrow="Recommended path"
              title="Run login from your terminal."
              description="This matches the current product architecture and keeps authentication tied to the session you actually want to use."
            />
            <ul className="detail-list">
              <li>Run <span className="inline-code">krud login</span> in your terminal.</li>
              <li>Approve the device in the browser when prompted.</li>
              <li>Return to the CLI and continue directly into chat or queued work.</li>
            </ul>
            <div className="button-row">
              <Link to="/docs#login" className="button button-primary">
                Read the login guide
                <ArrowRight size={15} />
              </Link>
              <Link to="/pricing" className="button button-secondary">
                Compare plans
              </Link>
            </div>
          </Reveal>

          <Reveal delay={0.1}>
            <CommandWindow
              title="access flow"
              label="device auth"
              lines={[
                { kind: 'command', text: 'krud login' },
                { kind: 'agent', text: 'Generated device code and opened the approval page.' },
                { kind: 'output', text: 'Waiting for browser confirmation...' },
                { kind: 'success', text: 'Session approved. Ready to chat.' },
              ]}
              footer="This is the path worth polishing because it already exists in the product."
            />
          </Reveal>
        </div>
      </section>

      <section className="section-block">
        <div className="shell split-section">
          <Reveal>
            <SectionHeading
              eyebrow="Why this is better"
              title="Good UX removes fake decisions."
              description="A web sign-in form that does nothing is worse than no form. This page now clarifies the path instead of pretending there are multiple entry points."
            />
            <ul className="detail-list">
              <li>Trust goes up because every visible action is real.</li>
              <li>Support load goes down because the next step is unambiguous.</li>
              <li>The site stays aligned with the actual backend and CLI architecture.</li>
            </ul>
          </Reveal>

          <Reveal delay={0.1} className="story-panel">
            <p className="story-kicker">Access notes</p>
            <ul className="plan-list">
              <li>
                <LockKeyhole size={15} style={{ marginRight: '0.45rem', verticalAlign: 'text-bottom' }} />
                Browser approval is only used to confirm the device session.
              </li>
              <li>
                <Command size={15} style={{ marginRight: '0.45rem', verticalAlign: 'text-bottom' }} />
                The product remains terminal-first after authentication.
              </li>
            </ul>
          </Reveal>
        </div>
      </section>
    </>
  );
}
