from __future__ import annotations


def build_device_page(user_code: str | None = None, approved: bool = False, email: str | None = None) -> str:
    user_code_value = user_code or ""
    approved_markup = ""
    if approved and email:
        approved_markup = f"""
        <div class="success">
          <h2>Krud AI connected</h2>
          <p>{email} can return to the terminal. The `krud login` command will finish automatically.</p>
        </div>
        """

    return f"""
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Krud AI Device Login</title>
        <style>
          :root {{
            color-scheme: light;
            --bg: #f4efe6;
            --panel: #fffdf8;
            --ink: #1d1c1a;
            --muted: #6e675e;
            --accent: #b6512f;
            --accent-dark: #8e3d22;
            --border: #dccfbe;
          }}
          * {{ box-sizing: border-box; }}
          body {{
            margin: 0;
            min-height: 100vh;
            display: grid;
            place-items: center;
            background:
              radial-gradient(circle at top left, rgba(182, 81, 47, 0.18), transparent 40%),
              linear-gradient(160deg, var(--bg), #ede4d8 60%, #f9f5ee);
            font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            color: var(--ink);
          }}
          .panel {{
            width: min(560px, calc(100vw - 32px));
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 28px;
            box-shadow: 0 20px 70px rgba(29, 28, 26, 0.08);
          }}
          h1 {{ margin: 0 0 8px; font-size: 2rem; }}
          p {{ color: var(--muted); line-height: 1.5; }}
          form {{ display: grid; gap: 14px; margin-top: 20px; }}
          label {{ display: grid; gap: 6px; font-weight: 600; }}
          input {{
            padding: 12px 14px;
            border: 1px solid var(--border);
            border-radius: 12px;
            font: inherit;
          }}
          button {{
            border: 0;
            border-radius: 999px;
            padding: 12px 18px;
            background: var(--accent);
            color: white;
            font: inherit;
            font-weight: 700;
            cursor: pointer;
          }}
          button:hover {{ background: var(--accent-dark); }}
          .success {{
            margin-top: 18px;
            border: 1px solid rgba(31, 119, 78, 0.25);
            background: rgba(31, 119, 78, 0.08);
            border-radius: 14px;
            padding: 16px;
          }}
        </style>
      </head>
      <body>
        <main class="panel">
          <h1>Connect Krud AI</h1>
          <p>Approve this terminal session and start your 14-day trial.</p>
          <form method="post" action="/device">
            <label>
              User code
              <input type="text" name="user_code" value="{user_code_value}" placeholder="ABCD-1234" required />
            </label>
            <label>
              Email
              <input type="email" name="email" placeholder="you@company.com" required />
            </label>
            <label>
              Name
              <input type="text" name="name" placeholder="Optional" />
            </label>
            <button type="submit">Approve device</button>
          </form>
          {approved_markup}
        </main>
      </body>
    </html>
    """

