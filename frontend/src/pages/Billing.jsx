import React from 'react';
import { ArrowRight, BadgeCheck, CreditCard, LifeBuoy, ShieldCheck } from 'lucide-react';
import { Link, useSearchParams } from 'react-router-dom';
import { INSTALL_COMMAND, SUPPORT_EMAIL, SUPPORT_MAILTO } from '../content/site';
import { CopyCommand, PageIntro, Reveal, SectionHeading } from '../components/ui';

export default function Billing() {
  const [params] = useSearchParams();
  const returnedEmail = params.get('email');
  const returnedStatus = params.get('status') ?? 'Account-gated';

  return (
    <>
      <PageIntro
        eyebrow="Billing"
        title="Keep the money side as calm as the shell."
        description="This route is the bridge between pricing, checkout returns, and support. It now exists as a real part of the site instead of a dead redirect target."
        aside={
          <div className="meta-panel">
            <p>Billing is attached to authenticated operator sessions.</p>
            <p>Status: {returnedStatus}</p>
            {returnedEmail ? <p>Account: {returnedEmail}</p> : null}
          </div>
        }
      />

      <section className="section-block">
        <div className="shell split-section">
          <Reveal>
            <SectionHeading
              eyebrow="How it works"
              title="Use the CLI to establish trust, then manage the plan here."
              description="Krud is built so billing follows a real operator identity. The cleanest flow is: install, run device login, then return to pricing or checkout with a known session."
            />
            <ul className="detail-list">
              <li>Start from the shell with <span className="inline-code">krud login</span>.</li>
              <li>Approve the device in the browser when prompted.</li>
              <li>Return to checkout or the billing portal once the session exists.</li>
            </ul>
            <div className="button-row">
              <Link to="/pricing" className="button button-primary">
                Compare plans
                <ArrowRight size={15} />
              </Link>
              <Link to="/docs#login" className="button button-secondary">
                Device login guide
              </Link>
            </div>
          </Reveal>

          <Reveal delay={0.08} className="billing-panel">
            <div className="billing-panel__row">
              <span className="status-pill">
                <BadgeCheck size={14} />
                Pro unlocks deeper daily use
              </span>
            </div>
            <div className="billing-panel__rail">
              <div>
                <strong>What you are paying for</strong>
                <p>History, budget headroom, clearer receipts, and support for real operator work.</p>
              </div>
              <div>
                <strong>What stays the same</strong>
                <p>The terminal remains the primary surface. The browser is still there to confirm and orient.</p>
              </div>
              <div>
                <strong>If something goes sideways</strong>
                <p>Use the billing route or support email instead of guessing which page should handle it.</p>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      <section className="section-block">
        <div className="shell split-section is-reverse">
          <Reveal>
            <SectionHeading
              eyebrow="Operator path"
              title="The shortest useful loop still starts in the terminal."
              description="Billing should support the product rhythm, not interrupt it. Install, authenticate, then keep going."
            />
            <CopyCommand command={INSTALL_COMMAND} label="Install command" />
          </Reveal>

          <Reveal delay={0.08} className="story-panel">
            <p className="story-kicker">Need help?</p>
            <ul className="plan-list">
              <li>
                <CreditCard size={15} style={{ marginRight: '0.45rem', verticalAlign: 'text-bottom' }} />
                Use this route when a checkout or return URL lands you back on the site.
              </li>
              <li>
                <ShieldCheck size={15} style={{ marginRight: '0.45rem', verticalAlign: 'text-bottom' }} />
                If the session is not authenticated yet, start with device login.
              </li>
              <li>
                <LifeBuoy size={15} style={{ marginRight: '0.45rem', verticalAlign: 'text-bottom' }} />
                For billing questions, email {SUPPORT_EMAIL}.
              </li>
            </ul>
            <div className="button-row">
              <a href={SUPPORT_MAILTO} className="button button-secondary">
                Billing support
              </a>
            </div>
          </Reveal>
        </div>
      </section>
    </>
  );
}
