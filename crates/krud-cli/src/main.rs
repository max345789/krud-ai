use std::env;
use std::fs;
use std::io::{self, Read, Write};
use std::os::unix::net::UnixStream;
use std::path::Path;
use std::process::Command;
use std::time::Duration;

use anyhow::{anyhow, Context, Result};
use clap::{Args, Parser, Subcommand};
use krud_core::{
    api_base_url, append_local_message, copy_file_if_exists, delete_session_token, init_local_db,
    read_session_token, recent_tasks, store_session_token, task_counts, upsert_local_session,
    AccountResponse, AppPaths, ChatReply, DevicePollResponse, DeviceStartResponse, IpcRequest,
    IpcResponse, SERVICE_NAME,
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

#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();
    let paths = AppPaths::discover()?;
    paths.ensure()?;
    init_local_db(&paths)?;

    let command = cli
        .command
        .unwrap_or(Commands::Chat(ChatArgs { prompt: None }));

    match command {
        Commands::Chat(args) => chat(&paths, args).await?,
        Commands::Login => login().await?,
        Commands::Logout => logout()?,
        Commands::Status => status(&paths).await?,
        Commands::Run(args) => queue_task(&paths, &args.task)?,
        Commands::Update => update().await?,
        Commands::Daemon(command) => manage_daemon(&paths, command.action)?,
    }

    Ok(())
}

async fn login() -> Result<()> {
    let client = reqwest::Client::new();
    let response = client
        .post(format!("{}/v1/device/start", api_base_url()))
        .json(&serde_json::json!({ "client_name": "krud-cli" }))
        .send()
        .await?
        .error_for_status()?
        .json::<DeviceStartResponse>()
        .await?;

    println!("Open this page to approve Krud AI:");
    println!("{}", response.verification_uri_complete);
    let _ = Command::new("open")
        .arg(&response.verification_uri_complete)
        .status();

    loop {
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
                println!("Logged in as {email}");
                break;
            }
            "expired" => return Err(anyhow!("The device code expired before approval")),
            _ => {
                println!("Waiting for approval...");
                sleep(Duration::from_secs(response.interval_seconds)).await;
            }
        }
    }

    Ok(())
}

fn logout() -> Result<()> {
    delete_session_token()?;
    println!("Logged out of Krud AI");
    Ok(())
}

async fn status(paths: &AppPaths) -> Result<()> {
    let token = read_session_token()?;

    println!("Krud AI status");
    println!("API base URL: {}", api_base_url());
    println!(
        "Keychain session: {}",
        if token.is_some() {
            "present"
        } else {
            "missing"
        }
    );
    println!("Socket path: {}", paths.socket_path.display());
    println!("Daemon launch agent: {}", paths.launch_agent_path.display());
    println!("Local database: {}", paths.db_path.display());

    if let Some(response) = ping_daemon(&paths.socket_path) {
        println!("Daemon: {}", response.message);
    } else {
        println!("Daemon: not reachable");
    }

    let counts = task_counts(paths)?;
    println!(
        "Tasks: queued={} running={} completed={} failed={}",
        counts.queued, counts.running, counts.completed, counts.failed
    );
    for task in recent_tasks(paths, 3)? {
        println!(
            "  {} [{}] {} ({})",
            task.id, task.status, task.command, task.cwd
        );
    }

    if let Some(token) = token {
        let client = authenticated_client(&token)?;
        let account = client
            .get(format!("{}/v1/account/me", api_base_url()))
            .send()
            .await?;
        if account.status().is_success() {
            let body: AccountResponse = account.json().await?;
            println!(
                "Account: {} (usage events: {})",
                body.email,
                body.usage_events.unwrap_or(0)
            );
        } else {
            println!("Account: stored session token is invalid");
        }
    }

    Ok(())
}

async fn chat(paths: &AppPaths, args: ChatArgs) -> Result<()> {
    let token = read_session_token()?.ok_or_else(|| anyhow!("Run `krud login` first"))?;
    let client = authenticated_client(&token)?;

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

    if let Some(prompt) = args.prompt {
        handle_prompt(paths, &client, &session_id, &prompt).await?;
        return Ok(());
    }

    println!("Krud AI interactive chat. Type `exit` to leave.");
    loop {
        print!("krud> ");
        io::stdout().flush()?;
        let mut input = String::new();
        io::stdin().read_line(&mut input)?;
        let trimmed = input.trim();
        if trimmed.eq_ignore_ascii_case("exit") {
            break;
        }
        if trimmed.is_empty() {
            continue;
        }
        handle_prompt(paths, &client, &session_id, trimmed).await?;
    }

    Ok(())
}

async fn handle_prompt(
    paths: &AppPaths,
    client: &reqwest::Client,
    session_id: &str,
    prompt: &str,
) -> Result<()> {
    append_local_message(paths, session_id, "user", prompt)?;
    let cwd = env::current_dir()
        .ok()
        .and_then(|path| path.to_str().map(|value| value.to_string()));
    let reply = client
        .post(format!(
            "{}/v1/chat/sessions/{session_id}/messages",
            api_base_url()
        ))
        .json(&serde_json::json!({ "content": prompt, "cwd": cwd }))
        .send()
        .await?
        .error_for_status()?
        .json::<ChatReply>()
        .await?;

    append_local_message(paths, session_id, "assistant", &reply.text)?;
    println!("\n{}\n", reply.text);
    println!(
        "Provider: {} ({}) tokens {} in / {} out\n",
        reply.provider, reply.usage.model, reply.usage.prompt_tokens, reply.usage.completion_tokens
    );

    for proposal in reply.command_proposals {
        println!("Proposed command [{}]: {}", proposal.risk, proposal.command);
        println!("Reason: {}", proposal.rationale);
        print!("Run it now, queue it, or skip? [r/q/N] ");
        io::stdout().flush()?;

        let mut decision = String::new();
        io::stdin().read_line(&mut decision)?;
        let decision = decision.trim().to_lowercase();
        match decision.as_str() {
            "r" => {
                if let Err(error) = run_shell_command(&proposal.command) {
                    eprintln!("Krud could not complete `{}`: {error}", proposal.command);
                }
            }
            "q" => {
                if let Err(error) = queue_task(paths, &proposal.command) {
                    eprintln!("Krud could not queue `{}`: {error}", proposal.command);
                }
            }
            _ => {}
        }
    }

    Ok(())
}

fn run_shell_command(command: &str) -> Result<()> {
    if command.trim_start().starts_with("git ") && !inside_git_repo()? {
        return Err(anyhow!(
            "current directory is not a Git repository; run `git init` first or change into a repo"
        ));
    }

    let output = Command::new("zsh").args(["-lc", command]).output()?;
    if !output.stdout.is_empty() {
        print!("{}", String::from_utf8_lossy(&output.stdout));
    }
    if !output.stderr.is_empty() {
        eprint!("{}", String::from_utf8_lossy(&output.stderr));
    }
    if !output.status.success() {
        return Err(anyhow!("command exited with status {}", output.status));
    }
    Ok(())
}

fn inside_git_repo() -> Result<bool> {
    let output = Command::new("git")
        .args(["rev-parse", "--is-inside-work-tree"])
        .output()?;
    Ok(output.status.success())
}

fn queue_task(paths: &AppPaths, task: &str) -> Result<()> {
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
    println!("{}", response.message);
    Ok(())
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

    println!(
        "Latest version: {}",
        release["version"].as_str().unwrap_or("unknown")
    );
    println!("Use install/install.sh to wire a real binary swap step during release publishing.");
    Ok(())
}

fn manage_daemon(paths: &AppPaths, action: DaemonAction) -> Result<()> {
    match action {
        DaemonAction::Install => {
            install_daemon_binary(paths)?;
            let template = include_str!("../../../launchd/in.krud.ai.plist");
            let daemon_binary = paths.daemon_binary.display().to_string();
            let log_dir = paths.log_dir.display().to_string();
            let rendered = template
                .replace("__KRUDD_BINARY__", &daemon_binary)
                .replace("__KRUD_LOG_DIR__", &log_dir);

            if let Some(parent) = paths.launch_agent_path.parent() {
                fs::create_dir_all(parent)?;
            }
            fs::write(&paths.launch_agent_path, rendered)?;
            println!("Wrote {}", paths.launch_agent_path.display());
            println!("Daemon binary ready at {}", paths.daemon_binary.display());
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
            println!("Started {SERVICE_NAME}");
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
            println!("Stopped {SERVICE_NAME}");
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
