//! Terminal chat UI for krud — clean scrolling chat with a single mascot.
//!
//! Layout overview:
//!
//!  ╭──────────────────────────────────────────────────────────────────╮
//!  │  ◆ krud AI                            AI terminal agent · user@ │  ← header (printed once)
//!  ╰──────────────────────────────────────────────────────────────────╯
//!
//!  [chat messages scroll here naturally as the terminal scrolls up]
//!
//!                                ╭──────────────────────────────────╮
//!                                │  your message                    │  ← user bubble (right)
//!                                ╰─────────────────── You ──────────╯
//!
//!  ◆ Thinking…                                                          ← thinking line (erased)
//!    OR
//!  ◆ krud AI  ·  gpt-4o-mini  ·  8↑ 42↓                               ← assistant header
//!  ─────────────────────────────────────────────────────────────────────
//!  I'll help you find large files...
//!
//!  ╭─ Command 1/1 ──────────────────────────── ⚠ medium ─╮
//!  │  $ find . -type f -size +10M                         │
//!  ├──────────────────────────────────────────────────────┤
//!  │  [r] Run now   [q] Queue   [s] Skip                  │
//!  ╰──────────────────────────────────────────────────────╯
//!
//!  [single static robot, drawn once above each input box]
//!
//!  ╭─ ~/Projects/krud ──────────────────────────────────────
//!  │  › _

use crossterm::style::Stylize;
use crossterm::terminal;
use std::io::Write;

// ─── sizing ─────────────────────────────────────────────────────────────────

pub fn term_width() -> usize {
    terminal::size().map(|(w, _)| w as usize).unwrap_or(80)
}

/// Full-width box (minus 4 chars for the 2-space indent + │ + │).
pub fn box_width() -> usize {
    term_width().saturating_sub(4).min(92).max(56)
}

fn inner_width(bw: usize) -> usize {
    bw.saturating_sub(4)
}

// ─── word-wrap ──────────────────────────────────────────────────────────────

pub fn wrap(text: &str, width: usize) -> Vec<String> {
    if width == 0 {
        return vec![text.to_string()];
    }
    let mut lines: Vec<String> = Vec::new();
    for para in text.split('\n') {
        if para.trim().is_empty() {
            lines.push(String::new());
            continue;
        }
        let mut cur = String::new();
        for word in para.split_whitespace() {
            let wlen = word.chars().count();
            let clen = cur.chars().count();
            if cur.is_empty() {
                cur.push_str(word);
            } else if clen + 1 + wlen <= width {
                cur.push(' ');
                cur.push_str(word);
            } else {
                lines.push(std::mem::take(&mut cur));
                cur.push_str(word);
            }
        }
        if !cur.is_empty() {
            lines.push(cur);
        }
    }
    lines
}

// ─── low-level box drawing ──────────────────────────────────────────────────

fn pline(colored: impl std::fmt::Display, raw_len: usize, bw: usize) {
    let inner = inner_width(bw);
    let pad = inner.saturating_sub(raw_len);
    println!("  │  {}{}  │", colored, " ".repeat(pad));
}

fn pindented(colored: impl std::fmt::Display, raw_len: usize, bw: usize) {
    let avail = bw.saturating_sub(6);
    let pad = avail.saturating_sub(raw_len);
    println!("  │    {}{}  │", colored, " ".repeat(pad));
}

// ─── header toolbar ─────────────────────────────────────────────────────────

pub fn print_header(email: Option<&str>) {
    let bw = box_width();
    let iw = inner_width(bw);

    let brand_raw = "◆ krud AI";
    let brand_len = brand_raw.chars().count();

    let right_raw = match email {
        Some(e) => format!("AI terminal agent  ·  {}", e),
        None => "AI terminal agent".to_string(),
    };
    let right_len = right_raw.chars().count();
    let gap = iw.saturating_sub(brand_len + right_len);

    println!();
    println!("  ╭{}╮", "─".repeat(bw));
    println!(
        "  │  {}{}{}  │",
        brand_raw.cyan().bold(),
        " ".repeat(gap),
        right_raw.dark_grey()
    );
    println!("  ╰{}╯", "─".repeat(bw));
    println!();
}

// ─── welcome hint ───────────────────────────────────────────────────────────

pub fn print_welcome() {
    println!("  {} Type your request and press Enter.  Type {} to quit.", "◆".dark_grey(), "exit".white());
    println!();
}

// ─── user bubble (right-aligned) ────────────────────────────────────────────

pub fn print_user_message(text: &str) {
    let tw = term_width();
    let bw = (tw * 68 / 100).min(72).max(38);
    let iw = bw.saturating_sub(4);
    let left = tw.saturating_sub(bw + 4).max(2);
    let indent = " ".repeat(left);

    let lines = wrap(text, iw);

    println!("{}╭{}╮", indent, "─".repeat(bw));
    for line in &lines {
        let raw_len = line.chars().count();
        let pad = iw.saturating_sub(raw_len);
        println!("{}│  {}{}  │", indent, line, " ".repeat(pad));
    }

    let you = " You ";
    let you_len = you.chars().count();
    let total_dashes = bw.saturating_sub(you_len);
    let ld = 4.min(total_dashes);
    let rd = total_dashes - ld;
    println!(
        "{}╰{}{}{}╯",
        indent,
        "─".repeat(ld),
        you.white().bold(),
        "─".repeat(rd)
    );
    println!();
}

// ─── thinking indicator ──────────────────────────────────────────────────────
//
//  Printed inline (no newline) so we can erase it cleanly when the response
//  arrives.  Uses \r + ANSI CSI 2K (erase entire line) to clear in-place
//  without scrolling or redrawing anything else on screen.

pub fn print_thinking() {
    print!("  {} Thinking…", "◆".cyan().bold());
    std::io::stdout().flush().ok();
}

/// Erase the thinking line so the response can be printed in its place.
pub fn clear_thinking() {
    print!("\r\x1B[2K");
    std::io::stdout().flush().ok();
}

// ─── assistant message (left, no box) ───────────────────────────────────────

pub fn print_assistant_message(
    text: &str,
    model: &str,
    prompt_tokens: i64,
    completion_tokens: i64,
) {
    let bw = box_width();
    let iw = inner_width(bw);

    let brand_raw = "◆ krud AI";
    let brand_len = brand_raw.chars().count();
    let sep = "  ·  ";
    let sep_len = sep.chars().count();
    let model_len = model.chars().count();
    let tok_raw = format!("{}↑  {}↓", prompt_tokens, completion_tokens);
    let tok_len = tok_raw.chars().count();

    let total_header = brand_len + sep_len + model_len + sep_len + tok_len;
    let gap = (bw + 2).saturating_sub(total_header);

    println!(
        "  {}{}{}{}{}{}",
        brand_raw.cyan().bold(),
        sep.dark_grey(),
        model.dark_grey(),
        sep.dark_grey(),
        tok_raw.dark_grey(),
        " ".repeat(gap)
    );
    println!("  {}", "─".repeat(bw + 2));

    let lines = wrap(text, iw + 2);
    for line in &lines {
        if line.is_empty() {
            println!();
        } else {
            println!("  {}", line);
        }
    }
    println!();
}

// ─── command proposal card ───────────────────────────────────────────────────

fn risk_color(risk: &str) -> crossterm::style::Color {
    match risk.to_lowercase().as_str() {
        "low" | "safe" => crossterm::style::Color::Green,
        "high" | "critical" | "dangerous" => crossterm::style::Color::Red,
        _ => crossterm::style::Color::Yellow,
    }
}

pub fn print_command_proposal(
    command: &str,
    rationale: &str,
    risk: &str,
    index: usize,
    total: usize,
) {
    let bw = box_width();
    let iw = inner_width(bw);

    let label_raw = format!("Command {}/{}", index + 1, total);
    let label_len = label_raw.chars().count();
    let risk_raw = format!("⚠ {}", risk);
    let risk_len = risk_raw.chars().count();
    let rc = risk_color(risk);

    let inner_header = bw.saturating_sub(2 + label_len + 1 + risk_len + 2);
    println!(
        "  ╭─ {} {}─ {} ─╮",
        label_raw.bold(),
        "─".repeat(inner_header),
        risk_raw.with(rc).bold()
    );

    let cmd_max = iw.saturating_sub(2);
    let cmd_display: String = if command.chars().count() > cmd_max {
        command.chars().take(cmd_max.saturating_sub(1)).collect::<String>() + "…"
    } else {
        command.to_string()
    };
    let cmd_raw_len = 2 + cmd_display.chars().count();

    println!("  │{}│", " ".repeat(bw));
    pline(
        format!("{} {}", "$".dark_grey(), cmd_display.yellow().bold()),
        cmd_raw_len,
        bw,
    );
    println!("  │{}│", " ".repeat(bw));

    let rat_lines = wrap(rationale, iw.saturating_sub(2));
    for line in &rat_lines {
        pindented(line.as_str().dark_grey(), line.chars().count(), bw);
    }

    println!("  ├{}┤", "─".repeat(bw));
    let actions_raw_len = "[r] Run now   [q] Queue   [s] Skip".chars().count();
    pline(
        format!(
            "{} Run now   {} Queue   {} Skip",
            "[r]".green().bold(),
            "[q]".blue().bold(),
            "[s]".dark_grey()
        ),
        actions_raw_len,
        bw,
    );
    println!("  ╰{}╯", "─".repeat(bw));
    println!();
}

// ─── input area — single static robot + open input box ───────────────────────
//
//  The robot is drawn ONCE per prompt, always in the Idle pose (frame 0).
//  No background animation thread — eliminates all glitches.

pub fn print_input_area(cwd: Option<&str>) {
    use crate::rabbit::{self, RabbitState};
    // Single static robot — always frame 0, always Idle pose.
    rabbit::print_rabbit(RabbitState::Idle, 0);

    let bw = box_width();

    let cwd_short = cwd.map(|dir| {
        let parts: Vec<&str> = dir.trim_end_matches('/').split('/').collect();
        if parts.len() > 2 {
            format!("…/{}/{}", parts[parts.len() - 2], parts[parts.len() - 1])
        } else {
            dir.to_string()
        }
    });

    if let Some(ref short) = cwd_short {
        let short_len = short.chars().count();
        let dashes = bw.saturating_sub(3 + short_len + 1);
        println!(
            "  ╭─ {} {}",
            short.as_str().dark_grey(),
            "─".repeat(dashes)
        );
    } else {
        println!("  ╭{}", "─".repeat(bw + 1));
    }
}

/// Print the `›` prompt — cursor sits here, no newline.
pub fn print_prompt() {
    print!("  │  {} ", "›".cyan().bold());
    std::io::stdout().flush().ok();
}

/// Print the decision prompt (inline, after command proposal).
pub fn print_decision_prompt() {
    print!("  │  {} ", "›".dark_grey());
    std::io::stdout().flush().ok();
}

// ─── error / info ────────────────────────────────────────────────────────────

pub fn print_error(msg: &str) {
    let bw = box_width();
    let iw = inner_width(bw);
    let lines = wrap(msg, iw);
    println!("  ╭{}╮", "─".repeat(bw));
    pline("Error".red().bold(), 5, bw);
    println!("  ├{}┤", "─".repeat(bw));
    for line in &lines {
        pline(line.as_str().red(), line.chars().count(), bw);
    }
    println!("  ╰{}╯", "─".repeat(bw));
    println!();
}

pub fn print_info(msg: &str) {
    println!("  {} {}", "◆".cyan(), msg.dark_grey());
}

// ─── token budget bar ────────────────────────────────────────────────────────
//
//  ◆ 12,400 / 40,000 tokens  ▓▓▓▓▓▓░░░░░░░░░░░░░░  31%  resets 04:22

pub fn print_token_budget(used: i64, limit: i64, resets_at: &str) {
    if limit <= 0 {
        return;
    }

    let pct = ((used as f64 / limit as f64) * 100.0).min(100.0) as u64;

    let bar_width: usize = 20;
    let filled = ((pct as usize) * bar_width / 100).min(bar_width);
    let empty = bar_width - filled;
    let bar = format!("{}{}", "▓".repeat(filled), "░".repeat(empty));

    let coloured_bar = if pct < 70 {
        bar.green().to_string()
    } else if pct < 90 {
        bar.yellow().to_string()
    } else {
        bar.red().to_string()
    };

    let reset_hint = parse_reset_hint(resets_at);

    let bw = box_width();
    let label = format!(
        "{} / {} tokens  {}  {}%  resets {}",
        fmt_num(used),
        fmt_num(limit),
        coloured_bar,
        pct,
        reset_hint,
    );

    let max_len = bw.saturating_sub(6);
    let display: String = if label.chars().count() > max_len {
        let mut s: String = label.chars().take(max_len).collect();
        s.push('…');
        s
    } else {
        label
    };

    println!("  {} {}", "◆".cyan(), display.dark_grey());
    println!();
}

fn fmt_num(n: i64) -> String {
    let s = n.to_string();
    let mut result = String::new();
    for (i, ch) in s.chars().rev().enumerate() {
        if i > 0 && i % 3 == 0 {
            result.push(',');
        }
        result.push(ch);
    }
    result.chars().rev().collect()
}

fn parse_reset_hint(resets_at: &str) -> String {
    if let Some(remaining_secs) = remaining_seconds(resets_at) {
        if remaining_secs <= 0 {
            return "now".to_string();
        }
        let h = remaining_secs / 3600;
        let m = (remaining_secs % 3600) / 60;
        if h > 0 {
            return format!("{h}h {m:02}m");
        }
        return format!("{m}m");
    }
    resets_at.get(..16).unwrap_or(resets_at).to_string()
}

fn remaining_seconds(iso: &str) -> Option<i64> {
    let s = iso.trim();
    let dt_part = s.split('+').next().unwrap_or(s).trim_end_matches('Z');
    let parts: Vec<&str> = dt_part.splitn(2, 'T').collect();
    if parts.len() != 2 {
        return None;
    }
    let date_parts: Vec<u64> = parts[0].split('-').filter_map(|p| p.parse().ok()).collect();
    let time_parts: Vec<u64> = parts[1]
        .split(':')
        .filter_map(|p| p.parse::<f64>().map(|f| f as u64).ok())
        .collect();
    if date_parts.len() != 3 || time_parts.len() < 2 {
        return None;
    }
    let y = date_parts[0];
    let mo = date_parts[1];
    let d = date_parts[2];
    let h = time_parts[0];
    let mi = time_parts.get(1).copied().unwrap_or(0);
    let sec = time_parts.get(2).copied().unwrap_or(0);

    let leap_years = (1970..y)
        .filter(|&yr| yr % 4 == 0 && (yr % 100 != 0 || yr % 400 == 0))
        .count() as u64;
    let days_in_year = y.saturating_sub(1970) * 365 + leap_years;
    let month_days: [u64; 12] = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    let days_in_month: u64 =
        month_days[..((mo as usize).saturating_sub(1)).min(12)].iter().sum();
    let total_days = days_in_year + days_in_month + d.saturating_sub(1);
    let target_unix = total_days * 86400 + h * 3600 + mi * 60 + sec;

    use std::time::{SystemTime, UNIX_EPOCH};
    let now_unix = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()?
        .as_secs();

    Some(target_unix as i64 - now_unix as i64)
}
