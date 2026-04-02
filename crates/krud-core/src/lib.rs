use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};

use anyhow::{anyhow, Context, Result};
use rusqlite::{params, Connection, OptionalExtension};
use serde::{Deserialize, Serialize};

pub const SERVICE_NAME: &str = "in.dabcloud.krudd";
pub const KEYCHAIN_SERVICE: &str = "Krud AI";
pub const KEYCHAIN_ACCOUNT: &str = "cli-session";

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SubscriptionStatus {
    Trialing,
    Active,
    PastDue,
    Canceled,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuthTokenResponse {
    pub token: String,
    pub email: String,
    pub name: Option<String>,
    pub subscription_status: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DeviceStartResponse {
    pub device_code: String,
    pub user_code: String,
    pub verification_uri: String,
    pub verification_uri_complete: String,
    pub interval_seconds: u64,
    pub expires_in_seconds: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AccountResponse {
    pub user_id: String,
    pub email: String,
    pub name: Option<String>,
    pub usage_events: Option<i64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SubscriptionResponse {
    pub status: String,
    pub trial_ends_at: String,
    pub price_id: String,
    pub customer_id: Option<String>,
    pub subscription_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DevicePollResponse {
    pub status: String,
    pub session_token: Option<String>,
    pub account: Option<AccountResponse>,
    pub subscription: Option<SubscriptionResponse>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommandProposal {
    pub command: String,
    pub rationale: String,
    pub risk: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UsageSummary {
    pub provider: String,
    pub model: String,
    pub prompt_tokens: i64,
    pub completion_tokens: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenBudget {
    pub used: i64,
    pub limit: i64,
    pub resets_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatReply {
    pub session_id: String,
    pub text: String,
    pub command_proposals: Vec<CommandProposal>,
    pub provider: String,
    pub usage: UsageSummary,
    pub budget: TokenBudget,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrgAction {
    pub action_type: String, // "command" | "create_file" | "create_dir"
    pub path: Option<String>,
    pub content: Option<String>,
    pub command: Option<String>,
    pub rationale: String,
    pub risk: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrgAnalyzeResponse {
    pub stack: String,
    pub summary: String,
    pub actions: Vec<OrgAction>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum IpcRequest {
    Ping,
    QueueCommand { command: String, cwd: String },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IpcResponse {
    pub ok: bool,
    pub message: String,
}

#[derive(Debug, Clone)]
pub struct AppPaths {
    pub base: PathBuf,
    pub bin_dir: PathBuf,
    pub config_dir: PathBuf,
    pub run_dir: PathBuf,
    pub log_dir: PathBuf,
    pub socket_path: PathBuf,
    pub daemon_binary: PathBuf,
    pub launch_agent_path: PathBuf,
    pub db_path: PathBuf,
}

#[derive(Debug, Clone)]
pub struct TaskRecord {
    pub id: String,
    pub command: String,
    pub cwd: String,
    pub status: String,
    pub output: Option<String>,
}

#[derive(Debug, Clone, Default)]
pub struct TaskCounts {
    pub queued: i64,
    pub running: i64,
    pub completed: i64,
    pub failed: i64,
}

impl AppPaths {
    pub fn discover() -> Result<Self> {
        let home = dirs::home_dir().ok_or_else(|| anyhow!("Home directory not found"))?;
        let base = home.join(".krud");
        let bin_dir = base.join("bin");
        let config_dir = base.join("config");
        let run_dir = base.join("run");
        let log_dir = base.join("logs");
        let socket_path = run_dir.join("krudd.sock");
        let daemon_binary = bin_dir.join("krudd");
        let launch_agent_path = home
            .join("Library/LaunchAgents")
            .join(format!("{SERVICE_NAME}.plist"));
        let db_path = base.join("local.db");

        Ok(Self {
            base,
            bin_dir,
            config_dir,
            run_dir,
            log_dir,
            socket_path,
            daemon_binary,
            launch_agent_path,
            db_path,
        })
    }

    pub fn ensure(&self) -> Result<()> {
        fs::create_dir_all(&self.base)?;
        fs::create_dir_all(&self.bin_dir)?;
        fs::create_dir_all(&self.config_dir)?;
        fs::create_dir_all(&self.run_dir)?;
        fs::create_dir_all(&self.log_dir)?;
        Ok(())
    }
}

pub fn api_base_url() -> String {
    std::env::var("KRUD_API_BASE_URL")
        .unwrap_or_else(|_| "https://krud-api.onrender.com".to_string())
}

pub fn store_session_token(token: &str) -> Result<()> {
    let status = Command::new("security")
        .args([
            "add-generic-password",
            "-U",
            "-s",
            KEYCHAIN_SERVICE,
            "-a",
            KEYCHAIN_ACCOUNT,
            "-w",
            token,
        ])
        .status()
        .context("Failed to write Krud AI token to Keychain")?;

    if !status.success() {
        return Err(anyhow!("macOS security command returned a non-zero status"));
    }
    Ok(())
}

pub fn read_session_token() -> Result<Option<String>> {
    let output = Command::new("security")
        .args([
            "find-generic-password",
            "-s",
            KEYCHAIN_SERVICE,
            "-a",
            KEYCHAIN_ACCOUNT,
            "-w",
        ])
        .output()
        .context("Failed to read Krud AI token from Keychain")?;

    if !output.status.success() {
        return Ok(None);
    }

    let token = String::from_utf8(output.stdout)?.trim().to_string();
    if token.is_empty() {
        return Ok(None);
    }
    Ok(Some(token))
}

pub fn delete_session_token() -> Result<()> {
    let output = Command::new("security")
        .args([
            "delete-generic-password",
            "-s",
            KEYCHAIN_SERVICE,
            "-a",
            KEYCHAIN_ACCOUNT,
        ])
        .output()
        .context("Failed to delete Krud AI token from Keychain")?;

    if !output.status.success() {
        return Err(anyhow!("macOS security command returned a non-zero status"));
    }
    Ok(())
}

pub fn init_local_db(paths: &AppPaths) -> Result<()> {
    let conn = open_local_db(paths)?;
    conn.execute_batch(
        "
        create table if not exists local_sessions (
            id text primary key,
            title text not null,
            created_at integer not null
        );
        create table if not exists local_messages (
            id integer primary key autoincrement,
            session_id text not null,
            role text not null,
            content text not null,
            created_at integer not null
        );
        create table if not exists local_tasks (
            id text primary key,
            command text not null,
            cwd text not null,
            status text not null,
            output text,
            created_at integer not null,
            updated_at integer not null
        );
        ",
    )?;
    Ok(())
}

pub fn open_local_db(paths: &AppPaths) -> Result<Connection> {
    paths.ensure()?;
    let conn = Connection::open(&paths.db_path)?;
    Ok(conn)
}

pub fn upsert_local_session(paths: &AppPaths, session_id: &str, title: &str) -> Result<()> {
    let conn = open_local_db(paths)?;
    conn.execute(
        "
        insert into local_sessions (id, title, created_at)
        values (?1, ?2, ?3)
        on conflict(id) do update set title = excluded.title
        ",
        params![session_id, title, now_ts()],
    )?;
    Ok(())
}

pub fn append_local_message(
    paths: &AppPaths,
    session_id: &str,
    role: &str,
    content: &str,
) -> Result<()> {
    let conn = open_local_db(paths)?;
    conn.execute(
        "
        insert into local_messages (session_id, role, content, created_at)
        values (?1, ?2, ?3, ?4)
        ",
        params![session_id, role, content, now_ts()],
    )?;
    Ok(())
}

pub fn queue_local_task(paths: &AppPaths, command: &str, cwd: &str) -> Result<String> {
    let conn = open_local_db(paths)?;
    let task_id = format!("task_{}", unique_suffix());
    let now = now_ts();
    conn.execute(
        "
        insert into local_tasks (id, command, cwd, status, output, created_at, updated_at)
        values (?1, ?2, ?3, 'queued', null, ?4, ?4)
        ",
        params![task_id, command, cwd, now],
    )?;
    Ok(task_id)
}

pub fn pop_next_task(paths: &AppPaths) -> Result<Option<TaskRecord>> {
    let conn = open_local_db(paths)?;
    let mut statement = conn.prepare(
        "
        select id, command, cwd, status, output
        from local_tasks
        where status = 'queued'
        order by created_at asc
        limit 1
        ",
    )?;
    let task = statement
        .query_row([], |row| {
            Ok(TaskRecord {
                id: row.get(0)?,
                command: row.get(1)?,
                cwd: row.get(2)?,
                status: row.get(3)?,
                output: row.get(4)?,
            })
        })
        .optional()?;

    if let Some(task) = &task {
        conn.execute(
            "update local_tasks set status = 'running', updated_at = ?2 where id = ?1",
            params![task.id, now_ts()],
        )?;
    }

    Ok(task)
}

pub fn complete_task(paths: &AppPaths, task_id: &str, status: &str, output: &str) -> Result<()> {
    let conn = open_local_db(paths)?;
    conn.execute(
        "
        update local_tasks
        set status = ?2, output = ?3, updated_at = ?4
        where id = ?1
        ",
        params![task_id, status, output, now_ts()],
    )?;
    Ok(())
}

pub fn task_counts(paths: &AppPaths) -> Result<TaskCounts> {
    let conn = open_local_db(paths)?;
    let mut counts = TaskCounts::default();
    for (status_name, target) in [
        ("queued", &mut counts.queued),
        ("running", &mut counts.running),
        ("completed", &mut counts.completed),
        ("failed", &mut counts.failed),
    ] {
        let value: i64 = conn.query_row(
            "select count(*) from local_tasks where status = ?1",
            params![status_name],
            |row| row.get(0),
        )?;
        *target = value;
    }
    Ok(counts)
}

pub fn recent_tasks(paths: &AppPaths, limit: i64) -> Result<Vec<TaskRecord>> {
    let conn = open_local_db(paths)?;
    let mut statement = conn.prepare(
        "
        select id, command, cwd, status, output
        from local_tasks
        order by updated_at desc
        limit ?1
        ",
    )?;

    let rows = statement.query_map(params![limit], |row| {
        Ok(TaskRecord {
            id: row.get(0)?,
            command: row.get(1)?,
            cwd: row.get(2)?,
            status: row.get(3)?,
            output: row.get(4)?,
        })
    })?;

    let mut tasks = Vec::new();
    for row in rows {
        tasks.push(row?);
    }
    Ok(tasks)
}

pub fn now_ts() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs() as i64
}

pub fn copy_file_if_exists(source: &Path, destination: &Path) -> Result<bool> {
    if !source.exists() {
        return Ok(false);
    }
    if let Some(parent) = destination.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::copy(source, destination)?;
    let mut permissions = fs::metadata(destination)?.permissions();
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        permissions.set_mode(0o755);
        fs::set_permissions(destination, permissions)?;
    }
    Ok(true)
}

fn unique_suffix() -> String {
    format!("{}", now_ts())
}
