from __future__ import annotations


def render_billing_checkout_page(email: str, plan: str) -> str:
    return f"""
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Krud AI Mock Checkout</title>
        <style>
          body {{
            margin: 0;
            min-height: 100vh;
            display: grid;
            place-items: center;
            background: linear-gradient(135deg, #f4efe6, #f7f4ec);
            font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            color: #1d1c1a;
          }}
          main {{
            width: min(560px, calc(100vw - 32px));
            background: white;
            border: 1px solid #e4d8c7;
            border-radius: 20px;
            padding: 28px;
            box-shadow: 0 18px 60px rgba(29, 28, 26, 0.08);
          }}
          h1 {{ margin-top: 0; }}
          p {{ line-height: 1.6; color: #655f58; }}
          form {{ margin-top: 20px; display: grid; gap: 12px; }}
          input {{
            padding: 12px 14px;
            border: 1px solid #d9c8b2;
            border-radius: 12px;
            font: inherit;
          }}
          button {{
            border: 0;
            border-radius: 999px;
            padding: 12px 18px;
            background: #b6512f;
            color: white;
            font: inherit;
            font-weight: 700;
            cursor: pointer;
          }}
          .muted {{ font-size: 0.95rem; }}
        </style>
      </head>
      <body>
        <main>
          <h1>Mock Checkout</h1>
          <p>This local MVP page simulates a successful Krud AI subscription checkout.</p>
          <p class="muted">Email: <strong>{email}</strong><br />Plan: <strong>{plan}</strong></p>
          <form method="post" action="/billing/mock-checkout">
            <input type="hidden" name="email" value="{email}" />
            <input type="hidden" name="status" value="active" />
            <button type="submit">Activate Subscription</button>
          </form>
        </main>
      </body>
    </html>
    """


def render_billing_portal_page(email: str, status: str) -> str:
    return f"""
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Krud AI Mock Portal</title>
        <style>
          body {{
            margin: 0;
            min-height: 100vh;
            display: grid;
            place-items: center;
            background: #f6f2ea;
            font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            color: #1d1c1a;
          }}
          main {{
            width: min(560px, calc(100vw - 32px));
            background: white;
            border: 1px solid #e4d8c7;
            border-radius: 20px;
            padding: 28px;
            box-shadow: 0 18px 60px rgba(29, 28, 26, 0.08);
          }}
          form {{ display: inline-block; margin-right: 12px; margin-top: 16px; }}
          button {{
            border: 0;
            border-radius: 999px;
            padding: 12px 18px;
            background: #1d1c1a;
            color: white;
            font: inherit;
            cursor: pointer;
          }}
          .secondary {{ background: #8a857e; }}
        </style>
      </head>
      <body>
        <main>
          <h1>Mock Billing Portal</h1>
          <p>Email: <strong>{email}</strong></p>
          <p>Subscription status: <strong>{status}</strong></p>
          <form method="post" action="/billing/mock-portal">
            <input type="hidden" name="email" value="{email}" />
            <input type="hidden" name="status" value="active" />
            <button type="submit">Set Active</button>
          </form>
          <form method="post" action="/billing/mock-portal">
            <input type="hidden" name="email" value="{email}" />
            <input type="hidden" name="status" value="canceled" />
            <button class="secondary" type="submit">Set Canceled</button>
          </form>
        </main>
      </body>
    </html>
    """


def render_simple_notice(title: str, body: str) -> str:
    return f"""
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>{title}</title>
        <style>
          body {{
            margin: 0;
            min-height: 100vh;
            display: grid;
            place-items: center;
            background: #f5f0e6;
            font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            color: #1d1c1a;
          }}
          main {{
            width: min(560px, calc(100vw - 32px));
            background: white;
            border: 1px solid #e4d8c7;
            border-radius: 20px;
            padding: 28px;
          }}
        </style>
      </head>
      <body>
        <main>
          <h1>{title}</h1>
          <p>{body}</p>
        </main>
      </body>
    </html>
    """
