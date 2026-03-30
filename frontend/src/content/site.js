export const REPO_URL = 'https://github.com/max345789/krud-ai';
export const INSTALL_COMMAND = 'curl -fsSL https://dabcloud.in/install.sh | sh';
export const SUPPORT_EMAIL = 'support@dabcloud.in';
export const SUPPORT_MAILTO = `mailto:${SUPPORT_EMAIL}`;
export const TEAM_ROLLOUT_MAILTO =
  'mailto:support@dabcloud.in?subject=Krud%20team%20rollout';
export const DEVICE_BASE_URL = 'https://dabcloud.in';
export const API_BASE_URL = 'https://api.dabcloud.in';

export const BLOG_POSTS = [
  {
    slug: 'v2-command-history-device-auth-and-billing-paths',
    category: 'Release',
    title:
      'Krud AI v2.0 brings command history, device auth polish, and clearer billing paths',
    excerpt:
      'The product loop feels calmer when the shell, the browser approval, and the account surface all tell the same story.',
    date: 'March 2026',
    readTime: '4 min read',
    summary:
      'This release was about trust. The command trail is easier to read, the browser approval page is cleaner, and billing now has clearer return paths instead of dead ends.',
    sections: [
      {
        heading: 'The shell needed memory, not more hype',
        paragraphs: [
          'A terminal agent stops feeling real the moment it forgets why you asked for something. That is why command history and receipts matter more than louder demos.',
          'This release tightened the loop around proposals, approvals, and the readable summary that comes back after execution.',
        ],
      },
      {
        heading: 'Device auth got simpler and more honest',
        paragraphs: [
          'The browser step exists for one reason: confirm the session that started in the terminal. We leaned into that instead of pretending there was a full web-login product hiding behind it.',
          'The result is less confusion, fewer wrong clicks, and a clearer handoff back to the shell.',
        ],
      },
      {
        heading: 'Billing returns to a page that can hold the story',
        paragraphs: [
          'Checkout and portal return URLs should not land on nowhere. They now come back to a site that explains what changed and where to go next.',
          'That sounds small, but it is the difference between a product surface and a loose collection of pages.',
        ],
      },
    ],
    notes: [
      'Command history is treated as product context, not debug exhaust.',
      'Device approval stays browser-based but terminal-first.',
      'Billing return URLs now point back into a real public route map.',
    ],
    cta: { label: 'Read the docs', to: '/docs' },
  },
  {
    slug: 'why-the-control-plane-matters-for-a-terminal-product',
    category: 'Engineering',
    title: 'Why the control plane matters for a terminal product',
    excerpt:
      'Terminal products still need somewhere to keep billing, release metadata, auth, and account state coherent. The shell alone is not enough.',
    date: 'March 2026',
    readTime: '6 min read',
    summary:
      'Krud works because the CLI, daemon, and FastAPI control plane each own a clear part of the operator loop. The web surface should reflect that architecture instead of hiding it.',
    sections: [
      {
        heading: 'Trust is infrastructural',
        paragraphs: [
          'People do not trust a terminal agent because it speaks well. They trust it because approvals are explicit, release artifacts are traceable, and account state does not drift.',
          'That is the work the control plane does quietly in the background.',
        ],
      },
      {
        heading: 'The browser is a checkpoint, not the product',
        paragraphs: [
          'The browser should confirm, summarize, and hand the user back to the terminal. It should never become a parallel product that competes with the CLI for attention.',
          'Once you accept that boundary, the site gets cleaner and the routing gets easier to reason about.',
        ],
      },
      {
        heading: 'One story across every surface',
        paragraphs: [
          'Release metadata, billing status, chat sessions, and daemon state are all part of the same operator narrative.',
          'The strongest public site is the one that names those pieces clearly and lets each route do one useful job.',
        ],
      },
    ],
    notes: [
      'The CLI owns the working loop.',
      'The control plane owns identity, releases, and account state.',
      'The site should orient, not impersonate the product.',
    ],
    cta: { label: 'Explore features', to: '/features' },
  },
  {
    slug: 'diagnose-an-nginx-502-without-leaving-the-shell',
    category: 'Tutorial',
    title: 'Use Krud to diagnose an nginx 502 without leaving the shell',
    excerpt:
      'A good shell assistant should help you move from symptom to diagnosis without losing the trail of what was checked and why.',
    date: 'February 2026',
    readTime: '5 min read',
    summary:
      'This walkthrough shows the rhythm that Krud is built for: ask in plain language, inspect safely, read the receipt, and keep the operator in control the whole time.',
    sections: [
      {
        heading: 'Start with the symptom, not the exact command',
        paragraphs: [
          'The first prompt can be plain: explain why nginx is returning 502. Krud should translate that into the likely checks instead of forcing the operator to remember each log path by hand.',
          'That is where the product starts to save real time.',
        ],
      },
      {
        heading: 'Stay reviewable while you narrow the issue',
        paragraphs: [
          'Inspection commands can run immediately. Destructive fixes should wait for approval. That keeps the session fast without giving up control.',
          'When the assistant returns a summary, the next decision is usually obvious.',
        ],
      },
      {
        heading: 'Keep the receipt for later',
        paragraphs: [
          'The answer matters, but so does the trail. When the team looks back later, they should be able to see what was checked, what failed, and what fixed it.',
          'That is why history is a product feature, not an implementation detail.',
        ],
      },
    ],
    notes: [
      'Plain-language prompts are enough to start the investigation.',
      'Inspection and approval can live in the same session.',
      'Readable receipts are what make the answer reusable later.',
    ],
    cta: { label: 'Try the operator loop', to: '/login' },
  },
  {
    slug: 'why-we-kept-browser-approval-and-dropped-fake-web-login',
    category: 'Engineering',
    title: 'Why we kept browser approval but removed fake web login',
    excerpt:
      'The terminal is the front door. The browser is there to confirm the session, not to pretend it is the main interface.',
    date: 'February 2026',
    readTime: '4 min read',
    summary:
      'We cut the parts of the public site that implied a different product than the one in the repo. What stayed is the piece that helps the real workflow: clean device approval.',
    sections: [
      {
        heading: 'The honest path is shorter',
        paragraphs: [
          'A fake web login might look polished, but it trains people into the wrong mental model. The right move was to make the device-code path explicit and remove the dead end.',
          'That made the whole product feel more grounded immediately.',
        ],
      },
      {
        heading: 'Browser approval is still useful',
        paragraphs: [
          'Approving a device in the browser is good UX when it keeps credentials and confirmation out of copied terminal text.',
          'What matters is being clear about its role: confirm, then return to the shell.',
        ],
      },
      {
        heading: 'A quieter interface creates more trust',
        paragraphs: [
          'When every visible action maps to a real capability, the site stops feeling like a pitch deck and starts feeling like a dependable tool.',
          'That is the kind of soul product surfaces earn instead of declaring.',
        ],
      },
    ],
    notes: [
      'The terminal remains primary before and after auth.',
      'Browser approval exists to confirm a device session.',
      'Less pretending produces more trust.',
    ],
    cta: { label: 'See the login guide', to: '/docs#login' },
  },
];
