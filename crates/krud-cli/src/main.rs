mod ui;

use std::env;
use std::fs;
use std::io::{self, Read, Write};
use std::os::unix::net::UnixStream;
use std::path::Path;
use std::process::Command;
use std::time::Duration;

use anyhow::{anyhow, Context, Result};
use clap::{Args, Parser, Subcommand};
use crossterm::event::{self, Event, KeyCode, KeyModifiers};
use krud_core::{
    api_base_url, append_local_message, copy_file_if_exists, delete_session_token, init_local_db,
    read_session_token, recent_tasks, store_session_token, task_counts, upsert_local_session,
    AccountResponse, AppPaths, ChatReply, CommandProposal, DevicePollResponse, DeviceStartResponse,
    IpcRequest, IpcResponse, SERVICE_NAME,
};
use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION};
use tokio::time::sleep;

#[derive(Parser)]
#[command(name = "krud", about = "Krud AI terminal agent")]
struct Cli {
    #[command(subcommand)]
    command: Option<Commands>,
}

#[derive(Subcommand)]
enum Commands {
    Chat(ChatArgs),
    Login,
    Logout,
    Status,
    Run(RunArgs),
    Update,
    Daemon(DaemonCommand),
}

#[derive(Args)]
struct ChatArgs {
    prompt: Option<String>,
}

#[derive(Args)]
struct RunArgs {
    task: String,
}

#[derive(Subcommand)]
enum DaemonAction {
    Install,
    Start,
    Stop,
}

#[derive(Args)]
struct DaemonCommand {
    #[command(subcommand)]
    action: DaemonAction,
}

enum ProposalDecision {
    Run,
    Queue,
    Skip,
}

enum ChatRequestError {
    SessionExpired,
    Message(String),
}

struct PendingActions {
    proposals: Vec<CommandProposal>,
    index: usize,
    ran: usize,
    queued: usize,
    skipped: usize,
}

struct InteractiveChatState {
    items: Vec<ui::FullscreenItem>,
    input: String,
    scroll_from_bottom: usize,
    pending: Option<PendingActions>,
}

#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();
    let paths = AppPaths::discover()?;
    paths.ensure()?;
    init_local_db(&paths)?;

    let command = cli
        .command
        .unwrap_or(Commands::Chat(ChatArgs { prompt: None }));

    // For any command that needs auth (chat, status, run), ensure the user
    // is logged in first. If no session token exists, automatically start
    // the login flow before continuing.
    let needs_auth = matches!(
        command,
        Commands::Chat(_) | Commands::Status | Commands::Run(_)
    );
    if needs_auth && read_session_token()?.is_none() {
        login().await?;
        // If login was cancelled or failed, stop here.
        if read_session_token()?.is_none() {
            return Ok(());
        }
    }

    match command {
        Commands::Chat(args) => chat(&paths, args).await?,
        Commands::Login => login().await?,
        Commands::Logout => logout()?,
        Commands::Status => status(&paths).await?,
        Commands::Run(args) => {
            let message = queue_task(&paths, &args.task)?;
            ui::print_success(&message);
        }
        Commands::Update => update().await?,
        Commands::Daemon(command) => manage_daemon(&paths, command.action)?,
    }

    Ok(())
}

async fn login() -> Result<()> {
    // ── connection check ──────────────────────────────────────────────────────
    ui::print_connecting();
    let client = reqwest::Client::new();
    let health = client
        .get(format!("{}/healthz", api_base_url()))
        .send()
        .await;
    ui::clear_connecting();
    if health.is_err() || !health.unwrap().status().is_success() {
        ui::print_connect_failed(&api_base_url());
        return Ok(());
    }

    // ── start device flow ─────────────────────────────────────────────────────
    let response = client
        .post(format!("{}/v1/device/start", api_base_url()))
        .json(&serde_json::json!({ "client_name": "krud-cli" }))
        .send()
        .await?
        .error_for_status()?
        .json::<DeviceStartResponse>()
        .await?;

    ui::print_login_screen(&response.verification_uri_complete);
    let _ = Command::new("open")
        .arg(&response.verification_uri_complete)
        .status();

    // ── poll for approval ─────────────────────────────────────────────────────
    loop {
        ui::print_login_waiting();
        sleep(Duration::from_secs(response.interval_seconds)).await;
        ui::clear_login_waiting();

        let poll = client
            .post(format!("{}/v1/device/poll", api_base_url()))
            .json(&serde_json::json!({ "device_code": response.device_code }))
            .send()
            .await?
            .error_for_status()?
            .json::<DevicePollResponse>()
            .await?;

        match poll.status.as_str() {
            "approved" => {
                let token = poll.session_token.clone().ok_or_else(|| {
                    anyhow!("Approved device flow did not return a session token")
                })?;
                store_session_token(&token)?;
                let email = poll
                    .account
                    .as_ref()
                    .map(|account| account.email.as_str())
                    .unwrap_or("unknown");
                ui::print_login_success(email);
                break;
            }
            "expired" => {
                ui::print_login_expired();
                return Ok(());
            }
            _ => {} // still pending — loop continues
        }
    }

    Ok(())
}

fn logout() -> Result<()> {
    delete_session_token()?;
    ui::print_success("Logged out of Krud AI.");
    Ok(())
}

async fn status(paths: &AppPaths) -> Result<()> {
    let token = read_session_token()?;
    ui::print_header(None);
    ui::print_section_title("system status", Some("local runtime"));
    ui::print_kv("api", &api_base_url());
    ui::print_kv(
        "session",
        if token.is_some() {
            "present"
        } else {
            "missing"
        },
    );
    ui::print_kv("socket", &paths.socket_path.display().to_string());
    ui::print_kv("db", &paths.db_path.display().to_string());

    if let Some(response) = ping_daemon(&paths.socket_path) {
        ui::print_kv("daemon", &response.message);
    } else {
        ui::print_kv("daemon", "not reachable");
    }

    let counts = task_counts(paths)?;
    ui::print_kv(
        "tasks",
        &format!(
            "queued={} running={} completed={} failed={}",
            counts.queued, counts.running, counts.completed, counts.failed
        ),
    );

    let recent = recent_tasks(paths, 3)?;
    if !recent.is_empty() {
        ui::print_section_title("recent tasks", Some("latest 3"));
        for task in recent {
            ui::print_info(&format!(
                "{} [{}] {} ({})",
                task.id, task.status, task.command, task.cwd
            ));
        }
    }

    if let Some(token) = token {
        let client = authenticated_client(&token)?;
        let account = client
            .get(format!("{}/v1/account/me", api_base_url()))
            .send()
            .await?;
        if account.status().is_success() {
            let body: AccountResponse = account.json().await?;
            ui::print_kv("account", &body.email);
        } else {
            ui::print_kv("account", "stored session token is invalid");
        }
    }

    println!();
    Ok(())
}

async fn chat(paths: &AppPaths, args: ChatArgs) -> Result<()> {
    // Token is guaranteed to exist — main() runs login() if absent.
    let token = read_session_token()?.expect("session token must exist before chat");
    let client = authenticated_client(&token)?;

    // ── connection check ──────────────────────────────────────────────────────
    ui::print_connecting();
    let health = client
        .get(format!("{}/healthz", api_base_url()))
        .send()
        .await;
    ui::clear_connecting();
    match health {
        Err(_) => {
            ui::print_connect_failed(&api_base_url());
            return Ok(());
        }
        Ok(r) if !r.status().is_success() => {
            ui::print_connect_failed(&api_base_url());
            return Ok(());
        }
        _ => {}
    }

    // ── fetch account (verify token, get email) ───────────────────────────────
    let email: Option<String> = async {
        let resp = client
            .get(format!("{}/v1/account/me", api_base_url()))
            .send()
            .await
            .ok()?;
        if resp.status() == reqwest::StatusCode::UNAUTHORIZED {
            return None; // handled below
        }
        let body: AccountResponse = resp.json().await.ok()?;
        let e = body.email;
        Some(if e.len() > 28 {
            format!("{}…", &e[..27])
        } else {
            e
        })
    }
    .await;

    // If /account/me returned 401, session is expired.
    // Re-check to distinguish "network fine but token bad" vs "no email field".
    {
        let check = client
            .get(format!("{}/v1/account/me", api_base_url()))
            .send()
            .await;
        if let Ok(r) = check {
            if r.status() == reqwest::StatusCode::UNAUTHORIZED {
                ui::print_session_expired();
                return Ok(());
            }
        }
    }

    ui::print_header(email.as_deref());

    let mut session_id = create_chat_session(&client, paths).await?;

    // One-shot mode: prompt provided as argument.
    if let Some(prompt) = args.prompt {
        handle_prompt(paths, &client, &session_id, &prompt).await?;
        return Ok(());
    }

    interactive_chat_fullscreen(paths, &client, email, &mut session_id).await?;
    Ok(())
}

async fn handle_prompt(
    paths: &AppPaths,
    client: &reqwest::Client,
    session_id: &str,
    prompt: &str,
) -> Result<()> {
    // Show what the user typed as a chat bubble.
    ui::print_user_message(prompt);

    append_local_message(paths, session_id, "user", prompt)?;

    let reply = match request_chat_reply(client, session_id, prompt).await {
        Ok(reply) => reply,
        Err(ChatRequestError::SessionExpired) => {
            ui::print_session_expired();
            return Ok(());
        }
        Err(ChatRequestError::Message(message)) => {
            ui::print_error(&message);
            return Ok(());
        }
    };

    append_local_message(paths, session_id, "assistant", &reply.text)?;

    // Display the assistant reply.
    ui::print_assistant_message(&reply.text, &reply.usage.model);

    // Display each command proposal with action buttons.
    let total = reply.command_proposals.len();
    if total == 0 {
        ui::print_success("No terminal actions were proposed for that reply.");
        return Ok(());
    }

    let mut ran = 0usize;
    let mut queued = 0usize;
    let mut skipped = 0usize;
    for (i, proposal) in reply.command_proposals.iter().enumerate() {
        ui::print_command_proposal(
            &proposal.command,
            &proposal.rationale,
            &proposal.risk,
            i,
            total,
        );

        match read_proposal_decision()? {
            ProposalDecision::Run => {
                ui::print_info(&format!("Running approved command: {}", proposal.command));
                let result = run_shell_command(&proposal.command);
                match result {
                    Ok(output) => {
                        ran += 1;
                        if !output.is_empty() {
                            print!("{output}");
                            if !output.ends_with('\n') {
                                println!();
                            }
                        }
                        ui::print_success("Command completed.");
                    }
                    Err(error) => {
                        ui::print_error(&format!("Command failed: {error}"));
                    }
                }
            }
            ProposalDecision::Queue => match queue_task(paths, &proposal.command) {
                Ok(message) => {
                    queued += 1;
                    ui::print_success(&message);
                }
                Err(error) => {
                    ui::print_error(&format!("Could not queue: {error}"));
                }
            },
            ProposalDecision::Skip => {
                skipped += 1;
                ui::print_info("Skipped.");
            }
        }
        println!();
    }

    ui::print_action_summary(ran, queued, skipped);

    Ok(())
}

async fn interactive_chat_fullscreen(
    paths: &AppPaths,
    client: &reqwest::Client,
    email: Option<String>,
    session_id: &mut String,
) -> Result<()> {
    let _guard = ui::FullscreenGuard::enter()?;
    let mut state = InteractiveChatState {
        items: vec![ui::FullscreenItem::Welcome(
            "Describe the outcome you want. Krud will answer directly and only suggest shell work when it helps.".to_string(),
        )],
        input: String::new(),
        scroll_from_bottom: 0,
        pending: None,
    };
    let mut toy_frame = 0usize;
    let mut toy_typing_burst = 0u8;

    loop {
        let cwd = env::current_dir()
            .ok()
            .and_then(|path| path.to_str().map(|value| value.to_string()));
        let input_label = if state.pending.is_some() {
            "choose [r/q/s] >"
        } else {
            "krud >"
        };
        ui::render_fullscreen(
            email.as_deref(),
            cwd.as_deref(),
            &state.items,
            input_label,
            &state.input,
            state.scroll_from_bottom,
            toy_frame,
            toy_typing_burst,
        )?;

        if !event::poll(Duration::from_millis(240))? {
            toy_frame = toy_frame.wrapping_add(1);
            if toy_typing_burst > 0 {
                toy_typing_burst -= 1;
            }
            continue;
        }

        match event::read()? {
            Event::Resize(_, _) => continue,
            Event::Key(key) => {
                let mut typing_action = false;
                match key.code {
                    KeyCode::Char('c') if key.modifiers.contains(KeyModifiers::CONTROL) => break,
                    KeyCode::Char('d')
                        if key.modifiers.contains(KeyModifiers::CONTROL)
                            && state.input.is_empty() =>
                    {
                        break
                    }
                    KeyCode::Esc => state.input.clear(),
                    KeyCode::Backspace => {
                        state.input.pop();
                        typing_action = true;
                    }
                    KeyCode::Up => {
                        state.scroll_from_bottom = state.scroll_from_bottom.saturating_add(1);
                    }
                    KeyCode::Down => {
                        state.scroll_from_bottom = state.scroll_from_bottom.saturating_sub(1);
                    }
                    KeyCode::PageUp => {
                        state.scroll_from_bottom = state.scroll_from_bottom.saturating_add(8);
                    }
                    KeyCode::PageDown => {
                        state.scroll_from_bottom = state.scroll_from_bottom.saturating_sub(8);
                    }
                    KeyCode::End => {
                        state.scroll_from_bottom = 0;
                    }
                    KeyCode::Enter => {
                        let input = std::mem::take(&mut state.input);
                        let trimmed = input.trim().to_string();

                        if let Some(mut pending) = state.pending.take() {
                            let decision = match trimmed.to_ascii_lowercase().as_str() {
                                "r" | "run" | "y" | "yes" => ProposalDecision::Run,
                                "q" | "queue" => ProposalDecision::Queue,
                                "" | "s" | "skip" | "n" | "no" => ProposalDecision::Skip,
                                _ => {
                                    state.items.push(ui::FullscreenItem::Info(
                                        "Use r to run, q to queue, or s to skip.".to_string(),
                                    ));
                                    state.pending = Some(pending);
                                    state.scroll_from_bottom = 0;
                                    continue;
                                }
                            };

                            let proposal = pending.proposals[pending.index].clone();
                            match decision {
                                ProposalDecision::Run => {
                                    state.items.push(ui::FullscreenItem::Info(format!(
                                        "Running approved command: {}",
                                        proposal.command
                                    )));
                                    let result = run_shell_command(&proposal.command);
                                    match result {
                                        Ok(output) => {
                                            pending.ran += 1;
                                            if !output.is_empty() {
                                                state.items.push(ui::FullscreenItem::Info(output));
                                            }
                                            state.items.push(ui::FullscreenItem::Success(
                                                "Command completed.".to_string(),
                                            ));
                                        }
                                        Err(error) => {
                                            state.items.push(ui::FullscreenItem::Error(format!(
                                                "Command failed: {error}"
                                            )));
                                        }
                                    }
                                }
                                ProposalDecision::Queue => {
                                    match queue_task(paths, &proposal.command) {
                                        Ok(message) => {
                                            pending.queued += 1;
                                            state.items.push(ui::FullscreenItem::Success(message));
                                        }
                                        Err(error) => {
                                            state.items.push(ui::FullscreenItem::Error(format!(
                                                "Could not queue: {error}"
                                            )));
                                        }
                                    }
                                }
                                ProposalDecision::Skip => {
                                    pending.skipped += 1;
                                    state
                                        .items
                                        .push(ui::FullscreenItem::Info("Skipped.".to_string()));
                                }
                            }

                            pending.index += 1;
                            if pending.index < pending.proposals.len() {
                                let next = &pending.proposals[pending.index];
                                state.items.push(ui::FullscreenItem::Action {
                                    command: next.command.clone(),
                                    rationale: next.rationale.clone(),
                                    risk: next.risk.clone(),
                                    index: pending.index,
                                    total: pending.proposals.len(),
                                });
                                state.pending = Some(pending);
                            } else {
                                state.items.push(ui::FullscreenItem::Success(format!(
                                    "Reply complete. Ran {}   queued {}   skipped {}",
                                    pending.ran, pending.queued, pending.skipped
                                )));
                            }
                            state.scroll_from_bottom = 0;
                            continue;
                        }

                        if trimmed.is_empty() {
                            continue;
                        }

                        match trimmed.as_str() {
                            "exit" | "quit" => break,
                            "/help" => {
                                state.items.push(ui::FullscreenItem::Info(
                                    "Commands: /help   /new   /status   /clear   exit".to_string(),
                                ));
                            }
                            "/clear" => {
                                state.items = vec![ui::FullscreenItem::Welcome(
                                "Describe the outcome you want. Krud will answer directly and only suggest shell work when it helps.".to_string(),
                            )];
                            }
                            "/status" => {
                                let cwd = env::current_dir()
                                    .ok()
                                    .and_then(|path| path.to_str().map(|value| value.to_string()))
                                    .unwrap_or_else(|| "unknown workspace".to_string());
                                state.items.push(ui::FullscreenItem::Info(format!(
                                    "session {}   cwd {}",
                                    session_id, cwd
                                )));
                            }
                            "/new" => match create_chat_session(client, paths).await {
                                Ok(new_session_id) => {
                                    *session_id = new_session_id.clone();
                                    state.items.push(ui::FullscreenItem::Success(format!(
                                        "Opened a new remote session: {}",
                                        new_session_id
                                    )));
                                }
                                Err(error) => {
                                    state.items.push(ui::FullscreenItem::Error(format!(
                                        "Could not open a new session: {error}"
                                    )));
                                }
                            },
                            _ => {
                                state.items.push(ui::FullscreenItem::User(trimmed.clone()));
                                append_local_message(paths, session_id, "user", &trimmed)?;
                                state.items.push(ui::FullscreenItem::Info(
                                    "Krud is thinking…".to_string(),
                                ));
                                state.scroll_from_bottom = 0;
                                ui::render_fullscreen(
                                    email.as_deref(),
                                    cwd.as_deref(),
                                    &state.items,
                                    input_label,
                                    &state.input,
                                    state.scroll_from_bottom,
                                    toy_frame,
                                    toy_typing_burst,
                                )?;

                                let reply_result =
                                    request_chat_reply(client, session_id, &trimmed).await;
                                if matches!(state.items.last(), Some(ui::FullscreenItem::Info(text)) if text == "Krud is thinking…")
                                {
                                    state.items.pop();
                                }

                                match reply_result {
                                    Ok(reply) => {
                                        append_local_message(
                                            paths,
                                            session_id,
                                            "assistant",
                                            &reply.text,
                                        )?;
                                        state.items.push(ui::FullscreenItem::Assistant {
                                            model: reply.usage.model.clone(),
                                            text: reply.text,
                                        });

                                        if reply.command_proposals.is_empty() {
                                            state.items.push(ui::FullscreenItem::Success(
                                                "No shell actions were proposed for that reply."
                                                    .to_string(),
                                            ));
                                        } else {
                                            let total = reply.command_proposals.len();
                                            let first = &reply.command_proposals[0];
                                            state.items.push(ui::FullscreenItem::Action {
                                                command: first.command.clone(),
                                                rationale: first.rationale.clone(),
                                                risk: first.risk.clone(),
                                                index: 0,
                                                total,
                                            });
                                            state.pending = Some(PendingActions {
                                                proposals: reply.command_proposals,
                                                index: 0,
                                                ran: 0,
                                                queued: 0,
                                                skipped: 0,
                                            });
                                        }
                                    }
                                    Err(ChatRequestError::SessionExpired) => {
                                        state.items.push(ui::FullscreenItem::Error(
                                            "Your session expired. Run `krud login` again."
                                                .to_string(),
                                        ));
                                        state.scroll_from_bottom = 0;
                                        break;
                                    }
                                    Err(ChatRequestError::Message(message)) => {
                                        state.items.push(ui::FullscreenItem::Error(message));
                                    }
                                }
                            }
                        }

                        state.scroll_from_bottom = 0;
                    }
                    KeyCode::Char(character)
                        if !key.modifiers.contains(KeyModifiers::CONTROL)
                            && !key.modifiers.contains(KeyModifiers::ALT) =>
                    {
                        state.input.push(character);
                        typing_action = true;
                    }
                    _ => {}
                }

                if typing_action {
                    toy_typing_burst = 6;
                    toy_frame = toy_frame.wrapping_add(1);
                } else if toy_typing_burst > 0 {
                    toy_typing_burst -= 1;
                }
            }
            _ => {}
        }
    }

    Ok(())
}

async fn create_chat_session(client: &reqwest::Client, paths: &AppPaths) -> Result<String> {
    let session: serde_json::Value = client
        .post(format!("{}/v1/chat/sessions", api_base_url()))
        .json(&serde_json::json!({ "title": "CLI Chat" }))
        .send()
        .await?
        .error_for_status()?
        .json()
        .await?;

    let session_id = session["session_id"]
        .as_str()
        .ok_or_else(|| anyhow!("Chat session response did not include a session_id"))?
        .to_string();
    let session_title = session["title"].as_str().unwrap_or("CLI Chat").to_string();
    upsert_local_session(paths, &session_id, &session_title)?;
    Ok(session_id)
}

async fn request_chat_reply(
    client: &reqwest::Client,
    session_id: &str,
    prompt: &str,
) -> std::result::Result<ChatReply, ChatRequestError> {
    let cwd = env::current_dir()
        .ok()
        .and_then(|path| path.to_str().map(|value| value.to_string()));

    let response = client
        .post(format!(
            "{}/v1/chat/sessions/{session_id}/messages",
            api_base_url()
        ))
        .json(&serde_json::json!({ "content": prompt, "cwd": cwd }))
        .send()
        .await
        .map_err(|error| ChatRequestError::Message(format!("Could not reach Krud: {error}")))?;

    if response.status() == reqwest::StatusCode::UNAUTHORIZED {
        return Err(ChatRequestError::SessionExpired);
    }

    let response = response.error_for_status().map_err(|error| {
        ChatRequestError::Message(format!("Krud returned an API error: {error}"))
    })?;

    response.json().await.map_err(|error| {
        ChatRequestError::Message(format!("Could not read the assistant response: {error}"))
    })
}

fn run_shell_command(command: &str) -> Result<String> {
    if command.trim_start().starts_with("git ") && !inside_git_repo()? {
        return Err(anyhow!(
            "current directory is not a Git repository; run `git init` first or change into a repo"
        ));
    }

    let output = Command::new("zsh").args(["-lc", command]).output()?;
    let stdout = String::from_utf8_lossy(&output.stdout)
        .trim_end()
        .to_string();
    let stderr = String::from_utf8_lossy(&output.stderr)
        .trim_end()
        .to_string();
    let mut rendered = String::new();
    if !stdout.is_empty() {
        rendered.push_str(&stdout);
    }
    if !stderr.is_empty() {
        if !rendered.is_empty() {
            rendered.push('\n');
        }
        rendered.push_str(&stderr);
    }

    if !output.status.success() {
        if rendered.is_empty() {
            return Err(anyhow!("command exited with status {}", output.status));
        }
        return Err(anyhow!(
            "{}\ncommand exited with status {}",
            rendered,
            output.status
        ));
    }

    Ok(rendered)
}

fn inside_git_repo() -> Result<bool> {
    let output = Command::new("git")
        .args(["rev-parse", "--is-inside-work-tree"])
        .output()?;
    Ok(output.status.success())
}

fn queue_task(paths: &AppPaths, task: &str) -> Result<String> {
    let cwd = env::current_dir()
        .context("Could not determine current directory")?
        .display()
        .to_string();
    let response = send_ipc_request(
        &paths.socket_path,
        &IpcRequest::QueueCommand {
            command: task.to_string(),
            cwd,
        },
    )?;
    Ok(response.message)
}

fn read_proposal_decision() -> Result<ProposalDecision> {
    loop {
        ui::print_decision_prompt();

        let mut decision = String::new();
        io::stdin().read_line(&mut decision)?;
        let decision = decision.trim().to_lowercase();

        match decision.as_str() {
            "r" | "run" | "y" | "yes" => return Ok(ProposalDecision::Run),
            "q" | "queue" => return Ok(ProposalDecision::Queue),
            "" | "s" | "skip" | "n" | "no" => return Ok(ProposalDecision::Skip),
            _ => ui::print_info("Use r to run, q to queue, or s to skip."),
        }
    }
}

async fn update() -> Result<()> {
    let client = reqwest::Client::new();
    let release: serde_json::Value = client
        .get(format!(
            "{}/v1/releases/latest?channel=stable",
            api_base_url()
        ))
        .send()
        .await?
        .error_for_status()?
        .json()
        .await?;

    ui::print_section_title("release channel", Some("stable"));
    ui::print_kv("latest", release["version"].as_str().unwrap_or("unknown"));
    ui::print_info(
        "Use install/install.sh to wire a real binary swap step during release publishing.",
    );
    Ok(())
}

fn manage_daemon(paths: &AppPaths, action: DaemonAction) -> Result<()> {
    match action {
        DaemonAction::Install => {
            install_daemon_binary(paths)?;
            let template = include_str!("../../../launchd/in.dabcloud.krudd.plist");
            let daemon_binary = paths.daemon_binary.display().to_string();
            let log_dir = paths.log_dir.display().to_string();
            let rendered = template
                .replace("__KRUDD_BINARY__", &daemon_binary)
                .replace("__KRUD_LOG_DIR__", &log_dir);

            if let Some(parent) = paths.launch_agent_path.parent() {
                fs::create_dir_all(parent)?;
            }
            fs::write(&paths.launch_agent_path, rendered)?;
            ui::print_success(&format!("Wrote {}", paths.launch_agent_path.display()));
            ui::print_info(&format!(
                "Daemon binary ready at {}",
                paths.daemon_binary.display()
            ));
        }
        DaemonAction::Start => {
            let status = Command::new("launchctl")
                .args([
                    "load",
                    "-w",
                    paths.launch_agent_path.to_str().unwrap_or_default(),
                ])
                .status()
                .context("Failed to load LaunchAgent")?;
            if !status.success() {
                return Err(anyhow!("launchctl load failed with status {}", status));
            }
            ui::print_success(&format!("Started {SERVICE_NAME}"));
        }
        DaemonAction::Stop => {
            let status = Command::new("launchctl")
                .args([
                    "unload",
                    "-w",
                    paths.launch_agent_path.to_str().unwrap_or_default(),
                ])
                .status()
                .context("Failed to unload LaunchAgent")?;
            if !status.success() {
                return Err(anyhow!("launchctl unload failed with status {}", status));
            }
            ui::print_success(&format!("Stopped {SERVICE_NAME}"));
        }
    }

    Ok(())
}

fn install_daemon_binary(paths: &AppPaths) -> Result<()> {
    let current = env::current_exe().context("Could not determine current executable path")?;
    let current_dir = env::current_dir().ok();
    let candidate_paths = [
        current.parent().map(|dir| dir.join("krudd")),
        current_dir.map(|dir| dir.join("target/debug/krudd")),
    ];

    for candidate in candidate_paths.into_iter().flatten() {
        if copy_file_if_exists(&candidate, &paths.daemon_binary)? {
            return Ok(());
        }
    }

    Err(anyhow!(
        "Could not find a built krudd binary. Run `cargo build -p krudd` first."
    ))
}

fn authenticated_client(token: &str) -> Result<reqwest::Client> {
    let mut headers = HeaderMap::new();
    headers.insert(
        AUTHORIZATION,
        HeaderValue::from_str(&format!("Bearer {token}")).context("Invalid token header")?,
    );

    Ok(reqwest::Client::builder()
        .default_headers(headers)
        .build()?)
}

fn ping_daemon(socket_path: &Path) -> Option<IpcResponse> {
    send_ipc_request(socket_path, &IpcRequest::Ping).ok()
}

fn send_ipc_request(socket_path: &Path, request: &IpcRequest) -> Result<IpcResponse> {
    let mut stream =
        UnixStream::connect(socket_path).context("Unable to connect to krudd socket")?;
    let payload = serde_json::to_vec(request)?;
    stream.write_all(&payload)?;
    stream.write_all(b"\n")?;

    let mut response = String::new();
    stream.read_to_string(&mut response)?;
    Ok(serde_json::from_str(&response)?)
}
