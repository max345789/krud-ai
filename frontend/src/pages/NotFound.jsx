import React from 'react';
import { ArrowRight, Compass } from 'lucide-react';
import { Link } from 'react-router-dom';
import { PageIntro, Reveal } from '../components/ui';

export default function NotFound() {
  return (
    <>
      <PageIntro
        eyebrow="404"
        title="That route went dark."
        description="The site now has a real fallback instead of a blank miss. If someone lands on a bad path, the next move is still obvious."
        aside={
          <div className="meta-panel">
            <p>The shell is still here.</p>
            <p>The route you asked for is not.</p>
          </div>
        }
      />

      <section className="section-block">
        <div className="shell">
          <Reveal className="cta-band">
            <p className="story-kicker">Try one of these instead</p>
            <div className="button-row">
              <Link to="/" className="button button-primary">
                Back home
                <ArrowRight size={15} />
              </Link>
              <Link to="/docs" className="button button-secondary">
                Open docs
              </Link>
              <Link to="/blog" className="button button-secondary">
                <Compass size={15} />
                Read the journal
              </Link>
            </div>
          </Reveal>
        </div>
      </section>
    </>
  );
}
