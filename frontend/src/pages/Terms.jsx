import React from 'react';
import { PageIntro, Reveal } from '../components/ui';

export default function Terms() {
  return (
    <>
      <PageIntro
        eyebrow="Legal"
        title="Terms of Service"
        description="Presented in a cleaner legal reading layout so the page feels deliberate instead of copied in from another visual system."
        aside={<div className="meta-panel"><p>Last updated: October 2025</p></div>}
      />

      <section className="section-block">
        <div className="shell legal-layout">
          {[
            {
              title: 'Acceptance',
              text: 'By using Krud AI, you agree to these terms. If you do not agree, do not use the product. Terms may change as the product and operating model evolve.',
            },
            {
              title: 'Service description',
              text: 'Krud AI is a terminal-focused assistant that proposes and helps execute command-line work. It can translate natural language into commands, but it does not guarantee perfect correctness for every output.',
            },
            {
              title: 'Operator responsibility',
              text: 'The product is intentionally built around approvals for risky actions. You remain responsible for reviewing commands and deciding whether they should run in your environment.',
            },
            {
              title: 'Acceptable use',
              text: 'You may not use the product to generate malware, attack systems you do not own or control, or carry out unlawful activity.',
            },
          ].map((section, index) => (
            <Reveal key={section.title} delay={index * 0.07} className="legal-section">
              <h3>{section.title}</h3>
              <p>{section.text}</p>
            </Reveal>
          ))}
        </div>
      </section>
    </>
  );
}
