from __future__ import annotations

import html
import os

MARKETING_URL = os.getenv("KRUD_MARKETING_URL", "https://dabcloud.in").rstrip("/")
GITHUB_URL = os.getenv("KRUD_GITHUB_URL", "https://github.com/max345789/krud-ai").rstrip("/")
DOCS_URL = os.getenv("KRUD_DOCS_URL", GITHUB_URL)


def safe_text(value: str | None) -> str:
    return html.escape(value or "", quote=True)


def brand_mark_html() -> str:
    return """
    <span class="brand-mark" aria-hidden="true">
      <span></span>
      <span></span>
      <span></span>
      <span></span>
    </span>
    """


def detail_item_html(title: str, body: str) -> str:
    return f"""
    <div class="detail-item">
      <span class="detail-dot" aria-hidden="true"></span>
      <div>
        <strong>{safe_text(title)}</strong>
        <span>{safe_text(body)}</span>
      </div>
    </div>
    """


def terminal_preview_html(lines: list[str]) -> str:
    rendered = "\n".join(
        f'<div class="terminal-line">{safe_text(line)}</div>' for line in lines
    )
    return f"""
    <div class="terminal-preview" aria-hidden="true">
      <div class="terminal-bar">
        <span></span><span></span><span></span>
      </div>
      <div class="terminal-body">{rendered}</div>
    </div>
    """


def status_pill_html(text: str, tone: str = "default") -> str:
    return f'<span class="status-pill status-pill--{safe_text(tone)}">{safe_text(text)}</span>'


def action_link_html(label: str, href: str, variant: str = "secondary") -> str:
    return (
        f'<a class="btn btn-{safe_text(variant)}" href="{safe_text(href)}">'
        f"{safe_text(label)}</a>"
    )


def render_browser_document(title: str, body_html: str, footer_copy: str | None = None) -> str:
    footer_text = safe_text(
        footer_copy
        or "Krud keeps terminal actions explicit. Approve first, then run."
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{safe_text(title)}</title>
  <style>
    :root {{
      --bg: #f4efe8;
      --bg-deep: #efe8de;
      --panel: rgba(255, 255, 255, 0.72);
      --panel-strong: rgba(255, 255, 255, 0.84);
      --line: rgba(37, 22, 57, 0.1);
      --line-soft: rgba(37, 22, 57, 0.06);
      --text: #241535;
      --muted: #665a75;
      --soft: #8d819c;
      --accent: #5b33f2;
      --accent-strong: #4f29df;
      --violet: #8f72ff;
      --success: #5b33f2;
      --danger: #c83e49;
      --shadow: 0 30px 90px rgba(36, 21, 53, 0.08);
    }}

    * {{ box-sizing: border-box; }}

    html, body {{ margin: 0; min-height: 100%; }}

    body {{
      min-height: 100vh;
      color: var(--text);
      font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at 15% 18%, rgba(91, 51, 242, 0.08), transparent 28%),
        radial-gradient(circle at 82% 10%, rgba(255, 255, 255, 0.82), transparent 28%),
        linear-gradient(180deg, #fcfbf8 0%, var(--bg) 55%, var(--bg-deep) 100%);
      overflow-x: hidden;
    }}

    body::before {{
      content: "";
      position: fixed;
      inset: 0;
      background:
        linear-gradient(rgba(36,21,53,0.03), rgba(36,21,53,0.03)) 0 0 / 100% 1px no-repeat,
        linear-gradient(90deg, rgba(36,21,53,0.03), rgba(36,21,53,0.03)) 0 0 / 1px 100% no-repeat;
      opacity: 0.18;
      pointer-events: none;
    }}

    a {{ color: inherit; text-decoration: none; }}

    .frame {{
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}

    .site-header,
    .site-footer,
    .shell {{
      width: min(1180px, calc(100vw - 48px));
      margin: 0 auto;
    }}

    .site-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 24px;
      padding: 24px 0 0;
    }}

    .brand {{
      display: inline-flex;
      align-items: center;
      gap: 14px;
    }}

    .brand-copy {{
      display: flex;
      flex-direction: column;
      gap: 2px;
    }}

    .brand-copy strong {{
      font-size: 0.92rem;
      letter-spacing: 0.14em;
      text-transform: uppercase;
    }}

    .brand-copy span {{
      font-size: 0.74rem;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      color: var(--soft);
    }}

    .brand-mark {{
      width: 42px;
      height: 42px;
      padding: 7px;
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 5px;
      border-radius: 14px;
      border: 1px solid var(--line);
      background:
        radial-gradient(circle at 35% 35%, rgba(255,255,255,0.8), transparent 55%),
        linear-gradient(145deg, rgba(91,51,242,0.16), rgba(37,22,57,0.04));
      box-shadow: 0 8px 24px rgba(37, 22, 57, 0.08);
    }}

    .brand-mark span {{
      border-radius: 6px;
      background: rgba(255,255,255,0.18);
    }}

    .brand-mark span:nth-child(1) {{ background: linear-gradient(180deg, #f2e7ff, #9c7bff); }}
    .brand-mark span:nth-child(2) {{ background: linear-gradient(180deg, #6a44f5, #3c1fd2); }}
    .brand-mark span:nth-child(3) {{ background: linear-gradient(180deg, #ffffff, #d8cfe9); }}
    .brand-mark span:nth-child(4) {{ background: linear-gradient(180deg, #d9ceff, #8f72ff); }}

    .nav-links {{
      display: inline-flex;
      align-items: center;
      gap: 18px;
      color: var(--muted);
      font-size: 0.88rem;
    }}

    .nav-links a {{
      transition: color 160ms ease, transform 160ms ease;
    }}

    .nav-links a:hover {{
      color: var(--text);
      transform: translateY(-1px);
    }}

    .shell {{
      flex: 1;
      display: grid;
      gap: clamp(28px, 4vw, 64px);
      align-items: center;
      padding: 44px 0 56px;
    }}

    .shell--split {{
      grid-template-columns: minmax(0, 1.06fr) minmax(360px, 0.94fr);
    }}

    .shell--notice {{
      grid-template-columns: minmax(0, 760px);
      justify-content: center;
      padding-top: min(16vh, 120px);
    }}

    .intro {{
      padding-top: clamp(12px, 4vh, 54px);
    }}

    .eyebrow {{
      margin: 0 0 18px;
      color: var(--accent);
      font-size: 0.74rem;
      font-weight: 700;
      letter-spacing: 0.28em;
      text-transform: uppercase;
    }}

    .hero-title,
    .panel-title {{
      margin: 0;
      letter-spacing: -0.06em;
      line-height: 0.92;
    }}

    .hero-title {{
      font-size: clamp(3.2rem, 8vw, 6.6rem);
      max-width: 8.5ch;
    }}

    .hero-copy,
    .panel-copy,
    .notice-copy {{
      margin: 18px 0 0;
      max-width: 44ch;
      color: var(--muted);
      font-size: 1.02rem;
      line-height: 1.75;
    }}

    .detail-list {{
      display: grid;
      gap: 14px;
      margin-top: 30px;
      max-width: 36rem;
    }}

    .detail-item {{
      display: grid;
      grid-template-columns: 12px 1fr;
      gap: 14px;
      align-items: start;
    }}

    .detail-dot {{
      width: 10px;
      height: 10px;
      margin-top: 8px;
      border-radius: 999px;
      background: linear-gradient(180deg, var(--accent-strong), var(--violet));
      box-shadow: 0 0 18px rgba(212, 170, 108, 0.35);
    }}

    .detail-item strong {{
      display: block;
      margin-bottom: 4px;
      font-size: 0.96rem;
      color: var(--text);
    }}

    .detail-item span {{
      display: block;
      color: var(--muted);
      line-height: 1.65;
    }}

    .terminal-preview {{
      width: min(100%, 540px);
      margin-top: 34px;
      border: 1px solid rgba(37, 22, 57, 0.08);
      border-radius: 24px;
      overflow: hidden;
      background: rgba(21, 16, 35, 0.96);
      box-shadow: var(--shadow);
    }}

    .terminal-bar {{
      display: flex;
      gap: 8px;
      padding: 14px 16px;
      border-bottom: 1px solid rgba(255,255,255,0.08);
      background: rgba(255,255,255,0.04);
    }}

    .terminal-bar span {{
      width: 10px;
      height: 10px;
      border-radius: 999px;
      background: rgba(255,255,255,0.18);
    }}

    .terminal-bar span:nth-child(1) {{ background: rgba(255, 123, 114, 0.9); }}
    .terminal-bar span:nth-child(2) {{ background: rgba(240, 203, 146, 0.9); }}
    .terminal-bar span:nth-child(3) {{ background: rgba(155, 230, 204, 0.9); }}

    .terminal-body {{
      padding: 18px 18px 20px;
      font-family: "SFMono-Regular", "JetBrains Mono", "Fira Code", monospace;
      font-size: 0.92rem;
      line-height: 1.8;
      color: #f7f3ff;
    }}

    .terminal-line + .terminal-line {{
      margin-top: 3px;
    }}

    .panel {{
      position: relative;
      align-self: center;
      padding: clamp(26px, 3vw, 34px);
      border-radius: 28px;
      border: 1px solid var(--line);
      background:
        linear-gradient(180deg, rgba(255,255,255,0.3), rgba(255,255,255,0.12)),
        var(--panel);
      box-shadow: var(--shadow);
      backdrop-filter: blur(24px);
    }}

    .panel::after {{
      content: "";
      position: absolute;
      inset: 0;
      border-radius: inherit;
      pointer-events: none;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.36);
    }}

    .panel-kicker {{
      margin: 0 0 14px;
      color: var(--accent);
      font-size: 0.74rem;
      font-weight: 700;
      letter-spacing: 0.24em;
      text-transform: uppercase;
    }}

    .panel-kicker--success {{ color: var(--accent); }}
    .panel-kicker--danger {{ color: var(--danger); }}

    .panel-title {{
      font-size: clamp(2rem, 4vw, 3rem);
    }}

    .stack {{
      display: grid;
      gap: 16px;
      margin-top: 26px;
    }}

    .field {{
      display: grid;
      gap: 8px;
    }}

    .field-label {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      color: var(--text);
      font-size: 0.92rem;
      font-weight: 600;
    }}

    .field-note {{
      color: var(--soft);
      font-size: 0.78rem;
      font-weight: 500;
    }}

    .input,
    .text-input {{
      width: 100%;
      padding: 15px 16px;
      border-radius: 16px;
      border: 1px solid rgba(37,22,57,0.12);
      background: rgba(255,255,255,0.88);
      color: var(--text);
      font: inherit;
      outline: none;
      transition: border-color 180ms ease, box-shadow 180ms ease, transform 180ms ease;
    }}

    .input:focus,
    .text-input:focus {{
      border-color: rgba(91, 51, 242, 0.38);
      box-shadow: 0 0 0 4px rgba(91, 51, 242, 0.12);
      transform: translateY(-1px);
    }}

    .mono {{
      font-family: "SFMono-Regular", "JetBrains Mono", "Fira Code", monospace;
      letter-spacing: 0.18em;
      text-transform: uppercase;
    }}

    .error-box {{
      display: none;
      padding: 14px 16px;
      border-radius: 16px;
      border: 1px solid rgba(200, 62, 73, 0.18);
      background: rgba(200, 62, 73, 0.08);
      color: var(--danger);
      line-height: 1.65;
    }}

    .button-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 10px;
    }}

    .button-row form {{
      margin: 0;
    }}

    .btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 48px;
      padding: 0 18px;
      border: 1px solid transparent;
      border-radius: 999px;
      font-weight: 700;
      font-size: 0.94rem;
      transition: transform 160ms ease, opacity 160ms ease, border-color 160ms ease,
        background 160ms ease;
      cursor: pointer;
      text-decoration: none;
      font-family: inherit;
    }}

    .btn:hover {{
      transform: translateY(-1px);
    }}

    .btn-primary {{
      background: linear-gradient(135deg, var(--accent), var(--accent-strong));
      color: #ffffff;
      box-shadow: 0 18px 30px rgba(91, 51, 242, 0.18);
    }}

    .btn-secondary {{
      background: rgba(255,255,255,0.56);
      border-color: rgba(37,22,57,0.12);
      color: var(--text);
    }}

    .btn-ghost {{
      background: transparent;
      border-color: rgba(37,22,57,0.1);
      color: var(--muted);
    }}

    .helper {{
      margin-top: 14px;
      color: var(--soft);
      font-size: 0.84rem;
      line-height: 1.7;
    }}

    .status-pill {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      width: fit-content;
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid rgba(37,22,57,0.1);
      background: rgba(255,255,255,0.56);
      font-size: 0.86rem;
      color: var(--text);
    }}

    .status-pill::before {{
      content: "";
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: currentColor;
      opacity: 0.85;
    }}

    .status-pill--success {{ color: var(--accent); }}
    .status-pill--danger {{ color: var(--danger); }}
    .status-pill--default {{ color: var(--accent-strong); }}
    .status-pill--muted {{ color: var(--muted); }}

    .steps {{
      margin: 18px 0 0;
      padding-left: 20px;
      color: var(--muted);
      line-height: 1.8;
    }}

    .steps strong {{
      color: var(--text);
    }}

    .inline-code {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      background: rgba(91, 51, 242, 0.08);
      border: 1px solid rgba(91, 51, 242, 0.14);
      font-family: "SFMono-Regular", "JetBrains Mono", monospace;
      font-size: 0.86rem;
      color: var(--accent);
    }}

    .notice-copy {{
      max-width: 52ch;
    }}

    .notice-panel {{
      padding: clamp(28px, 4vw, 40px);
    }}

    .site-footer {{
      padding: 0 0 28px;
      color: var(--soft);
      font-size: 0.82rem;
    }}

    .site-footer-inner {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
      padding-top: 18px;
      border-top: 1px solid rgba(37,22,57,0.08);
    }}

    .site-footer-links {{
      display: inline-flex;
      gap: 14px;
      flex-wrap: wrap;
    }}

    .site-footer-links a:hover {{
      color: var(--text);
    }}

    @media (max-width: 920px) {{
      .site-header {{
        flex-direction: column;
        align-items: flex-start;
      }}

      .shell--split {{
        grid-template-columns: 1fr;
      }}

      .intro {{
        padding-top: 0;
      }}

      .hero-title {{
        max-width: 10ch;
      }}
    }}

    @media (max-width: 640px) {{
      .site-header,
      .site-footer,
      .shell {{
        width: min(100vw - 28px, 1180px);
      }}

      .hero-title {{
        font-size: clamp(2.6rem, 14vw, 4.6rem);
      }}

      .panel-title {{
        font-size: clamp(1.8rem, 8vw, 2.5rem);
      }}

      .button-row {{
        flex-direction: column;
      }}

      .button-row form {{
        width: 100%;
      }}

      .btn {{
        width: 100%;
      }}

      .site-footer-inner {{
        flex-direction: column;
        align-items: flex-start;
      }}
    }}
  </style>
</head>
<body>
  <div class="frame">
    <header class="site-header">
      <a class="brand" href="{safe_text(MARKETING_URL)}">
        {brand_mark_html()}
        <span class="brand-copy">
          <strong>Krud AI</strong>
          <span>terminal agent</span>
        </span>
      </a>
      <nav class="nav-links" aria-label="Primary">
        <a href="{safe_text(DOCS_URL)}">Docs</a>
        <a href="{safe_text(GITHUB_URL)}">GitHub</a>
      </nav>
    </header>
    {body_html}
    <footer class="site-footer">
      <div class="site-footer-inner">
        <span>{footer_text}</span>
        <div class="site-footer-links">
          <a href="{safe_text(MARKETING_URL)}">Home</a>
          <a href="{safe_text(DOCS_URL)}">Install</a>
          <a href="{safe_text(GITHUB_URL)}">Source</a>
        </div>
      </div>
    </footer>
  </div>
</body>
</html>
"""
