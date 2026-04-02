import React, { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  ArrowRight,
  CircleAlert,
  CircleCheckBig,
  Loader2,
  LockKeyhole,
  LogOut,
  TimerReset,
} from 'lucide-react';
import BrandMark from '../components/BrandMark';
import { CommandWindow, Reveal } from '../components/ui';

const API = import.meta.env.VITE_API_BASE_URL || 'https://api.dabcloud.in';
const STORAGE_KEY = 'krud_browser_session';

function Countdown({ seconds }) {
  const minutes = Math.floor(seconds / 60).toString().padStart(2, '0');
  const remainder = (seconds % 60).toString().padStart(2, '0');
  const urgent = seconds <= 60 && seconds > 0;

  return (
    <span className={`inline-code ${urgent ? 'inline-code-danger' : ''}`}>
      {minutes}:{remainder}
    </span>
  );
}

function persistBrowserSession(session) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

function readBrowserSession() {
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    if (!parsed?.token) return null;
    return parsed;
  } catch {
    return null;
  }
}

function clearBrowserSession() {
  window.localStorage.removeItem(STORAGE_KEY);
}

export default function CliAuth() {
  const [params] = useSearchParams();
  const userCode = params.get('user_code') || '';

  const [mode, setMode] = useState('signup');
  const [sessionChecked, setSessionChecked] = useState(false);
  const [browserSession, setBrowserSession] = useState(null);
  const [status, setStatus] = useState('idle');
  const [errMsg, setErrMsg] = useState('');
  const [successEmail, setSuccessEmail] = useState('');
  const [timeLeft, setTimeLeft] = useState(600);

  const [signupForm, setSignupForm] = useState({
    name: '',
    email: '',
    password: '',
  });
  const [loginForm, setLoginForm] = useState({
    email: '',
    password: '',
  });

  useEffect(() => {
    if (timeLeft === 0) return;
    const id = window.setTimeout(() => {
      setTimeLeft((value) => Math.max(0, value - 1));
    }, 1000);
    return () => window.clearTimeout(id);
  }, [timeLeft]);

  useEffect(() => {
    let cancelled = false;

    async function validateExistingSession() {
      const stored = readBrowserSession();
      if (!stored?.token) {
        setSessionChecked(true);
        return;
      }

      try {
        const response = await fetch(`${API}/v1/account/me`, {
          headers: { Authorization: `Bearer ${stored.token}` },
        });
        if (!response.ok) {
          clearBrowserSession();
          if (!cancelled) {
            setBrowserSession(null);
            setSessionChecked(true);
          }
          return;
        }

        const account = await response.json();
        if (cancelled) return;
        const nextSession = {
          token: stored.token,
          email: account.email,
          name: account.name || stored.name || '',
        };
        setBrowserSession(nextSession);
        setSignupForm((current) => ({
          ...current,
          email: nextSession.email,
          name: nextSession.name || current.name,
        }));
        persistBrowserSession(nextSession);
      } catch {
        clearBrowserSession();
        if (!cancelled) {
          setBrowserSession(null);
        }
      } finally {
        if (!cancelled) {
          setSessionChecked(true);
        }
      }
    }

    validateExistingSession();
    return () => {
      cancelled = true;
    };
  }, []);

  const expired = timeLeft === 0;
  const missingCode = !userCode;
  const deviceFlow = !missingCode;
  const blocked = expired || missingCode;

  const errorMessage = useMemo(() => {
    if (missingCode && deviceFlow) {
      return 'No device code was attached to this page. Run krud login again from your terminal.';
    }
    if (expired) {
      return 'This device code expired. Run krud login again to generate a fresh approval request.';
    }
    return errMsg;
  }, [deviceFlow, errMsg, expired, missingCode]);

  async function handleLogout() {
    if (browserSession?.token) {
      try {
        await fetch(`${API}/v1/auth/logout`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${browserSession.token}` },
        });
      } catch {
        // Ignore logout transport errors and still clear local state.
      }
    }
    clearBrowserSession();
    setBrowserSession(null);
    setStatus('idle');
    setErrMsg('');
    setSuccessEmail('');
  }

  async function approveDevice(token, fallbackEmail = '') {
    if (blocked) {
      return;
    }

    setStatus('approving');
    setErrMsg('');

    try {
      const response = await fetch(`${API}/v1/device/approve-authenticated`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ user_code: userCode }),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || 'Approval failed');
      }

      const payload = await response.json();
      setSuccessEmail(payload.email || fallbackEmail);
      setStatus('approved');
      setErrMsg('');
    } catch (error) {
      setStatus('error');
      setErrMsg(error instanceof Error ? error.message : 'Approval failed');
    }
  }

  async function submitAuth(kind, event) {
    event.preventDefault();
    setStatus(kind === 'signup' ? 'signup' : 'login');
    setErrMsg('');

    const payload =
      kind === 'signup'
        ? {
            email: signupForm.email,
            password: signupForm.password,
            name: signupForm.name || undefined,
          }
        : {
            email: loginForm.email,
            password: loginForm.password,
          };

    try {
      const response = await fetch(`${API}/v1/auth/${kind}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || `${kind === 'signup' ? 'Sign up' : 'Login'} failed`);
      }

      const nextSession = {
        token: data.token,
        email: data.email,
        name: data.name || (kind === 'signup' ? signupForm.name : ''),
      };
      setBrowserSession(nextSession);
      persistBrowserSession(nextSession);

      if (deviceFlow) {
        await approveDevice(nextSession.token, nextSession.email);
        return;
      }

      setStatus('account-ready');
      setErrMsg('');
    } catch (error) {
      setStatus('error');
      setErrMsg(error instanceof Error ? error.message : 'Authentication failed');
    }
  }

  const busy = ['signup', 'login', 'approving'].includes(status);

  return (
    <div className="auth-shell">
      <div className="site-ambient" aria-hidden="true">
        <span className="site-ambient__glow site-ambient__glow-primary" />
        <span className="site-ambient__glow site-ambient__glow-secondary" />
        <span className="site-ambient__grid" />
      </div>

      <header className="auth-header">
        <div className="shell auth-header__inner">
          <Link to="/" className="brand-link">
            <BrandMark />
          </Link>
          <div className="button-row auth-header__actions">
            {browserSession ? (
              <button type="button" className="button button-secondary" onClick={handleLogout}>
                <LogOut size={15} />
                Log out
              </button>
            ) : null}
            <Link to="/" className="button button-secondary">
              Back to site
            </Link>
          </div>
        </div>
      </header>

      <main className="shell auth-main">
        <Reveal className="auth-copy">
          <p className="section-eyebrow">{deviceFlow ? 'Device approval' : 'Account access'}</p>
          <h1 className="auth-copy__title">
            {deviceFlow ? 'Create or sign in, then approve this terminal.' : 'Create your account or sign in.'}
          </h1>
          <p className="page-intro__description">
            {deviceFlow
              ? 'The browser page now confirms a real Krud account first. New users create an account. Returning users sign in and approve the device in one flow.'
              : 'This is the main web entry for Krud accounts. Use it to create an account, return later, and approve future device logins without starting from zero.'}
          </p>

          <ul className="detail-list">
            <li>Every CLI session ends up attached to a real user account.</li>
            <li>Returning users can approve quickly once the browser already remembers them.</li>
            <li>The terminal remains the place where work starts and finishes.</li>
          </ul>

          <div className="hero-notes auth-copy__notes">
            <span className="status-pill">
              <LockKeyhole size={14} />
              Account-first approval
            </span>
            {deviceFlow ? (
              <span className="status-pill">
                <TimerReset size={14} />
                Expires in <Countdown seconds={timeLeft} />
              </span>
            ) : null}
          </div>
        </Reveal>

        <Reveal delay={0.1} className="auth-panel">
          {status === 'approved' ? (
            <div className="auth-success">
              <span className="status-pill">
                <CircleCheckBig size={14} />
                Approved
              </span>
              <strong>Terminal connected for {successEmail}.</strong>
              <p>
                Your account is authenticated and the device approval is complete. Switch back
                to the CLI. The session is ready and you can close this tab.
              </p>
              <CommandWindow
                title="next step"
                label="ready"
                lines={[
                  { kind: 'command', text: 'krud chat' },
                  { kind: 'prompt', text: 'explain the last failed deploy in plain English' },
                  { kind: 'success', text: 'You are authenticated and ready to continue.' },
                ]}
              />
            </div>
          ) : (
            <>
              {(status === 'error' || (deviceFlow && blocked)) ? (
                <div className="auth-alert">
                  <p className="auth-alert__text">
                    <CircleAlert size={16} />
                    {errorMessage}
                  </p>
                </div>
              ) : null}

              {deviceFlow ? (
                <div className="auth-code">
                  <div className="auth-code__meta">
                    <span>Device code</span>
                    <span>{expired ? 'Expired' : 'Waiting for approval'}</span>
                  </div>
                  <div className="auth-code__value">{userCode || 'XXXX-XXXX'}</div>
                  <div className="auth-code__meta">
                    <span>Auto-filled from the terminal</span>
                    <span>{blocked ? 'Needs a fresh request' : 'Ready to confirm'}</span>
                  </div>
                </div>
              ) : null}

              {!sessionChecked ? (
                <div className="auth-state-card">
                  <Loader2 size={16} className="spin-icon" />
                  <span>Checking your saved browser session…</span>
                </div>
              ) : browserSession ? (
                <div className="auth-session-card">
                  <div className="auth-session-card__copy">
                    <p className="story-kicker">Saved account</p>
                    <strong>{browserSession.email}</strong>
                    <p>
                      {deviceFlow
                        ? 'You already have a browser session. Continue as this account or switch to another one.'
                        : 'You are already signed in on this browser.'}
                    </p>
                  </div>

                  {deviceFlow ? (
                    <div className="button-row auth-session-card__actions">
                      <button
                        type="button"
                        className="button button-primary"
                        onClick={() => approveDevice(browserSession.token, browserSession.email)}
                        disabled={busy || blocked}
                      >
                        {status === 'approving' ? (
                          <>
                            <Loader2 size={15} className="spin-icon" />
                            Approving…
                          </>
                        ) : (
                          <>
                            Approve device
                            <ArrowRight size={15} />
                          </>
                        )}
                      </button>
                      <button
                        type="button"
                        className="button button-secondary"
                        onClick={handleLogout}
                        disabled={busy}
                      >
                        Use another account
                      </button>
                    </div>
                  ) : (
                    <div className="button-row auth-session-card__actions">
                      <Link to="/pricing" className="button button-primary">
                        Continue to pricing
                      </Link>
                      <button
                        type="button"
                        className="button button-secondary"
                        onClick={handleLogout}
                      >
                        Log out
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <>
                  <div className="auth-switch" role="tablist" aria-label="Authentication mode">
                    <button
                      type="button"
                      className={`auth-switch__item ${mode === 'signup' ? 'is-active' : ''}`}
                      onClick={() => setMode('signup')}
                    >
                      Create account
                    </button>
                    <button
                      type="button"
                      className={`auth-switch__item ${mode === 'login' ? 'is-active' : ''}`}
                      onClick={() => setMode('login')}
                    >
                      Log in
                    </button>
                  </div>

                  {mode === 'signup' ? (
                    <form onSubmit={(event) => submitAuth('signup', event)} className="form-stack">
                      <div className="field">
                        <label htmlFor="signup-name">Name</label>
                        <input
                          id="signup-name"
                          type="text"
                          placeholder="Your name"
                          value={signupForm.name}
                          onChange={(event) =>
                            setSignupForm((current) => ({ ...current, name: event.target.value }))
                          }
                          disabled={busy}
                        />
                      </div>
                      <div className="field">
                        <label htmlFor="signup-email">Email</label>
                        <input
                          id="signup-email"
                          type="email"
                          required
                          placeholder="you@company.com"
                          value={signupForm.email}
                          onChange={(event) =>
                            setSignupForm((current) => ({ ...current, email: event.target.value }))
                          }
                          disabled={busy}
                        />
                      </div>
                      <div className="field">
                        <label htmlFor="signup-password">Password</label>
                        <input
                          id="signup-password"
                          type="password"
                          required
                          minLength={8}
                          placeholder="At least 8 characters"
                          value={signupForm.password}
                          onChange={(event) =>
                            setSignupForm((current) => ({ ...current, password: event.target.value }))
                          }
                          disabled={busy}
                        />
                      </div>
                      <button type="submit" className="button button-primary button-block" disabled={busy}>
                        {status === 'signup' ? (
                          <>
                            <Loader2 size={15} className="spin-icon" />
                            Creating account…
                          </>
                        ) : (
                          <>
                            {deviceFlow ? 'Create account and approve' : 'Create account'}
                            <ArrowRight size={15} />
                          </>
                        )}
                      </button>
                    </form>
                  ) : (
                    <form onSubmit={(event) => submitAuth('login', event)} className="form-stack">
                      <div className="field">
                        <label htmlFor="login-email">Email</label>
                        <input
                          id="login-email"
                          type="email"
                          required
                          placeholder="you@company.com"
                          value={loginForm.email}
                          onChange={(event) =>
                            setLoginForm((current) => ({ ...current, email: event.target.value }))
                          }
                          disabled={busy}
                        />
                      </div>
                      <div className="field">
                        <label htmlFor="login-password">Password</label>
                        <input
                          id="login-password"
                          type="password"
                          required
                          placeholder="Your password"
                          value={loginForm.password}
                          onChange={(event) =>
                            setLoginForm((current) => ({ ...current, password: event.target.value }))
                          }
                          disabled={busy}
                        />
                      </div>
                      <button type="submit" className="button button-primary button-block" disabled={busy}>
                        {status === 'login' ? (
                          <>
                            <Loader2 size={15} className="spin-icon" />
                            Logging in…
                          </>
                        ) : (
                          <>
                            {deviceFlow ? 'Log in and approve' : 'Log in'}
                            <ArrowRight size={15} />
                          </>
                        )}
                      </button>
                    </form>
                  )}

                  <p className="auth-note">
                    {deviceFlow
                      ? 'If you already created an account earlier, log in and approve the device. If not, create it here first.'
                      : 'Create a new account here or come back with a device code from the terminal.'}
                  </p>
                </>
              )}

              {!deviceFlow && status === 'account-ready' ? (
                <div className="auth-state-card">
                  <CircleCheckBig size={16} />
                  <span>Account ready. Return later with a device code, or continue into pricing.</span>
                </div>
              ) : null}
            </>
          )}
        </Reveal>
      </main>
    </div>
  );
}
