import React, { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { ArrowUpRight, GitBranch, Menu, X } from 'lucide-react';
import { NavLink, Outlet } from 'react-router-dom';
import BrandMark from './BrandMark';

const navItems = [
  { to: '/', label: 'Home' },
  { to: '/features', label: 'Features' },
  { to: '/pricing', label: 'Pricing' },
  { to: '/docs', label: 'Docs' },
  { to: '/blog', label: 'Journal' },
];

const footerGroups = [
  {
    title: 'Product',
    links: [
      { to: '/', label: 'Overview' },
      { to: '/features', label: 'Capabilities' },
      { to: '/pricing', label: 'Pricing' },
      { to: '/login', label: 'Access' },
    ],
  },
  {
    title: 'Build',
    links: [
      { to: '/docs', label: 'Documentation' },
      { to: '/blog', label: 'Release journal' },
      { href: 'https://github.com/max345789/krud-ai', label: 'GitHub', external: true },
    ],
  },
  {
    title: 'Company',
    links: [
      { to: '/contact', label: 'Contact' },
      { to: '/terms', label: 'Terms' },
      { to: '/privacy', label: 'Privacy' },
    ],
  },
];

function FooterLink({ item }) {
  if (item.external) {
    return (
      <a href={item.href} target="_blank" rel="noreferrer" className="footer-link">
        {item.label}
      </a>
    );
  }

  return (
    <NavLink to={item.to} className="footer-link">
      {item.label}
    </NavLink>
  );
}

export default function Layout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const MotionDiv = motion.div;

  return (
    <div className="site-shell">
      <div className="site-ambient" aria-hidden="true">
        <span className="site-ambient__glow site-ambient__glow-primary" />
        <span className="site-ambient__glow site-ambient__glow-secondary" />
        <span className="site-ambient__grid" />
      </div>

      <header className="site-header">
        <div className="shell site-header__inner">
          <NavLink to="/" className="brand-link" aria-label="Krud AI home">
            <BrandMark />
          </NavLink>

          <nav className="site-nav" aria-label="Primary navigation">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => `site-nav__link ${isActive ? 'is-active' : ''}`}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="site-header__actions">
            <a
              className="button button-secondary header-link-desktop"
              href="https://github.com/max345789/krud-ai"
              target="_blank"
              rel="noreferrer"
            >
              GitHub
              <ArrowUpRight size={14} />
            </a>
            <NavLink to="/docs" className="button button-primary header-primary">
              Get started
            </NavLink>
            <button
              type="button"
              className="menu-toggle"
              onClick={() => setMenuOpen((open) => !open)}
              aria-label={menuOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={menuOpen}
            >
              {menuOpen ? <X size={18} /> : <Menu size={18} />}
            </button>
          </div>
        </div>

        <AnimatePresence>
          {menuOpen ? (
            <MotionDiv
              className="mobile-menu"
              initial={{ opacity: 0, y: -18 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -18 }}
              transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
            >
              <div className="mobile-menu__links">
                {navItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className="mobile-menu__link"
                    onClick={() => setMenuOpen(false)}
                  >
                    {item.label}
                  </NavLink>
                ))}
              </div>
              <div className="mobile-menu__actions">
                <NavLink
                  to="/docs"
                  className="button button-primary"
                  onClick={() => setMenuOpen(false)}
                >
                  Open docs
                </NavLink>
                <a
                  className="button button-secondary"
                  href="https://github.com/max345789/krud-ai"
                  target="_blank"
                  rel="noreferrer"
                >
                  Repository
                </a>
              </div>
            </MotionDiv>
          ) : null}
        </AnimatePresence>
      </header>

      <main className="site-main">
        <Outlet />
      </main>

      <footer className="site-footer">
        <div className="shell site-footer__inner">
          <div className="site-footer__lead">
            <BrandMark />
            <p>
              Terminal-native AI for people who want receipts, approvals, and a command
              trail instead of a glossy demo.
            </p>
            <div className="site-footer__status">
              <span className="status-dot" />
              <span>Mac-first CLI. Device auth. Background daemon.</span>
            </div>
          </div>

          <div className="site-footer__links">
            {footerGroups.map((group) => (
              <div key={group.title}>
                <p className="footer-heading">{group.title}</p>
                {group.links.map((item) => (
                  <FooterLink key={item.label} item={item} />
                ))}
              </div>
            ))}
            <div>
              <p className="footer-heading">Open source</p>
              <a
                href="https://github.com/max345789/krud-ai"
                target="_blank"
                rel="noreferrer"
                className="footer-link footer-link-inline"
              >
                <GitBranch size={14} />
                Explore the repo
              </a>
            </div>
          </div>
        </div>
        <div className="shell site-footer__bottom">
          <p>© {new Date().getFullYear()} Krud AI. MIT licensed.</p>
          <p>Type the outcome. Review the plan. Run with confidence.</p>
        </div>
      </footer>
    </div>
  );
}
