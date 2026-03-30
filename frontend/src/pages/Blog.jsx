import React from 'react';
import { ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { BLOG_POSTS } from '../content/site';
import { PageIntro, Reveal } from '../components/ui';

export default function Blog() {
  const [featuredPost, ...supportingPosts] = BLOG_POSTS;

  return (
    <>
      <PageIntro
        eyebrow="Journal"
        title="Notes from the command line, not filler around it."
        description="The journal is where releases, engineering decisions, and operator walkthroughs get enough space to breathe. Every article now has a real route behind it."
        aside={
          <div className="meta-panel">
            <p>
              Good product writing should help someone understand what shipped, why it
              matters, and what kind of work the product is really built for.
            </p>
          </div>
        }
      />

      <section className="section-block">
        <div className="shell">
          <Reveal className="editorial-feature">
            <p className="story-kicker">{featuredPost.category}</p>
            <h2 style={{ fontSize: 'clamp(2rem, 4vw, 3.4rem)' }}>{featuredPost.title}</h2>
            <p style={{ marginTop: '1rem', maxWidth: '42rem' }}>{featuredPost.excerpt}</p>
            <ul className="story-meta">
              <li>{featuredPost.date}</li>
              <li>{featuredPost.readTime}</li>
            </ul>
            <div className="button-row">
              <Link to={`/blog/${featuredPost.slug}`} className="button button-primary">
                Read the full note
                <ArrowRight size={15} />
              </Link>
            </div>
          </Reveal>
        </div>
      </section>

      <section className="section-block">
        <div className="shell">
          {supportingPosts.map((post, index) => (
            <Reveal key={post.title} delay={index * 0.08} className="editorial-post">
              <p className="story-kicker">{post.category}</p>
              <div>
                <h3>{post.title}</h3>
                <p style={{ marginTop: '0.6rem', maxWidth: '42rem' }}>{post.excerpt}</p>
              </div>
              <div>
                <p className="story-meta">{post.date}</p>
                <p className="story-meta">{post.readTime}</p>
                <Link
                  to={`/blog/${post.slug}`}
                  className="button button-link editorial-link"
                  style={{ marginTop: '0.8rem' }}
                >
                  Read note
                  <ArrowRight size={15} />
                </Link>
              </div>
            </Reveal>
          ))}
        </div>
      </section>
    </>
  );
}
