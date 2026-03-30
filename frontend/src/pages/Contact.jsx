import React from 'react';
import { ArrowUpRight, LifeBuoy, Mail } from 'lucide-react';
import { PageIntro, Reveal, SectionHeading } from '../components/ui';

export default function Contact() {
  return (
    <>
      <PageIntro
        eyebrow="Contact"
        title="Clear channels, no fake form submission."
        description="The previous page looked polished but did not actually connect to anything. This version makes every route actionable and keeps the expectations explicit."
        aside={
          <div className="meta-panel">
            <p>
              The cleanest UX here is honest routing: email when you need help, GitHub when
              you want code-level context, and a direct rollout conversation when you are
              evaluating the product seriously.
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
              <a href="mailto:support@krud.ai" className="button button-primary">
                <Mail size={15} />
                support@krud.ai
              </a>
            </div>
          </Reveal>

          <Reveal delay={0.06} className="contact-channel">
            <strong>Team rollout</strong>
            <p>Use the same support path with context about team size and operating model.</p>
            <div className="button-row">
              <a
                href="mailto:support@krud.ai?subject=Krud%20team%20rollout"
                className="button button-secondary"
              >
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
                href="https://github.com/max345789/krud-ai"
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
              title="Contact UX should reduce support loops."
              description="A dead form looks finished but wastes time. Clear channels make the next move obvious for both the user and the team receiving the message."
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
