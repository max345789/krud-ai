from __future__ import annotations

from app.services.browser_ui import (
    DOCS_URL,
    MARKETING_URL,
    action_link_html,
    detail_item_html,
    render_browser_document,
    safe_text,
    status_pill_html,
    terminal_preview_html,
)


def render_billing_checkout_page(email: str, plan: str) -> str:
    intro = f"""
    <section class="intro">
      <p class="eyebrow">Billing preview</p>
      <h1 class="hero-title">Activate this Krud plan.</h1>
      <p class="hero-copy">
        This local checkout screen simulates a successful subscription so you can
        verify the billing flow end to end before connecting live payments.
      </p>
      <div class="detail-list">
        {detail_item_html("Account", email)}
        {detail_item_html("Plan", plan)}
        {detail_item_html("Mode", "Mock billing only. No real charge is created.")}
      </div>
      {terminal_preview_html([
          "$ krud login",
          "Open browser checkout",
          "Activate subscription",
          "Return to terminal and continue",
      ])}
    </section>
    """

    panel = f"""
    <section class="panel" aria-labelledby="checkout-title">
      <p class="panel-kicker">Mock checkout</p>
      <h2 class="panel-title" id="checkout-title">Confirm activation.</h2>
      <p class="panel-copy">
        When you submit this form, the local account is marked active and the
        CLI billing gate will treat the subscription as paid.
      </p>
      <div class="stack">
        {status_pill_html(plan or "builder", "default")}
        <div class="field">
          <span class="field-label">Email</span>
          <input class="input" value="{safe_text(email)}" readonly />
        </div>
      </div>
      <form method="post" action="/billing/mock-checkout" class="stack">
        <input type="hidden" name="email" value="{safe_text(email)}" />
        <input type="hidden" name="status" value="active" />
        <button class="btn btn-primary" type="submit">Activate subscription</button>
      </form>
      <p class="helper">
        This is only for local MVP validation. In production, checkout should
        be initiated from the real billing API.
      </p>
    </section>
    """

    body_html = f'<main class="shell shell--split">{intro}{panel}</main>'
    return render_browser_document(
        "Krud AI Billing Checkout",
        body_html,
        footer_copy="Mock billing mirrors the production path without creating a real charge.",
    )


def render_billing_portal_page(email: str, status: str) -> str:
    intro = f"""
    <section class="intro">
      <p class="eyebrow">Billing control</p>
      <h1 class="hero-title">Manage subscription state.</h1>
      <p class="hero-copy">
        This local control page lets you simulate lifecycle changes so the CLI,
        account API, and gating logic can be tested against real status flips.
      </p>
      <div class="detail-list">
        {detail_item_html("Current account", email)}
        {detail_item_html("Current status", status)}
        {detail_item_html("Purpose", "Test the billing transitions before going live.")}
      </div>
      {terminal_preview_html([
          "Subscription state sync",
          f"status → {status}",
          "CLI checks account access",
          "Billing gates update immediately",
      ])}
    </section>
    """

    actions = []
    for next_status, label, tone in (
        ("active", "Set active", "success"),
        ("past_due", "Set past due", "default"),
        ("canceled", "Set canceled", "danger"),
    ):
        button_class = "btn-primary" if next_status == "active" else "btn-secondary"
        actions.append(
            f"""
            <form method="post" action="/billing/mock-portal">
              <input type="hidden" name="email" value="{safe_text(email)}" />
              <input type="hidden" name="status" value="{safe_text(next_status)}" />
              <button class="btn {button_class}" type="submit">{safe_text(label)}</button>
            </form>
            """
        )

    panel = f"""
    <section class="panel" aria-labelledby="portal-title">
      <p class="panel-kicker">Mock portal</p>
      <h2 class="panel-title" id="portal-title">Billing state for this account.</h2>
      <p class="panel-copy">
        Use one of the actions below to change the stored subscription state and
        immediately verify how Krud responds.
      </p>
      <div class="stack">
        {status_pill_html(status, "success" if status == "active" else "danger" if status == "canceled" else "default")}
        <div class="field">
          <span class="field-label">Account</span>
          <input class="input" value="{safe_text(email)}" readonly />
        </div>
      </div>
      <div class="button-row">
        {''.join(actions)}
      </div>
      <p class="helper">
        These controls only affect the local MVP environment.
      </p>
    </section>
    """

    body_html = f'<main class="shell shell--split">{intro}{panel}</main>'
    return render_browser_document(
        "Krud AI Billing Portal",
        body_html,
        footer_copy="Switch states here to verify billing behavior before going live.",
    )


def render_simple_notice(
    title: str,
    body: str,
    *,
    primary_label: str = "Back to Krud AI",
    primary_href: str = MARKETING_URL,
    secondary_label: str | None = "Read docs",
    secondary_href: str | None = DOCS_URL,
) -> str:
    actions = [action_link_html(primary_label, primary_href, "primary")]
    if secondary_label and secondary_href:
        actions.append(action_link_html(secondary_label, secondary_href, "secondary"))

    body_html = f"""
    <main class="shell shell--notice">
      <section class="panel notice-panel" aria-labelledby="notice-title">
        <p class="panel-kicker">Krud AI</p>
        <h1 class="panel-title" id="notice-title">{safe_text(title)}</h1>
        <p class="notice-copy">{safe_text(body)}</p>
        <div class="button-row">
          {''.join(actions)}
        </div>
      </section>
    </main>
    """
    return render_browser_document(title, body_html)
