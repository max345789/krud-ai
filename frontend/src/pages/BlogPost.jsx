import React from 'react';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { Link, Navigate, useParams } from 'react-router-dom';
import { BLOG_POSTS } from '../content/site';
import { PageIntro, Reveal } from '../components/ui';

export default function BlogPost() {
  const { slug } = useParams();
  const postIndex = BLOG_POSTS.findIndex((post) => post.slug === slug);

  if (postIndex === -1) {
    return <Navigate to="/blog" replace />;
  }

  const post = BLOG_POSTS[postIndex];
  const previousPost = BLOG_POSTS[postIndex - 1] ?? null;
  const nextPost = BLOG_POSTS[postIndex + 1] ?? null;

  return (
    <>
      <PageIntro
        eyebrow={post.category}
        title={post.title}
        description={post.summary}
        aside={
          <div className="meta-panel">
            <p>{post.date}</p>
            <p>{post.readTime}</p>
            <p>
              This note is part of the same product story as the CLI, daemon, and
              control plane.
            </p>
          </div>
        }
      />

      <section className="section-block">
        <div className="shell reading-layout">
          <Reveal className="reading-body">
            <p className="reading-lead">{post.excerpt}</p>

            {post.sections.map((section) => (
              <section key={section.heading} className="reading-section">
                <h2>{section.heading}</h2>
                {section.paragraphs.map((paragraph) => (
                  <p key={paragraph}>{paragraph}</p>
                ))}
              </section>
            ))}
          </Reveal>

          <Reveal delay={0.08} className="reading-side">
            <div className="story-panel">
              <p className="story-kicker">Key notes</p>
              <ul className="plan-list">
                {post.notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            </div>

            <div className="story-panel">
              <p className="story-kicker">Next move</p>
              <p>
                The fastest way to validate the story is still to use the product and
                read the surfaces yourself.
              </p>
              <div className="button-row">
                <Link to={post.cta.to} className="button button-primary">
                  {post.cta.label}
                  <ArrowRight size={15} />
                </Link>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      <section className="section-block">
        <div className="shell reading-nav">
          {previousPost ? (
            <Link to={`/blog/${previousPost.slug}`} className="reading-nav__item">
              <ArrowLeft size={15} />
              <div>
                <span>Previous note</span>
                <strong>{previousPost.title}</strong>
              </div>
            </Link>
          ) : (
            <span className="reading-nav__item is-empty" aria-hidden="true" />
          )}

          {nextPost ? (
            <Link to={`/blog/${nextPost.slug}`} className="reading-nav__item reading-nav__item-end">
              <div>
                <span>Next note</span>
                <strong>{nextPost.title}</strong>
              </div>
              <ArrowRight size={15} />
            </Link>
          ) : (
            <Link to="/blog" className="reading-nav__item reading-nav__item-end">
              <div>
                <span>Back to the journal</span>
                <strong>See all notes</strong>
              </div>
              <ArrowRight size={15} />
            </Link>
          )}
        </div>
      </section>
    </>
  );
}
