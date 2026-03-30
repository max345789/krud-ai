import React from 'react';
import { ArrowRight } from 'lucide-react';
import { PageIntro, Reveal } from '../components/ui';

const posts = [
  {
    cat: 'Release',
    title: 'Krud AI v2.0 brings command history, device auth polish, and clearer billing paths',
    excerpt: 'The site and product now tell the same story: install fast, approve safely, read the receipt, and keep long-running work in the daemon queue.',
    date: 'March 2026',
    read: '4 min read',
  },
  {
    cat: 'Engineering',
    title: 'Why the control plane matters for a terminal product',
    excerpt: 'Device login, billing, release metadata, and token budgets are not side features. They are the infrastructure that makes the CLI feel trustworthy.',
    date: 'March 2026',
    read: '6 min read',
  },
  {
    cat: 'Tutorial',
    title: 'Use Krud to diagnose an nginx 502 without leaving the shell',
    excerpt: 'A walkthrough of prompt, proposal, approval, log inspection, and readable remediation in one operator loop.',
    date: 'February 2026',
    read: '5 min read',
  },
  {
    cat: 'Engineering',
    title: 'Why we kept browser approval but removed fake web login',
    excerpt: 'The sharper UX choice was to make the device-code flow explicit instead of dressing up a surface the product did not need.',
    date: 'February 2026',
    read: '4 min read',
  },
];

export default function Blog() {
  return (
    <>
      <PageIntro
        eyebrow="Journal"
        title="Editorial by default, not a pile of feature cards."
        description="The journal now reads like a place for shipping notes, engineering rationale, and operator walkthroughs. That suits the product better than another marketing grid."
        aside={
          <div className="meta-panel">
            <p>
              Good product writing should help someone understand why the system is built the
              way it is and what changed.
            </p>
          </div>
        }
      />

      <section className="section-block">
        <div className="shell">
          <Reveal className="editorial-feature">
            <p className="story-kicker">{posts[0].cat}</p>
            <h2 style={{ fontSize: 'clamp(2rem, 4vw, 3.4rem)' }}>{posts[0].title}</h2>
            <p style={{ marginTop: '1rem', maxWidth: '42rem' }}>{posts[0].excerpt}</p>
            <ul className="story-meta">
              <li>{posts[0].date}</li>
              <li>{posts[0].read}</li>
            </ul>
          </Reveal>
        </div>
      </section>

      <section className="section-block">
        <div className="shell">
          {posts.slice(1).map((post, index) => (
            <Reveal key={post.title} delay={index * 0.08} className="editorial-post">
              <p className="story-kicker">{post.cat}</p>
              <div>
                <h3>{post.title}</h3>
                <p style={{ marginTop: '0.6rem', maxWidth: '42rem' }}>{post.excerpt}</p>
              </div>
              <div>
                <p className="story-meta">{post.date}</p>
                <p className="story-meta">{post.read}</p>
                <span className="button button-link" style={{ marginTop: '0.8rem' }}>
                  Read note
                  <ArrowRight size={15} />
                </span>
              </div>
            </Reveal>
          ))}
        </div>
      </section>
    </>
  );
}
