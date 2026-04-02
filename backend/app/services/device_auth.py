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


def build_device_page(
    user_code: str | None = None,
    approved: bool = False,
    email: str | None = None,
) -> str:
    safe_code = safe_text(user_code or "")
    safe_email = safe_text(email or "")

    intro = f"""
    <section class="intro">
      <p class="eyebrow">Secure device flow</p>
      <h1 class="hero-title">Connect this terminal.</h1>
      <p class="hero-copy">
        Approve the session once in your browser. Krud finishes sign-in back in
        the shell and still requires explicit approval before any command runs.
      </p>
      <div class="detail-list">
        {detail_item_html("14-day trial", "Start without a card and validate the full workflow first.")}
        {detail_item_html("Local control", "The terminal still asks before every shell action.")}
        {detail_item_html("Fast handoff", "Approve here, then return to the CLI and keep working.")}
      </div>
      {terminal_preview_html([
          "$ krud login",
          "Open browser approval",
          "Approve this device",
          "$ krud chat",
      ])}
    </section>
    """

    if approved:
        panel = f"""
        <section class="panel" aria-labelledby="device-title">
          <p class="panel-kicker panel-kicker--success">Session approved</p>
          <h2 class="panel-title" id="device-title">This machine is connected.</h2>
          <p class="panel-copy">
            Return to your terminal. Krud will complete the login automatically
            and you can start working immediately.
          </p>
          <div class="stack">
            {status_pill_html(safe_email or "Device approved", "success")}
          </div>
          <ol class="steps">
            <li><strong>Return to the terminal</strong> where you started the device flow.</li>
            <li><strong>Wait for the CLI</strong> to confirm the session is connected.</li>
            <li><strong>Start chatting</strong> with <span class="inline-code">krud chat</span>.</li>
          </ol>
          <div class="button-row">
            {action_link_html("Open docs", DOCS_URL, "secondary")}
            {action_link_html("Back to Krud AI", MARKETING_URL, "ghost")}
          </div>
        </section>
        """
    else:
        panel = f"""
        <section class="panel" aria-labelledby="device-title">
          <p class="panel-kicker">Device approval</p>
          <h2 class="panel-title" id="device-title">Authorize this session.</h2>
          <p class="panel-copy">
            Use the code from your terminal and the email you want attached to
            this machine.
          </p>
          <div class="error-box" id="err"></div>
          <form id="frm" action="/cli-auth" method="post" class="stack" novalidate>
            <div class="field">
              <label class="field-label" for="user_code">User code</label>
              <input
                class="input mono"
                id="user_code"
                name="user_code"
                type="text"
                value="{safe_code}"
                placeholder="XXXX-XXXX"
                maxlength="9"
                inputmode="text"
                autocomplete="one-time-code"
                spellcheck="false"
                required
              />
            </div>
            <div class="field">
              <label class="field-label" for="email">Email</label>
              <input
                class="input"
                id="email"
                name="email"
                type="email"
                placeholder="you@company.com"
                autocomplete="email"
                required
              />
            </div>
            <div class="field">
              <label class="field-label" for="name">
                Name
                <span class="field-note">Optional</span>
              </label>
              <input
                class="input"
                id="name"
                name="name"
                type="text"
                placeholder="Display name"
                autocomplete="name"
              />
            </div>
            <button class="btn btn-primary" id="btn" type="submit">Approve this device</button>
          </form>
          <p class="helper">
            No credit card required. The trial starts after this approval finishes.
          </p>
        </section>
        """

    body_html = f"""
    <main class="shell shell--split">
      {intro}
      {panel}
    </main>
    <script>
      (function () {{
        var codeInput = document.getElementById("user_code");
        var form = document.getElementById("frm");
        var errorBox = document.getElementById("err");

        function normalize(value) {{
          return value
            .toUpperCase()
            .replace(/[^A-Z0-9]/g, "")
            .slice(0, 8)
            .replace(/(.{{4}})(?=.)/, "$1-");
        }}

        var preset = new URLSearchParams(window.location.search).get("user_code");
        if (codeInput && preset && !codeInput.value) {{
          codeInput.value = normalize(preset);
        }}

        if (codeInput) {{
          codeInput.addEventListener("input", function () {{
            codeInput.value = normalize(codeInput.value);
          }});
        }}

        if (form) {{
          form.addEventListener("submit", function (event) {{
            if (!codeInput) return;
            codeInput.value = normalize(codeInput.value);
            if (!/^[A-Z0-9]{{4}}-[A-Z0-9]{{4}}$/.test(codeInput.value)) {{
              event.preventDefault();
              if (errorBox) {{
                errorBox.style.display = "block";
                errorBox.textContent = "Enter the 8-character code shown in your terminal.";
              }}
              codeInput.focus();
            }}
          }});
        }}
      }})();
    </script>
    """

    return render_browser_document(
        "Krud AI Device Approval",
        body_html,
        footer_copy="Approve once here, then return to the terminal to finish the session.",
    )
