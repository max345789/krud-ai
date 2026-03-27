from __future__ import annotations

# Base64-encoded minimal black-circle-rabbit logo (1x1 transparent fallback)
# The real logo is served from the same domain when deployed.
_LOGO_B64 = (
    "data:image/svg+xml;base64,"
    "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj4"
    "8Y2lyY2xlIGN4PSI1MCIgY3k9IjUwIiByPSI1MCIgZmlsbD0iIzExMTExMSIvPjxwYXRoIGQ9Ik0zNSAy"
    "NUMzNSAxNyA0MiAxMiA1MCAxMkM1OCAxMiA2NSAxNyA2NSAyNUM2NSAzMiA2MCA0MCA1NSA0Mkw1NSA2NUw"
    "0NSA2NUw0NSA0MkM0MCA0MCAzNSAzMiAzNSAyNVoiIGZpbGw9IndoaXRlIi8+PC9zdmc+"
)


def build_device_page(
    user_code: str | None = None,
    approved: bool = False,
    email: str | None = None,
) -> str:
    user_code_value = user_code or ""

    success_block = ""
    if approved and email:
        success_block = f"""
        <div class="success-box">
          <div class="success-icon">&#10003;</div>
          <h2>Terminal connected!</h2>
          <p>Logged in as <strong>{email}</strong>.<br>
          Switch back to your terminal — Krud AI is ready.</p>
        </div>
        """

    form_style = "display:none;" if approved else ""
    success_style = "" if approved else "display:none;"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Krud AI — Connect Terminal</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, sans-serif;
    background: #0a0a0a;
    color: #e6edf3;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 1rem;
  }}

  nav {{
    position: fixed;
    top: 0; left: 0; right: 0;
    display: flex;
    align-items: center;
    padding: 0.9rem 1.75rem;
    border-bottom: 1px solid #1e1e1e;
    background: rgba(10,10,10,0.92);
    backdrop-filter: blur(8px);
    z-index: 10;
  }}
  .brand {{
    display: flex;
    align-items: center;
    gap: 9px;
    font-weight: 650;
    font-size: 0.95rem;
    color: #e6edf3;
    text-decoration: none;
  }}
  .brand img {{
    width: 30px; height: 30px;
    border-radius: 50%;
  }}

  .card {{
    background: #111;
    border: 1px solid #222;
    border-radius: 18px;
    padding: 2.25rem;
    width: 100%;
    max-width: 400px;
    margin-top: 4rem;
  }}

  .logo {{
    width: 52px; height: 52px;
    border-radius: 50%;
    margin-bottom: 1.25rem;
    display: block;
  }}

  h1 {{
    font-size: 1.45rem;
    font-weight: 700;
    color: #fff;
    margin-bottom: 0.35rem;
  }}

  .sub {{
    font-size: 0.85rem;
    color: #666;
    line-height: 1.55;
    margin-bottom: 1.6rem;
  }}

  .field {{ margin-bottom: 0.9rem; }}

  label {{
    display: block;
    font-size: 0.78rem;
    font-weight: 600;
    color: #888;
    margin-bottom: 0.3rem;
    letter-spacing: 0.03em;
    text-transform: uppercase;
  }}

  input {{
    width: 100%;
    padding: 0.65rem 0.85rem;
    background: #0d0d0d;
    border: 1px solid #2a2a2a;
    border-radius: 9px;
    color: #e6edf3;
    font-size: 0.9rem;
    font-family: inherit;
    outline: none;
    transition: border-color 0.18s;
  }}
  input:focus {{ border-color: #444; }}
  input#user_code {{
    font-family: 'SF Mono', 'Fira Code', ui-monospace, monospace;
    font-size: 1rem;
    letter-spacing: 0.1em;
    color: #fff;
  }}

  .err {{
    display: none;
    background: #1a0808;
    border: 1px solid #5a1a1a;
    border-radius: 8px;
    padding: 0.6rem 0.85rem;
    font-size: 0.8rem;
    color: #f87171;
    margin-bottom: 0.9rem;
  }}

  .btn {{
    width: 100%;
    padding: 0.72rem;
    margin-top: 0.25rem;
    background: #fff;
    color: #0a0a0a;
    border: none;
    border-radius: 9px;
    font-size: 0.92rem;
    font-weight: 700;
    cursor: pointer;
    transition: background 0.15s, transform 0.1s;
    font-family: inherit;
    letter-spacing: 0.01em;
  }}
  .btn:hover {{ background: #d4d4d4; transform: translateY(-1px); }}
  .btn:active {{ transform: translateY(0); }}
  .btn:disabled {{ opacity: 0.5; cursor: not-allowed; transform: none; }}

  .note {{
    font-size: 0.75rem;
    color: #444;
    text-align: center;
    margin-top: 0.9rem;
  }}

  /* success */
  .success-box {{
    text-align: center;
    padding: 0.5rem 0;
  }}
  .success-icon {{
    width: 52px; height: 52px;
    background: #0d2d0d;
    border: 1px solid #1f4d1f;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.4rem;
    color: #4ade80;
    margin: 0 auto 1rem;
  }}
  .success-box h2 {{
    font-size: 1.2rem;
    color: #4ade80;
    margin-bottom: 0.5rem;
  }}
  .success-box p {{
    font-size: 0.85rem;
    color: #666;
    line-height: 1.55;
  }}
  .success-box strong {{ color: #aaa; }}
</style>
</head>
<body>

<nav>
  <a class="brand" href="https://install.krud.ai">
    <img src="{_LOGO_B64}" alt="Krud AI">
    Krud AI
  </a>
</nav>

<div class="card">
  <img class="logo" src="{_LOGO_B64}" alt="Krud AI logo">
  <h1>Connect your terminal</h1>
  <p class="sub">Approve this session to start your 14-day free trial. No credit card required.</p>

  <div class="err" id="err"></div>

  <form id="frm" action="/cli-auth" method="post" style="{form_style}">
    <div class="field">
      <label>User code</label>
      <input id="user_code" name="user_code" type="text"
             value="{user_code_value}" placeholder="XXXX-XXXX"
             maxlength="9" autocomplete="off" required>
    </div>
    <div class="field">
      <label>Email</label>
      <input name="email" type="email" placeholder="you@company.com" required>
    </div>
    <div class="field">
      <label>Name <span style="font-weight:400;text-transform:none;color:#555">(optional)</span></label>
      <input name="name" type="text" placeholder="Your name">
    </div>
    <button class="btn" id="btn" type="submit">Approve device &rarr;</button>
    <p class="note">&#10003;&nbsp; 14-day free trial &nbsp;&middot;&nbsp; No credit card needed</p>
  </form>

  <div class="success-box" id="ok" style="{success_style}">
    {success_block}
  </div>
</div>

<script>
  /* Pre-fill user_code from ?user_code= URL param */
  (function() {{
    var p = new URLSearchParams(location.search).get('user_code');
    if (p) {{ var el = document.getElementById('user_code'); if (el) el.value = p; }}
  }})();
</script>
</body>
</html>"""
