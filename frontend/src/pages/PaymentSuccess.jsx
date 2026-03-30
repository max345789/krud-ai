import React from 'react';
import { ArrowRight, CircleCheckBig } from 'lucide-react';
import { Link, useSearchParams } from 'react-router-dom';
import { CopyCommand, PageIntro, Reveal, SectionHeading } from '../components/ui';

export default function PaymentSuccess() {
  const [params] = useSearchParams();
  const account = params.get('email');
  const plan = params.get('plan') ?? 'Pro';

  return (
    <>
      <PageIntro
        eyebrow="Payment success"
        title="You are clear to get back to the terminal."
        description="This route now gives checkout returns a proper landing surface: confirmation, next steps, and a clean path back into the product loop."
        aside={
          <div className="meta-panel">
            <p>Plan: {plan}</p>
            {account ? <p>Account: {account}</p> : null}
            <p>Next best move: open the shell and keep working.</p>
          </div>
        }
      />

      <section className="section-block">
        <div className="shell split-section">
          <Reveal className="success-panel">
            <span className="status-pill">
              <CircleCheckBig size={14} />
              Payment recorded
            </span>
            <SectionHeading
              eyebrow="Next move"
              title="Return to the command line and keep the rhythm."
              description="A good success page closes the loop quickly. You do not need another sales pitch after checkout."
            />
            <CopyCommand command="krud chat" label="Resume in the shell" />
            <div className="button-row">
              <Link to="/docs#login" className="button button-primary">
                Login and continue
                <ArrowRight size={15} />
              </Link>
              <Link to="/billing" className="button button-secondary">
                Billing overview
              </Link>
            </div>
          </Reveal>

          <Reveal delay={0.08} className="story-panel">
            <p className="story-kicker">What this unlocks</p>
            <ul className="plan-list">
              <li>Higher-confidence daily use, with more budget and clearer operational continuity.</li>
              <li>A proper return path from checkout into docs, billing, and the shell itself.</li>
              <li>A product story that stays consistent after someone decides to pay.</li>
            </ul>
          </Reveal>
        </div>
      </section>
    </>
  );
}
