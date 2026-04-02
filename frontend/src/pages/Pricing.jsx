import React, { useState } from 'react';
import { ArrowRight, BadgeCheck, LifeBuoy } from 'lucide-react';
import { Link } from 'react-router-dom';
import { PageIntro, Reveal, SectionHeading } from '../components/ui';

const plans = [
  {
    name: 'Solo',
    price: { monthly: 0, yearly: 0 },
    highlight: false,
    cta: 'Read docs',
    ctaTo: '/docs',
    description: 'Try the full workflow. No card required.',
    features: [
      'krud org — project hygiene scans',
      'krud chat — command proposals',
      'Trial token budget (14 days)',
      'Approval-gated execution',
      'Single machine',
    ],
  },
  {
    name: 'Builder',
    price: { monthly: 12, yearly: 10 },
    highlight: true,
    badge: 'For daily use',
    cta: 'Start trial',
    ctaTo: '/billing',
    description: 'For indie devs who use Krud every day.',
    features: [
      'Everything in Solo',
      'Full token budget (no daily cap)',
      'Unlimited project scans',
      'Full command history',
      'Priority model access',
      'Billing portal',
    ],
  },
  {
    name: 'Team',
    price: { monthly: 29, yearly: 24 },
    highlight: false,
    cta: 'Contact us',
    ctaTo: '/contact',
    description: 'For small teams standardising on Krud.',
    features: [
      'Everything in Builder',
      'Shared workflow templates',
      'Rollout support',
      'Priority escalation',
      'Custom usage guidance',
    ],
  },
];

const faqs = [
  {
    q: 'Do I need to pay to try krud org?',
    a: 'No. The Solo plan is free and includes full access to krud org project hygiene scans for 14 days. No card required.',
  },
  {
    q: 'What does Builder mainly unlock?',
    a: 'The full token budget so you can use krud chat all day without hitting a cap, plus unlimited project scans and full command history.',
  },
  {
    q: 'Is Krud only for Node.js and Python?',
    a: 'Those are the stacks Krud knows best — stack detection, tailored .gitignore generation, and project structure suggestions are tuned for them. Rust, Go, and others are supported but the hygiene proposals are less opinionated.',
  },
  {
    q: 'How does the 14-day trial work?',
    a: 'Install, sign in from the CLI, and you get Builder-level access for 14 days. After that, the free Solo plan stays available with a token budget suitable for occasional use.',
  },
];

export default function Pricing() {
  const [yearly, setYearly] = useState(false);

  return (
    <>
      <PageIntro
        eyebrow="Pricing"
        title="Simple pricing for solo builders."
        description="No seat math. No enterprise tiers hiding the good stuff. Pick the plan that matches how deeply Krud sits in your daily workflow."
        aside={
          <div className="meta-panel">
            <p>
              The Solo plan gives you the full workflow for free — including krud org.
            </p>
            <p>
              Builder unlocks the token budget for daily use without hitting a wall.
            </p>
          </div>
        }
      />

      <section className="section-block">
        <div className="shell">
          <div className="billing-toggle">
            <span>{yearly ? 'Yearly billing selected' : 'Monthly billing selected'}</span>
            <button
              type="button"
              className={`billing-toggle__switch ${yearly ? 'is-yearly' : ''}`}
              onClick={() => setYearly((value) => !value)}
              aria-label="Toggle billing cadence"
            >
              <span />
            </button>
            <span>{yearly ? 'Approx. 20% lower monthly rate' : 'Switch to yearly to reduce cost'}</span>
          </div>

          <div className="pricing-grid pricing-grid--spaced">
            {plans.map((plan, index) => (
              <Reveal
                key={plan.name}
                delay={index * 0.08}
                className={`plan-column ${plan.highlight ? 'is-featured' : ''}`}
              >
                {plan.badge ? (
                  <span className="plan-column__label">
                    <BadgeCheck size={15} />
                    {plan.badge}
                  </span>
                ) : null}
                <h3>{plan.name}</h3>
                <p>{plan.description}</p>
                <div className="plan-column__price">
                  ${yearly ? plan.price.yearly : plan.price.monthly}
                  <span>/mo</span>
                </div>
                <ul className="plan-list">
                  {plan.features.map((feature) => (
                    <li key={feature}>{feature}</li>
                  ))}
                </ul>
                <div className="button-row">
                  <Link
                    to={plan.ctaTo}
                    className={`button ${plan.highlight ? 'button-primary' : 'button-secondary'}`}
                  >
                    {plan.cta}
                  </Link>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section className="section-block">
        <div className="shell split-section">
          <Reveal>
            <SectionHeading
              eyebrow="How to decide"
              title="Start with Solo. Upgrade when Krud becomes part of your daily flow."
              description="The upgrade moment is clear: when you hit the token cap and want to keep going, Builder is the right move."
            />
            <ul className="comparison-list">
              <li>
                <strong>Solo (free):</strong> install, run krud org, validate the whole workflow during your 14-day trial.
              </li>
              <li>
                <strong>Builder ($12/mo):</strong> use krud chat and krud org every day without limits.
              </li>
              <li>
                <strong>Team ($29/mo):</strong> standardise the tool across a small team with rollout support.
              </li>
            </ul>
          </Reveal>

          <Reveal delay={0.1} className="story-panel">
            <p className="story-kicker">What the Builder plan is for</p>
            <ul className="plan-list">
              <li>Running krud org on every new project without thinking about it.</li>
              <li>Using krud chat throughout a full work session, not just occasionally.</li>
              <li>Keeping full command history so context carries across sessions.</li>
            </ul>
            <div className="button-row">
              <Link to="/billing" className="button button-secondary">
                Start 14-day trial
              </Link>
            </div>
          </Reveal>
        </div>
      </section>

      <section className="section-block">
        <div className="shell">
          <Reveal>
            <SectionHeading
              eyebrow="FAQ"
              title="Quick answers before you install."
              description="These are the questions worth settling before Krud becomes part of your workflow."
            />
          </Reveal>
          <div className="faq-list">
            {faqs.map((item, index) => (
              <Reveal key={item.q} delay={index * 0.06} className="faq-item">
                <h3>{item.q}</h3>
                <p>{item.a}</p>
              </Reveal>
            ))}
          </div>
          <div className="button-row">
            <Link to="/contact" className="button button-primary">
              Questions? Contact us
              <ArrowRight size={15} />
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
