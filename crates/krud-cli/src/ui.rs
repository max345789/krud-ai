//! Terminal UI for krud.
//!
//! Visual direction:
//! - compact "control deck" layout instead of stacked generic boxes
//! - purple accent for brand and user actions
//! - steel-blue metadata and system chrome
//! - denser prompt dock so the interface feels like a terminal product,
//!   not a chat transcript with borders

use crossterm::cursor::{Hide, MoveTo, Show};
use crossterm::style::{
    Attribute, Color, Print, ResetColor, SetAttribute, SetBackgroundColor, SetForegroundColor,
    StyledContent, Stylize,
};
use crossterm::terminal::{
    self, disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen,
};
use crossterm::{execute, queue};
use std::io::{self, Write};

const COPPER: Color = Color::Rgb {
    r: 109,
    g: 40,
    b: 217,
};
const COPPER_SOFT: Color = Color::Rgb {
    r: 147,
    g: 51,
    b: 234,
};
const TEAL: Color = Color::Rgb {
    r: 126,
    g: 34,
    b: 206,
};
const TEAL_SOFT: Color = Color::Rgb {
    r: 167,
    g: 139,
    b: 250,
};
const CLOUD: Color = Color::Rgb {
    r: 91,
    g: 33,
    b: 182,
};
const SMOKE: Color = Color::Rgb {
    r: 126,
    g: 34,
    b: 206,
};
const SUCCESS: Color = Color::Rgb {
    r: 124,
    g: 58,
    b: 237,
};
const WARNING: Color = Color::Rgb {
    r: 220,
    g: 38,
    b: 38,
};
const DANGER: Color = Color::Rgb {
    r: 220,
    g: 38,
    b: 38,
};

pub fn term_width() -> usize {
    terminal::size().map(|(w, _)| w as usize).unwrap_or(80)
}

pub fn box_width() -> usize {
    term_width().saturating_sub(4).min(94).max(58)
}

fn inner_width(bw: usize) -> usize {
    bw.saturating_sub(4)
}

pub fn wrap(text: &str, width: usize) -> Vec<String> {
    if width == 0 {
        return vec![text.to_string()];
    }

    let mut lines = Vec::new();
    for para in text.split('\n') {
        if para.trim().is_empty() {
            lines.push(String::new());
            continue;
        }

        let mut current = String::new();
        for word in para.split_whitespace() {
            let word_len = word.chars().count();
            let current_len = current.chars().count();
            if current.is_empty() {
                current.push_str(word);
            } else if current_len + 1 + word_len <= width {
                current.push(' ');
                current.push_str(word);
            } else {
                lines.push(std::mem::take(&mut current));
                current.push_str(word);
            }
        }
        if !current.is_empty() {
            lines.push(current);
        }
    }

    lines
}

fn rail(color: Color) -> StyledContent<&'static str> {
    "│".with(color)
}

fn top_border(bw: usize, color: Color) {
    println!("  {}", format!("╭{}╮", "─".repeat(bw)).with(color));
}

fn rule(bw: usize, color: Color) {
    println!("  {}", format!("├{}┤", "─".repeat(bw)).with(color));
}

fn bottom_border(bw: usize, color: Color) {
    println!("  {}", format!("╰{}╯", "─".repeat(bw)).with(color));
}

fn body(colored: impl std::fmt::Display, raw_len: usize, bw: usize) {
    let inner = inner_width(bw);
    let pad = inner.saturating_sub(raw_len);
    println!("  │  {}{}  │", colored, " ".repeat(pad));
}

fn section_bar(title: &str, subtitle: Option<&str>, accent: Color) {
    match subtitle {
        Some(value) if !value.is_empty() => println!(
            "  {} {}  {}",
            "◆".with(accent).bold(),
            title.to_ascii_uppercase().with(accent).bold(),
            value.with(SMOKE)
        ),
        _ => println!(
            "  {} {}",
            "◆".with(accent).bold(),
            title.to_ascii_uppercase().with(accent).bold()
        ),
    }
}

fn print_top_bar(title: &str, right: &str) {
    let width = term_width().max(48);
    let gap = width
        .saturating_sub(title.chars().count() + right.chars().count() + 1)
        .max(1);
    println!();
    println!(
        " {}{}{}",
        title.with(COPPER).bold(),
        " ".repeat(gap),
        right.with(SMOKE)
    );
    println!(
        " {}",
        "─".repeat(width.saturating_sub(1)).with(TEAL_SOFT).dim()
    );
    println!();
}

fn shorten_path(cwd: &str) -> String {
    let parts: Vec<&str> = cwd.trim_end_matches('/').split('/').collect();
    if parts.len() > 3 {
        format!(
            "…/{}/{}",
            parts[parts.len().saturating_sub(2)],
            parts[parts.len().saturating_sub(1)]
        )
    } else {
        cwd.to_string()
    }
}

fn risk_color(risk: &str) -> Color {
    match risk.to_ascii_lowercase().as_str() {
        "low" | "safe" => SUCCESS,
        "high" | "critical" | "dangerous" => DANGER,
        _ => WARNING,
    }
}

fn draw_notice(title: &str, message: &str, accent: Color) {
    let body_color = if accent == DANGER || accent == WARNING {
        DANGER
    } else {
        CLOUD
    };
    println!();
    println!("  {}", title.with(accent).bold());
    for line in wrap(message, term_width().saturating_sub(4).min(96)) {
        println!("  {}", line.as_str().with(body_color));
    }
    println!();
}

pub fn print_header(email: Option<&str>) {
    print_top_bar("KRUD", email.unwrap_or("guest session"));
}

pub fn print_section_title(title: &str, subtitle: Option<&str>) {
    section_bar(title, subtitle, TEAL);
}

pub fn print_kv(label: &str, value: &str) {
    println!(
        "  {} {:<11} {}",
        rail(TEAL),
        label.with(SMOKE).bold(),
        value.with(CLOUD)
    );
}

pub fn print_user_message(text: &str) {
    let tw = term_width();
    let block_width = (tw * 54 / 100).min(70).max(22);
    for line in wrap(text, block_width) {
        let indent = tw.saturating_sub(line.chars().count()).saturating_sub(2);
        println!("{}{}", " ".repeat(indent), line.as_str().with(CLOUD).bold());
    }
    println!();
}

pub fn print_assistant_message(text: &str, model: &str) {
    let wrap_width = term_width().saturating_sub(6).min(92).max(40);

    println!("  {}", format!("krud · {}", model).with(COPPER).bold());
    for line in wrap(text, wrap_width) {
        if line.is_empty() {
            println!();
        } else {
            println!("  {}", line.as_str().with(CLOUD));
        }
    }
    println!();
}

pub fn print_command_proposal(
    command: &str,
    rationale: &str,
    risk: &str,
    index: usize,
    total: usize,
) {
    let bw = box_width();
    let accent = risk_color(risk);
    let risk_label = format!("risk {}", risk.to_ascii_lowercase());
    let command_width = inner_width(bw).saturating_sub(2);

    let command_display = if command.chars().count() > command_width {
        let mut truncated: String = command
            .chars()
            .take(command_width.saturating_sub(1))
            .collect();
        truncated.push('…');
        truncated
    } else {
        command.to_string()
    };

    println!(
        "  {}",
        format!("action {}/{} · {}", index + 1, total, risk_label)
            .with(SMOKE)
            .bold()
    );
    top_border(bw, accent);
    body(
        format!("$ {}", command_display).with(CLOUD).bold(),
        2 + command_display.chars().count(),
        bw,
    );
    for line in wrap(rationale, inner_width(bw)) {
        body(line.as_str().with(CLOUD), line.chars().count(), bw);
    }
    rule(bw, accent);
    body(
        format!(
            "{} run now   {} queue for daemon   {} skip",
            "[r]".with(SUCCESS).bold(),
            "[q]".with(TEAL).bold(),
            "[s]".with(SMOKE).bold()
        ),
        41,
        bw,
    );
    bottom_border(bw, accent);
    println!();
}

pub fn print_decision_prompt() {
    print!("  {} ", "choose [r/q/s] >".with(TEAL).bold());
    std::io::stdout().flush().ok();
}

pub fn print_action_summary(ran: usize, queued: usize, skipped: usize) {
    let summary = format!("ran {}   queued {}   skipped {}", ran, queued, skipped);
    println!("  {}", "reply complete".with(COPPER).bold());
    println!("  {}", summary.with(CLOUD));
    println!();
}

pub fn print_login_screen(url: &str) {
    print_top_bar("KRUD", "device flow");
    println!(
        "  {}",
        "Approve this machine in your browser using the link below.".with(CLOUD)
    );
    println!();
    for line in wrap(url, term_width().saturating_sub(4).min(96)) {
        println!("  {}", line.as_str().with(COPPER).bold().underlined());
    }
    println!();
    for line in wrap(
        "If a browser window does not open, paste the URL manually.",
        term_width().saturating_sub(4).min(96),
    ) {
        println!("  {}", line.as_str().with(SMOKE));
    }
    println!();
}

pub fn print_login_waiting() {
    print!(
        "  {} {}",
        "waiting".with(TEAL).bold(),
        "browser approval pending…".with(SMOKE)
    );
    std::io::stdout().flush().ok();
}

pub fn clear_login_waiting() {
    print!("\r\x1B[2K");
    std::io::stdout().flush().ok();
}

pub fn print_login_success(email: &str) {
    print_top_bar("KRUD", "connected");
    draw_notice(
        "login complete",
        &format!("Authenticated as {email}. Run `krud` or `krud chat` to start."),
        SUCCESS,
    );
}

pub fn print_login_expired() {
    print_top_bar("KRUD", "device flow");
    draw_notice(
        "login expired",
        "The device code timed out before approval finished. Run `krud login` again.",
        DANGER,
    );
}

pub fn print_connecting() {
    print!(
        "  {} {}",
        "sync".with(TEAL).bold(),
        "connecting to krud cloud…".with(SMOKE)
    );
    std::io::stdout().flush().ok();
}

pub fn clear_connecting() {
    print!("\r\x1B[2K");
    std::io::stdout().flush().ok();
}

pub fn print_connect_failed(api_url: &str) {
    print_top_bar("KRUD", "offline");
    draw_notice(
        "service unreachable",
        &format!(
            "Krud could not reach the API endpoint at {}. Check connectivity or wait for the backend to recover.",
            api_url
        ),
        DANGER,
    );
}

pub fn print_not_logged_in() {
    print_top_bar("KRUD", "sign in");
    draw_notice(
        "authentication required",
        "Run `krud login` to connect this machine before opening a chat session.",
        WARNING,
    );
}

pub fn print_session_expired() {
    print_top_bar("KRUD", "session");
    draw_notice(
        "session expired",
        "Your stored session token was rejected. Run `krud login` again to refresh it.",
        WARNING,
    );
}

pub fn print_error(msg: &str) {
    draw_notice("error", msg, DANGER);
}

pub fn print_info(msg: &str) {
    println!("  {} {}", "info".with(TEAL).bold(), msg.with(SMOKE));
}

pub fn print_success(msg: &str) {
    println!("  {} {}", "done".with(SUCCESS).bold(), msg.with(CLOUD));
}

#[derive(Clone)]
pub enum FullscreenItem {
    Welcome(String),
    User(String),
    Assistant {
        model: String,
        text: String,
    },
    Action {
        command: String,
        rationale: String,
        risk: String,
        index: usize,
        total: usize,
    },
    Info(String),
    Success(String),
    Error(String),
}

struct ScreenLine {
    text: String,
    fg: Color,
    bold: bool,
    dim: bool,
}

impl ScreenLine {
    fn new(text: String, fg: Color) -> Self {
        Self {
            text,
            fg,
            bold: false,
            dim: false,
        }
    }

    fn bold(mut self) -> Self {
        self.bold = true;
        self
    }

    fn dim(mut self) -> Self {
        self.dim = true;
        self
    }

    fn blank() -> Self {
        Self::new(String::new(), CLOUD)
    }
}

pub struct FullscreenGuard;

impl FullscreenGuard {
    pub fn enter() -> io::Result<Self> {
        let mut stdout = io::stdout();
        enable_raw_mode()?;
        execute!(stdout, EnterAlternateScreen, Hide)?;
        Ok(Self)
    }
}

impl Drop for FullscreenGuard {
    fn drop(&mut self) {
        let _ = disable_raw_mode();
        let mut stdout = io::stdout();
        let _ = execute!(stdout, Show, LeaveAlternateScreen);
    }
}

pub fn render_fullscreen(
    email: Option<&str>,
    cwd: Option<&str>,
    items: &[FullscreenItem],
    input_label: &str,
    input_value: &str,
    scroll_from_bottom: usize,
    toy_frame: usize,
    toy_burst: u8,
) -> io::Result<()> {
    let (w, h) = terminal::size()?;
    let width = w as usize;
    let height = h as usize;

    let header = fullscreen_header_lines(email, cwd, width);
    let composer =
        fullscreen_composer_lines(cwd, input_label, input_value, width, toy_frame, toy_burst);

    let reserved = header.len() + composer.len();
    let chat_height = height.saturating_sub(reserved).max(1);

    let mut transcript = Vec::new();
    for (index, item) in items.iter().enumerate() {
        if index > 0 {
            let gap = item_gap(&items[index - 1], item);
            for _ in 0..gap {
                transcript.push(ScreenLine::blank());
            }
        }
        transcript.extend(fullscreen_item_lines(item, width));
    }

    let max_scroll = transcript.len().saturating_sub(chat_height);
    let hidden = scroll_from_bottom.min(max_scroll);
    let start = transcript
        .len()
        .saturating_sub(chat_height.saturating_add(hidden));
    let visible: Vec<ScreenLine> = transcript
        .into_iter()
        .skip(start)
        .take(chat_height)
        .collect();

    let mut stdout = io::stdout();
    execute!(stdout, MoveTo(0, 0))?;

    let mut row = 0u16;
    for line in header {
        write_screen_line(&mut stdout, row, &line, width, height)?;
        row += 1;
    }

    for line in visible {
        write_screen_line(&mut stdout, row, &line, width, height)?;
        row += 1;
    }

    while row < (height.saturating_sub(composer.len())) as u16 {
        write_screen_line(&mut stdout, row, &ScreenLine::blank(), width, height)?;
        row += 1;
    }

    for line in composer {
        write_screen_line(&mut stdout, row, &line, width, height)?;
        row += 1;
    }

    stdout.flush()?;
    Ok(())
}

fn write_screen_line(
    stdout: &mut io::Stdout,
    row: u16,
    line: &ScreenLine,
    width: usize,
    height: usize,
) -> io::Result<()> {
    let rendered = fit_line(line, width);
    queue!(
        stdout,
        MoveTo(0, row),
        SetBackgroundColor(background_for_row(row as usize, height)),
        SetForegroundColor(line.fg),
        SetAttribute(Attribute::Reset)
    )?;
    if line.bold {
        queue!(stdout, SetAttribute(Attribute::Bold))?;
    }
    if line.dim {
        queue!(stdout, SetAttribute(Attribute::Dim))?;
    }
    queue!(
        stdout,
        Print(rendered),
        ResetColor,
        SetAttribute(Attribute::Reset)
    )?;
    Ok(())
}

fn fit_line(line: &ScreenLine, width: usize) -> String {
    let mut out: String = line.text.chars().take(width).collect();
    let current = out.chars().count();
    if current < width {
        out.push_str(&" ".repeat(width - current));
    }
    out
}

fn background_for_row(row: usize, height: usize) -> Color {
    let _ = (row, height);
    Color::Rgb {
        r: 255,
        g: 255,
        b: 255,
    }
}

fn item_gap(previous: &FullscreenItem, current: &FullscreenItem) -> usize {
    if matches!(current, FullscreenItem::Action { .. })
        || matches!(
            current,
            FullscreenItem::Info(_) | FullscreenItem::Success(_) | FullscreenItem::Error(_)
        )
        || matches!(previous, FullscreenItem::Action { .. })
    {
        0
    } else {
        1
    }
}

fn fullscreen_header_lines(
    email: Option<&str>,
    cwd: Option<&str>,
    width: usize,
) -> Vec<ScreenLine> {
    let right = cwd
        .map(shorten_path)
        .or_else(|| email.map(|value| value.to_string()))
        .unwrap_or_else(|| "guest session".to_string());
    let title = "KRUD";
    let gap = width.saturating_sub(4 + title.len() + right.len());
    vec![
        ScreenLine::new(format!("  {}{}{}", title, " ".repeat(gap), right), CLOUD).bold(),
        ScreenLine::new(
            format!("  {}", "─".repeat(width.saturating_sub(4))),
            TEAL_SOFT,
        )
        .dim(),
    ]
}

fn fullscreen_composer_lines(
    cwd: Option<&str>,
    input_label: &str,
    input_value: &str,
    width: usize,
    toy_frame: usize,
    toy_burst: u8,
) -> Vec<ScreenLine> {
    let workspace = cwd
        .map(shorten_path)
        .unwrap_or_else(|| "unknown workspace".to_string());
    let frame_width = width.saturating_sub(6);
    let inner = frame_width.saturating_sub(4);
    let prompt = format!("{input_label} {input_value}");
    let visible_prompt = if prompt.chars().count() > inner {
        let keep = inner.saturating_sub(1);
        let chars: Vec<char> = prompt.chars().collect();
        chars[chars.len().saturating_sub(keep)..]
            .iter()
            .collect::<String>()
    } else {
        prompt
    };
    let sigil = prompt_sigil(toy_frame, toy_burst);
    let prompt_text = format!("{sigil}  {visible_prompt}");
    let prompt_width = 3 + visible_prompt.chars().count();
    vec![
        ScreenLine::new(
            format!(
                "  workspace {}  ·  PgUp/PgDn scroll  ·  /help /new /status /clear  ·  exit",
                workspace
            ),
            SMOKE,
        )
        .dim(),
        ScreenLine::new(format!("  ╭{}╮", "─".repeat(frame_width)), SMOKE),
        ScreenLine::new(
            format!(
                "  │ {}{} │",
                prompt_text,
                " ".repeat(inner.saturating_sub(prompt_width))
            ),
            CLOUD,
        ),
        ScreenLine::new(format!("  ╰{}╯", "─".repeat(frame_width)), SMOKE),
    ]
}

fn prompt_sigil(frame: usize, burst: u8) -> String {
    if burst > 0 {
        return "◈".to_string();
    }

    match frame % 4 {
        0 => "◌",
        1 => "◍",
        2 => "◉",
        _ => "◍",
    }
    .to_string()
}

fn fullscreen_item_lines(item: &FullscreenItem, width: usize) -> Vec<ScreenLine> {
    match item {
        FullscreenItem::Welcome(text) => {
            plain_left_block("krud", text, width.saturating_sub(2), true)
        }
        FullscreenItem::User(text) => plain_right_block("you", text, width.saturating_sub(2)),
        FullscreenItem::Assistant { model, text } => plain_left_block(
            &format!("krud · {}", model),
            text,
            width.saturating_sub(2),
            false,
        ),
        FullscreenItem::Action {
            command,
            rationale,
            risk,
            index,
            total,
        } => action_panel(
            command,
            rationale,
            risk,
            *index,
            *total,
            width.saturating_sub(2),
        ),
        FullscreenItem::Info(text) => note_block("info", text, width.saturating_sub(2), SMOKE),
        FullscreenItem::Success(text) => note_block("done", text, width.saturating_sub(2), SUCCESS),
        FullscreenItem::Error(text) => note_block("error", text, width.saturating_sub(2), DANGER),
    }
}

fn plain_left_block(label: &str, text: &str, width: usize, welcome: bool) -> Vec<ScreenLine> {
    let block_width = if welcome {
        width.min(68).max(34)
    } else {
        width.min(88).max(42)
    };
    let mut lines = vec![ScreenLine::new(format!("   {}", label), COPPER).bold()];
    for line in wrap(text, block_width) {
        lines.push(ScreenLine::new(format!("   {}", line), CLOUD));
    }
    lines
}

fn plain_right_block(_label: &str, text: &str, width: usize) -> Vec<ScreenLine> {
    let block_width = (width * 48 / 100).min(56).max(20);
    let mut lines = Vec::new();
    for line in wrap(text, block_width) {
        let indent = width.saturating_sub(line.chars().count()).saturating_sub(4);
        lines.push(ScreenLine::new(
            format!("{}{}", " ".repeat(indent), line),
            CLOUD,
        ));
    }
    lines
}

fn action_panel(
    command: &str,
    rationale: &str,
    risk: &str,
    index: usize,
    total: usize,
    width: usize,
) -> Vec<ScreenLine> {
    let accent = risk_color(risk);
    let bw = width.saturating_sub(10).min(98).max(46);
    let inner = bw.saturating_sub(4);
    let mut lines = vec![ScreenLine::new(
        format!("   proposed action {} of {}", index + 1, total),
        accent,
    )
    .bold()];
    lines.push(ScreenLine::new(format!("   ╭{}╮", "─".repeat(bw)), accent));
    let command_lines = wrap(&format!("$ {}", command), inner);
    for line in command_lines {
        let len = line.chars().count();
        lines.push(ScreenLine::new(
            format!("   │ {}{} │", line, " ".repeat(inner.saturating_sub(len))),
            CLOUD,
        ));
    }
    for line in wrap(rationale, inner) {
        let len = line.chars().count();
        lines.push(ScreenLine::new(
            format!("   │ {}{} │", line, " ".repeat(inner.saturating_sub(len))),
            SMOKE,
        ));
    }
    let action_text = "[r] run now    [q] queue for daemon    [s] skip";
    lines.push(ScreenLine::new(
        format!(
            "   │ {}{} │",
            action_text,
            " ".repeat(inner.saturating_sub(action_text.chars().count()))
        ),
        COPPER_SOFT,
    ));
    lines.push(ScreenLine::new(format!("   ╰{}╯", "─".repeat(bw)), accent));
    lines
}

fn note_block(label: &str, text: &str, width: usize, color: Color) -> Vec<ScreenLine> {
    let mut lines = Vec::new();
    let wrap_width = width.saturating_sub(label.len() + 6).max(14);
    for line in wrap(text, wrap_width) {
        let item = ScreenLine::new(format!("   {} {}", label, line), color);
        if color == DANGER || color == WARNING {
            lines.push(item.bold());
        } else {
            lines.push(item.dim());
        }
    }
    lines
}
