import React from 'react';
import { ArrowUpRight } from 'lucide-react';
import { API_BASE_URL, DEVICE_BASE_URL, INSTALL_COMMAND, REPO_URL } from '../content/site';
import { CommandWindow, CopyCommand, PageIntro, Reveal } from '../components/ui';

const sections = [
  { id: 'install', label: 'Install' },
  { id: 'login', label: 'Device auth' },
  { id: 'chat', label: 'Chat loop' },
  { id: 'daemon', label: 'Daemon queue' },
  { id: 'config', label: 'Configuration' },
  { id: 'self-host', label: 'Control plane' },
];

export default function Docs() {
  return (
    <>
      <PageIntro
        eyebrow="Documentation"
        title="From first install to the first real save."
        description="These docs are arranged around the operator journey that actually exists today: install, authenticate, work in chat, queue long jobs, then tune the control plane."
        aside={
          <div className="meta-panel">
            <p>
              If somebody skims only the headings and command snippets, they should still
              understand the product immediately.
            </p>
          </div>
        }
      />

      <section className="section-block">
        <div className="shell docs-layout">
          <aside className="docs-nav">
            <p className="docs-nav__title">Guide</p>
            {sections.map((section) => (
              <a key={section.id} href={`#${section.id}`} className="docs-nav__link">
                {section.label}
              </a>
            ))}
            <div className="docs-note docs-note--offset">
              <p>
                Need the backend shape too? The control plane lives in the same product story.
              </p>
              <a
                href={REPO_URL}
                target="_blank"
                rel="noreferrer"
                className="button button-link"
              >
                Open repository
                <ArrowUpRight size={15} />
              </a>
            </div>
          </aside>

          <div className="docs-main">
            <Reveal className="docs-section" id="install">
              <p className="section-eyebrow">Install</p>
              <h2>Start with one command.</h2>
              <p>
                The first step should take seconds. Install the CLI, confirm the binary, and
                move directly into authentication.
              </p>
              <CopyCommand command={INSTALL_COMMAND} label="Installer" />
              <ul className="docs-steps">
                <li>Installs the <span className="inline-code">krud</span> binary locally.</li>
                <li>Works for the primary macOS and Linux paths used by the product.</li>
                <li>Pairs naturally with the release manifest endpoint in the backend.</li>
              </ul>
            </Reveal>

            <Reveal className="docs-section" id="login">
              <p className="section-eyebrow">Device auth</p>
              <h2>Approve access from the browser without leaving the terminal workflow.</h2>
              <p>
                <span className="inline-code">krud login</span> starts the device-code flow.
                The browser page now asks the user to create an account or sign in first,
                then approve the device in the same flow.
              </p>
              <CopyCommand command="krud login" label="Authentication" />
              <ul className="docs-steps">
                <li>The browser lands on <span className="inline-code">/login</span> with the device code pre-filled.</li>
                <li>New users create an account there; returning users sign in.</li>
                <li>The CLI session token is stored locally only after authenticated approval finishes.</li>
              </ul>
            </Reveal>

            <Reveal className="docs-section" id="chat">
              <p className="section-eyebrow">Chat loop</p>
              <h2>Ask for the outcome, not the syntax.</h2>
              <p>
                The assistant plans the shell work, proposes commands, and returns a readable
                explanation of what happened after execution.
              </p>
              <CopyCommand command="krud chat" label="Interactive mode" />
              <CommandWindow
                title="krud chat"
                label="interactive"
                lines={[
                  { kind: 'prompt', text: 'find all files larger than 100MB in my home directory' },
                  { kind: 'agent', text: 'Planning a safe file search with depth limits...' },
                  { kind: 'output', text: 'find ~ -maxdepth 3 -size +100M -type f' },
                  { kind: 'success', text: 'Ready to run and summarize the result.' },
                ]}
              />
            </Reveal>

            <Reveal className="docs-section" id="daemon">
              <p className="section-eyebrow">Daemon queue</p>
              <h2>Move long-running work into the background.</h2>
              <p>
                The daemon path matters because good terminal UX is not only about command
                generation. It is also about staying responsive while the work continues.
              </p>
              <CopyCommand command="krud daemon install && krud daemon start" label="Background worker" />
              <CommandWindow
                title="krudd"
                label="queue"
                lines={[
                  { kind: 'command', text: 'krud run "nightly deploy sanity checks"' },
                  { kind: 'agent', text: 'Queued. Continue in the terminal while the daemon processes the task.' },
                  { kind: 'output', text: 'sqlite3 ~/.krud/local.db "select id,status from local_tasks;"' },
                  { kind: 'success', text: 'Task accepted and visible in local history.' },
                ]}
              />
            </Reveal>

            <Reveal className="docs-section" id="config">
              <p className="section-eyebrow">Configuration</p>
              <h2>Tune the product around your environment.</h2>
              <p>
                Configuration lives locally and lines up with the control plane settings used by
                the backend.
              </p>
              <div className="config-block">
                <div># ~/.krud/config.toml</div>
                <div>model = <strong>"gpt-4o"</strong></div>
                <div>safe_mode = <strong>true</strong></div>
                <div>api_key = <strong>"sk-..."</strong></div>
              </div>
              <ul className="docs-steps">
                <li>Safe mode is the right default for product trust.</li>
                <li>Local config complements server-side limits and billing state.</li>
                <li>You can keep model choice explicit without cluttering the core loop.</li>
              </ul>
            </Reveal>

            <Reveal className="docs-section" id="self-host">
              <p className="section-eyebrow">Control plane</p>
              <h2>The backend owns auth, billing, history, and releases.</h2>
              <p>
                The FastAPI app already exposes the routes that make the product coherent:
                device auth, account data, billing flows, chat sessions, and release manifests.
              </p>
              <div className="config-block">
                <div>
                  KRUD_PUBLIC_BASE_URL = <strong>"{API_BASE_URL}"</strong>
                </div>
                <div>
                  KRUD_DEVICE_BASE_URL = <strong>"{DEVICE_BASE_URL}"</strong>
                </div>
                <div>OPENAI_API_KEY = <strong>"set on backend"</strong></div>
                <div>KRUD_BILLING_MODE = <strong>"mock" | "dodo"</strong></div>
              </div>
              <ul className="docs-steps">
                <li>Use the main-domain <span className="inline-code">/login</span> route for device approval pages.</li>
                <li>Billing and release metadata can stay behind the same control plane.</li>
                <li>Legacy <span className="inline-code">/cli-auth</span> or <span className="inline-code">/device</span> paths can redirect into that same page.</li>
              </ul>
            </Reveal>
          </div>
        </div>
      </section>
    </>
  );
}
