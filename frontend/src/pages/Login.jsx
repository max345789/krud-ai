import React from 'react';
import { ArrowRight, Command, LockKeyhole } from 'lucide-react';
import { Link } from 'react-router-dom';
import { CommandWindow, PageIntro, Reveal, SectionHeading } from '../components/ui';

export default function Login() {
  return (
    <>
      <PageIntro
        eyebrow="Access"
        title="The terminal is the front door."
        description="Krud feels best when access starts where the work starts: in the shell. The browser only steps in to confirm the device and then gets out of the way."
        aside={
          <div className="meta-panel">
            <p>
              Run <span className="inline-code">krud login</span>, approve the session,
              and come straight back to the terminal. That is the whole rhythm.
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
              title="Less pretending creates more trust."
              description="A terminal-native product should not ask people to guess whether the real workflow lives in the browser or the shell. This page makes the boundary clear."
            />
            <ul className="detail-list">
              <li>Every visible action maps to a real capability in the repo.</li>
              <li>The browser helps confirm identity without becoming a second product.</li>
              <li>The site stays aligned with the backend and CLI architecture that already exists.</li>
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
