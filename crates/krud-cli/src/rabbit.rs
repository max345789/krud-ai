//! Pixel-art block-character rabbit mascot for krud.
//!
//! Styled after the Claude Code robot aesthetic:
//! blocky Unicode block characters (██▀▄) instead of ASCII art.
//!
//!  Idle     — sits, ears upright
//!  Typing   — leans in, one wide eye
//!  Thinking — ？eyes, animated dots
//!  Running  — leans forward, motion lines
//!  Success  — arms up, ^^ eyes
//!  Error    — ✕ eyes, slumped
//!  Waiting  — holds sign

use crossterm::style::Stylize;
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc,
};

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum RabbitState {
    Idle,
    #[allow(dead_code)]
    Typing,
    Thinking,
    Running,
    Success,
    Error,
    Waiting,
}

/// Two alternating frames per state. Each frame is exactly 9 lines.
fn frames(state: RabbitState) -> [[&'static str; 9]; 2] {
    match state {
        // ── idle ──────────────────────────────────────────────────────────────
        RabbitState::Idle => [
            [
                " ▄██▄  ▄██▄ ",
                " █  █  █  █ ",
                "▄██████████▄",
                "█  ██    ██ █",
                "█           █",
                "█   ─────   █",
                "▀███████████▀",
                "  ███    ███ ",
                " ▀▀▀     ▀▀▀ ",
            ],
            [
                " ▄██▄  ▄██▄ ",
                " █  █  █  █ ",
                "▄██████████▄",
                "█  ██    ██ █",
                "█     ▲     █",
                "█   ─────   █",
                "▀███████████▀",
                "  ███    ███ ",
                " ▀▀▀     ▀▀▀ ",
            ],
        ],
        // ── typing ────────────────────────────────────────────────────────────
        RabbitState::Typing => [
            [
                " ▄██▄  ▄██▄ ",
                " █  █  █  █ ",
                "▄██████████▄",
                "█  ██    ██ █",
                "█     ▲     █",
                "█   ─────   █",
                "▀███████████▀",
                "  ███    ███ ",
                " ▀▀▀     ▀▀▀ ",
            ],
            [
                " ▄██▄  ▄██▄ ",
                " █  █  █  █ ",
                "▄██████████▄",
                "█  ██    ██▌█",
                "█     ▲     █",
                "█   ─────   █",
                "▀███████████▀",
                "  ███    ███ ",
                " ▀▀▀     ▀▀▀ ",
            ],
        ],
        // ── thinking ──────────────────────────────────────────────────────────
        RabbitState::Thinking => [
            [
                " ▄██▄  ▄██▄ ",
                " █  █  █  █ ",
                "▄██████████▄",
                "█  ？   ？  █",
                "█           █",
                "█   ─────   █",
                "▀███████████▀",
                "  ███    ███ ",
                " ▀▀▀  ●  ▀▀▀ ",
            ],
            [
                " ▄██▄  ▄██▄ ",
                " █  █  █  █ ",
                "▄██████████▄",
                "█  ？   ？  █",
                "█     ▲     █",
                "█   ─────   █",
                "▀███████████▀",
                "  ███    ███ ",
                " ▀▀▀ ●●● ▀▀▀ ",
            ],
        ],
        // ── running ───────────────────────────────────────────────────────────
        RabbitState::Running => [
            [
                "  ▄██▄▄██▄  ",
                "  █  ██  █  ",
                " ▄█████████▄",
                " █  ▶▶   ▶▶ █",
                " █     ▲    █",
                " █  ──────  █",
                " ▀█████████▀",
                "≋≋  ███  ███ ",
                "    ▀▀▀  ▀▀▀ ",
            ],
            [
                " ▄██▄▄██▄   ",
                " █  ██  █   ",
                "▄█████████▄ ",
                "█  ▶▶   ▶▶ █ ",
                "█     ▲    █ ",
                "█  ──────  █ ",
                "▀█████████▀  ",
                "  ███  ███ ≋≋",
                "  ▀▀▀  ▀▀▀   ",
            ],
        ],
        // ── success ───────────────────────────────────────────────────────────
        RabbitState::Success => [
            [
                " ▄██▄  ▄██▄ ",
                " █  █  █  █ ",
                "▄██████████▄",
                "█  ^^    ^^ █",
                "█     ▲     █",
                "█   ╰───╯   █",
                "▀███████████▀",
                "▌ ███    ███ ▐",
                " ▀▀▀     ▀▀▀ ",
            ],
            [
                "▗▄██▄▖▗▄██▄▖",
                "▐█  █▌▐█  █▌",
                "▄██████████▄",
                "█  ^^    ^^ █",
                "█     ▲     █",
                "█   ╰───╯   █",
                "▀███████████▀",
                "▌ ███    ███ ▐",
                " ▀▀▀     ▀▀▀ ",
            ],
        ],
        // ── error ─────────────────────────────────────────────────────────────
        RabbitState::Error => [
            [
                " ▄██▄  ▄██▄ ",
                " █  █  █  █ ",
                "▄██████████▄",
                "█  ✕▌   ▌✕  █",
                "█           █",
                "█   ─────   █",
                "▀███████████▀",
                "   ███████   ",
                "  ▀▀▀▀▀▀▀▀▀  ",
            ],
            [
                " ▄██▄  ▄██▄ ",
                " █  ▼  ▼  █ ",
                "▄██████████▄",
                "█  ✕▌   ▌✕  █",
                "█           █",
                "█   ─────   █",
                "▀███████████▀",
                "   ███████   ",
                "  ▀▀▀▀▀▀▀▀▀  ",
            ],
        ],
        // ── waiting ───────────────────────────────────────────────────────────
        RabbitState::Waiting => [
            [
                " ▄██▄  ▄██▄ ",
                " █  █  █  █ ",
                "▄██████████▄",
                "█  ██    ██ █",
                "█     ▲     █",
                "█   ─────   █",
                "▀███████████▀",
                "  ███▐??▌███ ",
                " ▀▀▀▀▀▀▀▀▀▀▀ ",
            ],
            [
                " ▄██▄  ▄██▄ ",
                " █  █  █  █ ",
                "▄██████████▄",
                "█  ◉    ◉   █",
                "█     ▲     █",
                "█   ─────   █",
                "▀███████████▀",
                "  ███▐??▌███ ",
                " ▀▀▀▀▀▀▀▀▀▀▀ ",
            ],
        ],
    }
}

fn label(state: RabbitState) -> &'static str {
    match state {
        RabbitState::Idle => "ready",
        RabbitState::Typing => "listening…",
        RabbitState::Thinking => "thinking…",
        RabbitState::Running => "running…",
        RabbitState::Success => "done! ✓",
        RabbitState::Error => "uh oh…",
        RabbitState::Waiting => "awaiting your decision",
    }
}

fn label_color(state: RabbitState) -> crossterm::style::Color {
    match state {
        RabbitState::Success => crossterm::style::Color::Green,
        RabbitState::Error => crossterm::style::Color::Red,
        RabbitState::Thinking | RabbitState::Running => crossterm::style::Color::Yellow,
        RabbitState::Waiting => crossterm::style::Color::Cyan,
        _ => crossterm::style::Color::DarkGrey,
    }
}

/// Total rendered lines: blank + 9 sprite + label + blank = 12
const FRAME_LINES: u16 = 12;

/// Print a single static frame.
pub fn print_rabbit(state: RabbitState, frame_index: usize) {
    let all_frames = frames(state);
    let frame = &all_frames[frame_index % 2];
    let lbl = label(state);
    let color = label_color(state);

    println!();
    for line in frame {
        println!("  {}", line.dark_grey());
    }
    println!("  · {} ·", lbl.with(color));
    println!();
}

// ─── animated handle ────────────────────────────────────────────────────────

pub struct AnimationHandle {
    stop: Arc<AtomicBool>,
    thread: Option<std::thread::JoinHandle<()>>,
}

impl Drop for AnimationHandle {
    fn drop(&mut self) {
        self.stop.store(true, Ordering::SeqCst);
        if let Some(t) = self.thread.take() {
            t.join().ok();
        }
    }
}

pub fn start_animation(state: RabbitState) -> AnimationHandle {
    let stop = Arc::new(AtomicBool::new(false));
    let stop_clone = stop.clone();

    let all_frames = frames(state);
    let lbl = label(state);
    let color = label_color(state);

    let thread = std::thread::spawn(move || {
        use crossterm::{cursor, execute, terminal};
        use std::io::{stdout, Write};

        let _ = execute!(stdout(), cursor::Hide);
        let mut frame_index: usize = 0;

        loop {
            let frame = &all_frames[frame_index % 2];

            println!();
            for line in frame {
                println!("  {}", line.dark_grey());
            }
            println!("  · {} ·", lbl.with(color));
            println!();
            let _ = stdout().flush();

            std::thread::sleep(std::time::Duration::from_millis(500));

            let _ = execute!(
                stdout(),
                cursor::MoveUp(FRAME_LINES),
                terminal::Clear(terminal::ClearType::FromCursorDown)
            );

            if stop_clone.load(Ordering::SeqCst) {
                break;
            }

            frame_index += 1;
        }

        let _ = execute!(stdout(), cursor::Show);
    });

    AnimationHandle {
        stop,
        thread: Some(thread),
    }
}
