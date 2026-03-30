import React from 'react';
import { PageIntro, Reveal } from '../components/ui';

export default function Privacy() {
  return (
    <>
      <PageIntro
        eyebrow="Legal"
        title="Privacy Policy"
        description="The privacy page now matches the rest of the product surface while staying concise and readable."
        aside={<div className="meta-panel"><p>Last updated: October 2025</p></div>}
      />

      <section className="section-block">
        <div className="shell legal-layout">
          {[
            {
              title: 'Data collection',
              text: 'Krud AI should only collect what it needs to operate: prompts, basic operational logs, and minimal environment metadata required to support the workflow.',
            },
            {
              title: 'How data is used',
              text: 'Prompt and usage data are used to fulfill the request, return the result, and maintain essential account or billing state where applicable.',
            },
            {
              title: 'Telemetry',
              text: 'Operational telemetry may be used to keep the service reliable. Product settings should make that behavior visible and, where supported, configurable.',
            },
            {
              title: 'Third-party providers',
              text: 'Model and infrastructure providers may process data as part of fulfilling a request. Product messaging should stay explicit about that boundary.',
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
