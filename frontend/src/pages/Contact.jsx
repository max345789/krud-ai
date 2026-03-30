import React from 'react';
import { ArrowUpRight, LifeBuoy, Mail } from 'lucide-react';
import {
  REPO_URL,
  SUPPORT_EMAIL,
  SUPPORT_MAILTO,
  TEAM_ROLLOUT_MAILTO,
} from '../content/site';
import { PageIntro, Reveal, SectionHeading } from '../components/ui';

export default function Contact() {
  return (
    <>
      <PageIntro
        eyebrow="Contact"
        title="Talk to the people shipping the shell."
        description="Every path on this page does something real: email, rollout conversation, or direct code-level context. No dead-end form, no hollow CTA."
        aside={
          <div className="meta-panel">
            <p>
              If you need help, the fastest support loop is still specific context:
              what you ran, what you expected, and what actually happened.
            </p>
          </div>
        }
      />

      <section className="section-block">
        <div className="shell contact-grid">
          <Reveal className="contact-channel">
            <strong>General product help</strong>
            <p>Questions about installation, login, pricing, or rollout.</p>
            <div className="button-row">
              <a href={SUPPORT_MAILTO} className="button button-primary">
                <Mail size={15} />
                {SUPPORT_EMAIL}
              </a>
            </div>
          </Reveal>

          <Reveal delay={0.06} className="contact-channel">
            <strong>Team rollout</strong>
            <p>Use the same support path with context about team size and operating model.</p>
            <div className="button-row">
              <a href={TEAM_ROLLOUT_MAILTO} className="button button-secondary">
                <LifeBuoy size={15} />
                Discuss rollout
              </a>
            </div>
          </Reveal>

          <Reveal delay={0.12} className="contact-channel">
            <strong>Repository and implementation</strong>
            <p>Use the open-source repo when you want to inspect the current product surface.</p>
            <div className="button-row">
              <a
                href={REPO_URL}
                target="_blank"
                rel="noreferrer"
                className="button button-secondary"
              >
                Repository
                <ArrowUpRight size={15} />
              </a>
            </div>
          </Reveal>

          <Reveal delay={0.18} className="contact-channel">
            <strong>Best-response format</strong>
            <p>Include the command you ran, the expected outcome, and the result you saw.</p>
            <ul className="availability-list">
              <li>Command or request that triggered the issue</li>
              <li>Current OS and shell</li>
              <li>Any backend or daemon logs that already narrowed the problem</li>
            </ul>
          </Reveal>
        </div>
      </section>

      <section className="section-block">
        <div className="shell split-section">
          <Reveal>
            <SectionHeading
              eyebrow="Why this matters"
              title="Support should feel like a handoff, not a maze."
              description="When the route is explicit, people ask better questions and the team answering them starts closer to the real issue."
            />
          </Reveal>

          <Reveal delay={0.1} className="story-panel">
            <p className="story-kicker">Response guidance</p>
            <ul className="plan-list">
              <li>Use email for help that needs context or a follow-up thread.</li>
              <li>Use the repo for implementation details, issues, and code-level review.</li>
              <li>Use the pricing and docs pages first if the question is about adoption flow.</li>
            </ul>
          </Reveal>
        </div>
      </section>
    </>
  );
}
