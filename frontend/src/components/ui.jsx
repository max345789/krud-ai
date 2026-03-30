import { useState } from 'react';
import { Check, Copy } from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';

const REVEAL_EASE = [0.22, 1, 0.36, 1];

export function Reveal({ children, className = '', delay = 0, y = 28, ...props }) {
  const reduceMotion = useReducedMotion();
  const MotionDiv = motion.div;

  if (reduceMotion) {
    return (
      <div className={className} {...props}>
        {children}
      </div>
    );
  }

  return (
    <MotionDiv
      className={className}
      {...props}
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.2 }}
      transition={{ duration: 0.72, delay, ease: REVEAL_EASE }}
    >
      {children}
    </MotionDiv>
  );
}

export function SectionHeading({
  eyebrow,
  title,
  description,
  align = 'left',
  className = '',
}) {
  return (
    <div className={`section-heading ${align === 'center' ? 'section-heading-center' : ''} ${className}`.trim()}>
      {eyebrow ? <p className="section-eyebrow">{eyebrow}</p> : null}
      <h2>{title}</h2>
      {description ? <p className="section-description">{description}</p> : null}
    </div>
  );
}

export function PageIntro({ eyebrow, title, description, aside }) {
  return (
    <section className="page-intro">
      <div className="shell page-intro__grid">
        <Reveal className="page-intro__copy">
          <p className="section-eyebrow">{eyebrow}</p>
          <h1>{title}</h1>
          <p className="page-intro__description">{description}</p>
        </Reveal>
        {aside ? (
        <Reveal className="page-intro__aside" delay={0.08}>
          {aside}
        </Reveal>
        ) : null}
      </div>
    </section>
  );
}

export function CopyCommand({ command, label = 'Install command' }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(command);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  };

  return (
    <div className="copy-command">
      <div>
        <p className="copy-command__label">{label}</p>
        <code>{command}</code>
      </div>
      <button
        type="button"
        className="copy-command__button"
        onClick={handleCopy}
        aria-label={copied ? 'Copied command' : 'Copy command'}
      >
        {copied ? <Check size={16} /> : <Copy size={16} />}
      </button>
    </div>
  );
}

function TerminalLine({ line }) {
  const prefix = line.prefix ?? {
    command: '$',
    prompt: '>',
    agent: '●',
    output: '',
    success: '✓',
    meta: '',
  }[line.kind];

  return (
    <div className={`terminal-line terminal-line-${line.kind}`}>
      {prefix ? <span className="terminal-line__prefix">{prefix}</span> : null}
      <span>{line.text}</span>
    </div>
  );
}

export function CommandWindow({
  title = 'krud control loop',
  label = 'Live session',
  lines = [],
  footer,
}) {
  return (
    <div className="terminal-window">
      <div className="terminal-window__bar">
        <div className="terminal-window__lights" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        <p>{title}</p>
        <span className="terminal-window__label">{label}</span>
      </div>
      <div className="terminal-window__body">
        {lines.map((line) => (
          <TerminalLine key={`${line.kind}-${line.text}`} line={line} />
        ))}
      </div>
      {footer ? <div className="terminal-window__footer">{footer}</div> : null}
    </div>
  );
}
