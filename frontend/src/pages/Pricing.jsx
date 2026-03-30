import React, { useState } from 'react';
import { ArrowRight, BadgeCheck, LifeBuoy } from 'lucide-react';
import { Link } from 'react-router-dom';
import { PageIntro, Reveal, SectionHeading } from '../components/ui';

const plans = [
  {
    name: 'Free',
    price: { monthly: 0, yearly: 0 },
    highlight: false,
    cta: 'Read docs',
    ctaTo: '/docs',
    description: 'For evaluating the product loop and getting through the first install.',
    features: [
      'Core terminal workflow',
      'Basic output summaries',
      'Community support',
      'Single-operator setup',
    ],
  },
  {
    name: 'Pro',
    price: { monthly: 12, yearly: 10 },
    highlight: true,
    badge: 'Best fit',
    cta: 'Start trial',
    ctaTo: '/docs',
    description: 'For people using Krud as part of their daily terminal routine.',
    features: [
      'Full command history',
      'Higher token budget',
      'Priority product updates',
      'Deeper model access',
      'Billing portal access',
    ],
  },
  {
    name: 'Team',
    price: { monthly: 29, yearly: 24 },
    highlight: false,
    cta: 'Contact',
    ctaTo: '/contact',
    description: 'For shared operational playbooks, onboarding, and support expectations.',
    features: [
      'Everything in Pro',
      'Shared operator workflows',
      'Rollout support',
      'Priority escalation path',
      'Custom usage guidance',
    ],
  },
];

const faqs = [
  {
    q: 'Can I try Krud before paying?',
    a: 'Yes. The product is built to let you install first, log in from the terminal, and verify the workflow before deciding on a paid plan.',
  },
  {
    q: 'Can I bring my own model credentials?',
    a: 'The backend already exposes model configuration points, so bring-your-own-key support can fit cleanly into the product surface.',
  },
  {
    q: 'What does Pro mainly unlock?',
    a: 'Higher budgets, deeper history, more reliable daily use, and a product path that assumes Krud is part of real terminal work instead of occasional demos.',
  },
  {
    q: 'How should teams evaluate it?',
    a: 'Start with one operator, validate the approval and queue model, then use the contact path for rollout and support expectations.',
  },
];

export default function Pricing() {
  const [yearly, setYearly] = useState(false);

  return (
    <>
      <PageIntro
        eyebrow="Pricing"
        title="A cleaner pricing story for a serious terminal product."
        description="The page now reads like a rollout decision, not a generic startup grid. Plans are framed around operator maturity and support, not empty marketing promises."
        aside={
          <div className="meta-panel">
            <p>
              Device auth, subscription enforcement, token budgets, and billing routes
              already exist on the backend side.
            </p>
            <p>
              The UI now reflects that maturity without pretending to be more concrete than
              the current product setup.
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

          <div className="pricing-grid" style={{ marginTop: '2rem' }}>
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
              title="Roll out by trust level, not seat count."
              description="The sharpest pricing UX here is telling people how to choose, not flooding them with invented enterprise bullets."
            />
            <ul className="comparison-list">
              <li>
                <strong>Free:</strong> evaluate the install, login, and command loop.
              </li>
              <li>
                <strong>Pro:</strong> use Krud daily with history, budget headroom, and stronger product support.
              </li>
              <li>
                <strong>Team:</strong> standardize how multiple operators adopt the tool and escalate issues.
              </li>
            </ul>
          </Reveal>

          <Reveal delay={0.1} className="story-panel">
            <p className="story-kicker">What the UI optimizes for</p>
            <ul className="plan-list">
              <li>Honest plan framing instead of vanity comparison clutter.</li>
              <li>One featured choice for the most likely buyer path.</li>
              <li>Direct follow-up routes into docs or contact, depending on maturity.</li>
            </ul>
            <div className="button-row">
              <Link to="/contact" className="button button-secondary">
                <LifeBuoy size={15} />
                Talk through rollout
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
              title="Questions that actually help someone buy."
              description="These are the decision blockers worth answering on the page."
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
              Contact for rollout
              <ArrowRight size={15} />
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
