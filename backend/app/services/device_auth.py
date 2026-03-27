from __future__ import annotations

# Inline SVG rabbit logo (black circle + white rabbit silhouette)
# Used as a data-URI so the page has zero external dependencies.
_LOGO = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E"
    "%3Ccircle cx='50' cy='50' r='50' fill='%23111'/%3E"
    "%3Cellipse cx='40' cy='58' rx='18' ry='22' fill='white'/%3E"
    "%3Cellipse cx='62' cy='58' rx='18' ry='22' fill='white'/%3E"
    "%3Cellipse cx='50' cy='62' rx='26' ry='24' fill='white'/%3E"
    "%3Crect x='38' y='22' width='10' height='28' rx='5' fill='white'/%3E"
    "%3Crect x='52' y='26' width='9' height='24' rx='4' fill='white'/%3E"
    "%3C/svg%3E"
)


def build_device_page(
    user_code: str | None = None,
    approved: bool = False,
    email: str | None = None,
) -> str:
    user_code_value = user_code or ""
    form_style   = "display:none;" if approved else ""
    success_style = "" if approved else "display:none;"
    approved_email = f"<strong style='color:#aaa'>{email}</strong>" if email else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Krud AI — Connect Terminal</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #0a0a0a;
    color: #e6edf3;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }}

  /* ── NAV (exact match to landing page) ── */
  nav {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 2rem;
    border-bottom: 1px solid #1e1e1e;
  }}
  .nav-brand {{
    display: flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
  }}
  .nav-brand img {{
    width: 36px;
    height: 36px;
    border-radius: 50%;
  }}
  .nav-brand span {{
    font-size: 1rem;
    font-weight: 600;
    color: #fff;
    letter-spacing: -0.02em;
  }}
  .nav-links {{
    display: flex;
    align-items: center;
    gap: 1.5rem;
  }}
  .nav-links a {{
    color: #8b949e;
    text-decoration: none;
    font-size: 0.875rem;
    transition: color 0.15s;
  }}
  .nav-links a:hover {{ color: #fff; }}

  /* ── MAIN CONTENT ── */
  .page {{
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 3rem 1.5rem;
  }}

  /* ── CARD (same bg/border as install-box on landing) ── */
  .card {{
    background: #111;
    border: 1px solid #222;
    border-radius: 16px;
    padding: 2.5rem;
    width: 100%;
    max-width: 420px;
  }}

  .card-logo {{
    width: 56px;
    height: 56px;
    border-radius: 50%;
    margin-bottom: 1.25rem;
    display: block;
  }}

  h1 {{
    font-size: 1.6rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: #fff;
    margin-bottom: 0.4rem;
    line-height: 1.2;
  }}
  h1 span {{ color: #f78166; }}

  .sub {{
    font-size: 0.9rem;
    color: #8b949e;
    line-height: 1.7;
    margin-bottom: 1.75rem;
  }}

  /* ── FORM ── */
  .field {{ margin-bottom: 0.9rem; }}

  label {{
    display: block;
    font-size: 0.8rem;
    font-weight: 600;
    color: #8b949e;
    margin-bottom: 0.35rem;
    letter-spacing: 0.01em;
  }}

  input {{
    width: 100%;
    padding: 0.7rem 0.9rem;
    background: #0a0a0a;
    border: 1px solid #222;
    border-radius: 10px;
    color: #e6edf3;
    font-size: 0.9rem;
    font-family: inherit;
    outline: none;
    transition: border-color 0.15s;
  }}
  input:focus {{ border-color: #444; }}

  input#user_code {{
    font-family: 'SF Mono', 'Fira Code', monospace;
    font-size: 1rem;
    letter-spacing: 0.1em;
    color: #79c0ff;
  }}

  /* ── ERROR ── */
  .err {{
    display: none;
    background: #160909;
    border: 1px solid #3d1212;
    border-radius: 8px;
    padding: 0.65rem 0.85rem;
    font-size: 0.82rem;
    color: #f87171;
    margin-bottom: 0.9rem;
    line-height: 1.5;
  }}

  /* ── PRIMARY BUTTON (matches landing page .btn-primary) ── */
  .btn-primary {{
    width: 100%;
    padding: 0.7rem 1.5rem;
    margin-top: 0.25rem;
    background: #fff;
    color: #0a0a0a;
    border: none;
    border-radius: 999px;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.15s, transform 0.1s;
    font-family: inherit;
    letter-spacing: -0.01em;
  }}
  .btn-primary:hover {{ opacity: 0.85; transform: translateY(-1px); }}
  .btn-primary:active {{ transform: translateY(0); }}
  .btn-primary:disabled {{ opacity: 0.4; cursor: not-allowed; transform: none; }}

  .trial-note {{
    font-size: 0.78rem;
    color: #484f58;
    text-align: center;
    margin-top: 0.9rem;
  }}

  /* ── SUCCESS ── */
  .success-box {{
    text-align: center;
    padding: 0.5rem 0;
  }}
  .success-icon {{
    font-size: 2.5rem;
    margin-bottom: 0.75rem;
  }}
  .success-box h2 {{
    font-size: 1.3rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #fff;
    margin-bottom: 0.5rem;
  }}
  .success-box h2 span {{ color: #f78166; }}
  .success-box p {{
    font-size: 0.875rem;
    color: #8b949e;
    line-height: 1.7;
  }}

  /* ── FOOTER (exact match) ── */
  footer {{
    text-align: center;
    padding: 1.5rem 2rem;
    color: #484f58;
    font-size: 0.8rem;
    border-top: 1px solid #1a1a1a;
  }}
  footer a {{ color: #484f58; text-decoration: none; }}
  footer a:hover {{ color: #8b949e; }}
</style>
</head>
<body>

<!-- NAV -->
<nav>
  <a class="nav-brand" href="https://install.krud.ai">
    <img src="{_LOGO}" alt="Krud AI logo">
    <span>Krud AI</span>
  </a>
  <div class="nav-links">
    <a href="https://github.com/max345789/krud-ai">GitHub</a>
    <a href="https://github.com/max345789/krud-ai/releases">Releases</a>
  </div>
</nav>

<!-- MAIN -->
<div class="page">
  <div class="card">
    <img class="card-logo" src="{_LOGO}" alt="Krud AI">
    <h1>Connect your<br><span>terminal.</span></h1>
    <p class="sub">Approve this session and start your 14-day free trial. No credit card required.</p>

    <div class="err" id="err"></div>

    <form id="frm" action="/cli-auth" method="post" style="{form_style}">
      <div class="field">
        <label>User code</label>
        <input id="user_code" name="user_code" type="text"
               value="{user_code_value}" placeholder="XXXX-XXXX"
               maxlength="9" autocomplete="off" spellcheck="false" required>
      </div>
      <div class="field">
        <label>Email</label>
        <input name="email" type="email" placeholder="you@company.com" required>
      </div>
      <div class="field">
        <label>Name &nbsp;<span style="font-weight:400;color:#484f58">(optional)</span></label>
        <input name="name" type="text" placeholder="Your name">
      </div>
      <button class="btn-primary" id="btn" type="submit">Approve device &rarr;</button>
      <p class="trial-note">&#10003;&nbsp; 14-day free trial &nbsp;&middot;&nbsp; No credit card needed</p>
    </form>

    <div class="success-box" id="ok" style="{success_style}">
      <div class="success-icon">&#9989;</div>
      <h2>Terminal <span>connected.</span></h2>
      <p>{"Logged in as " + approved_email + ".<br>" if approved_email else ""}
         Switch back to your terminal &mdash;<br>Krud AI is ready to use.</p>
    </div>
  </div>
</div>

<!-- FOOTER -->
<footer>
  &copy; 2025 Krud AI &nbsp;&middot;&nbsp;
  <a href="https://github.com/max345789/krud-ai">Open Source</a> &nbsp;&middot;&nbsp;
  After installing: <code style="color:#555">krud login</code> then <code style="color:#555">krud chat</code>
</footer>

<script>
  /* Pre-fill user_code from ?user_code= URL param */
  (function() {{
    var p = new URLSearchParams(location.search).get('user_code');
    if (p) {{ var el = document.getElementById('user_code'); if (el) el.value = p; }}
  }})();
</script>
</body>
</html>"""
