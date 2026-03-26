//! Animated purple rabbit mascot for krud.
//!
//! Design goal: same vibe as Claude Code's orange pixel-art robot, but as a
//! full-body rabbit in purple.  All frames are 9 lines × 14 visual columns
//! so in-place overwrite never leaves stray characters.
//!
//! Animation states
//! ────────────────
//!  Idle     — sits, ears upright, gentle sway (2 frames)
//!  Thinking — one arm raised to chin, eyes shift (2 frames)
//!  Running  — legs pumping, leaning forward (2 frames)
//!  Success  — both arms raised, star eyes (2 frames)
//!  Error    — ears drooped, sad expression (1 frame)

use crossterm::style::{Color, Stylize};
use std::io::Write;
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc,
};
use std::thread;
use std::time::Duration;

// ── colours ─────────────────────────────────────────────────────────────────

const PURPLE: Color = Color::Rgb { r: 168, g: 85, b: 247 };
const PURPLE_LIGHT: Color = Color::Rgb { r: 216, g: 160, b: 252 };
const WHITE: Color = Color::White;

// ── frame data ───────────────────────────────────────────────────────────────
//
// Each frame is exactly 9 strings, each exactly 14 printable columns wide.
// Use trailing spaces to pad shorter rows.

pub const FRAME_HEIGHT: u16 = 9;

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum RabbitState {
    Idle,
    Thinking,
    Running,
    Success,
    Error,
}

type Frame = [&'static str; 9];

fn frames(state: RabbitState) -> [Frame; 2] {
    match state {
        // ── idle: gentle ear/arm sway ─────────────────────────────────────
        RabbitState::Idle => [
            [
                "   ▐▌   ▐▌   ",
                "   ██   ██   ",
                "  ▄████████▄ ",
                "  █ ●     ● █",
                "  █   ω     █",
                "  ▀████████▀ ",
                "  ▐████████▌ ",
                "  ██       ██",
                "  ▀▀       ▀▀",
            ],
            [
                "   ▐▌   ▐▌   ",
                "   ██   ██   ",
                "  ▄████████▄ ",
                "  █ ●     ● █",
                "  █   ‿     █",  // tiny smile change
                "  ▀████████▀ ",
                " ▗▐████████▌▖",  // arm hints
                "  ██       ██",
                "  ▀▀       ▀▀",
            ],
        ],
        // ── thinking: right arm raised, eyes shift ────────────────────────
        RabbitState::Thinking => [
            [
                "   ▐▌   ▐▌   ",
                "   ██   ██   ",
                "  ▄████████▄ ",
                "  █ ●     ◑ █",  // one eye looking up
                "  █   ─     █",  // neutral mouth
                "  ▀████████▀ ",
                "  ▐███████╱  ",  // right arm raised
                "  ██       ██",
                "  ▀▀       ▀▀",
            ],
            [
                "   ▐▌   ▐▌   ",
                "   ██   ██   ",
                "  ▄████████▄ ",
                "  █ ●     ◑ █",
                "  █   ─     █",
                "  ▀████████▀ ",
                " ▗▐███████╱  ",  // arm slightly different
                "  ██       ██",
                "  ▀▀       ▀▀",
            ],
        ],
        // ── running: leaning forward, legs pumping ────────────────────────
        RabbitState::Running => [
            [
                "  ▐▌  ▐▌     ",  // ears leaning
                "  ██  ██     ",
                " ▄████████▄  ",  // body shifted right (lean)
                " █ ●    ● █  ",
                " █   ─    █  ",
                " ▀████████▀  ",
                " ▗▐███████▌  ",  // arms pumping
                "  ██     ▐▌  ",  // asymmetric legs (stride)
                "  ▀       ▀  ",
            ],
            [
                "  ▐▌  ▐▌     ",
                "  ██  ██     ",
                " ▄████████▄  ",
                " █ ●    ● █  ",
                " █   ─    █  ",
                " ▀████████▀  ",
                " ▗▌████████▖ ",  // other arm forward
                "  ▐▌     ██  ",  // opposite stride
                "   ▀      ▀  ",
            ],
        ],
        // ── success: both arms raised, star eyes ─────────────────────────
        RabbitState::Success => [
            [
                "  ▐▌   ▐▌    ",
                "  ██   ██    ",
                " ▄████████▄  ",
                " █ ★     ★ █ ",  // star eyes
                " █   ▲      █",  // big smile
                " ▀████████▀  ",
                "╱ ▐███████▌ ╲",  // arms raised wide
                "  ██       ██",
                "  ▀▀       ▀▀",
            ],
            [
                " ✦▐▌   ▐▌✦   ",  // sparkles
                "  ██   ██    ",
                " ▄████████▄  ",
                " █ ★     ★ █ ",
                " █   ▲      █",
                " ▀████████▀  ",
                "╱  ▐██████▌ ╲",
                "  ██       ██",
                "  ▀▀       ▀▀",
            ],
        ],
        // ── error: ears drooped, sad face ────────────────────────────────
        RabbitState::Error => [
            [
                "  ▖▌   ▐▗    ",  // drooped ears
                "  ▀█   █▀    ",
                " ▄████████▄  ",
                " █ ×     × █ ",  // × eyes
                " █   ▽      █",  // sad mouth
                " ▀████████▀  ",
                "  ▐████████▌ ",
                "  ██       ██",
                "  ▀▀       ▀▀",
            ],
            [
                "  ▖▌   ▐▗    ",
                "  ▀█   █▀    ",
                " ▄████████▄  ",
                " █ ×     × █ ",
                " █   ▽      █",
                " ▀████████▀  ",
                "  ▐████████▌ ",
                "  ██       ██",
                "  ▀▀       ▀▀",
            ],
        ],
    }
}

// ── print one frame ──────────────────────────────────────────────────────────

pub fn print_rabbit(state: RabbitState, frame: usize) {
    let f = frames(state);
    let lines = &f[frame % 2];
    let mut stdout = std::io::stdout();

    for (i, line) in lines.iter().enumerate() {
        // Eyes row (row 3) gets lighter accent colour for contrast
        if i == 3 {
            // print body in purple, eye chars in white
            print!("  ");
            for ch in line.trim_end().chars() {
                if ch == '●' || ch == '◑' || ch == '★' || ch == '×' {
                    print!("{}", ch.to_string().with(WHITE).bold());
                } else if ch == 'ω' || ch == '‿' || ch == '▲' || ch == '▽' || ch == '─' {
                    print!("{}", ch.to_string().with(PURPLE_LIGHT));
                } else {
                    print!("{}", ch.to_string().with(PURPLE));
                }
            }
            println!();
        } else if i == 4 {
            // mouth row — light purple
            print!("  ");
            for ch in line.trim_end().chars() {
                if ch == 'ω' || ch == '‿' || ch == '▲' || ch == '▽' || ch == '─' {
                    print!("{}", ch.to_string().with(PURPLE_LIGHT).bold());
                } else {
                    print!("{}", ch.to_string().with(PURPLE));
                }
            }
            println!();
        } else if i == 0 || i == 1 {
            // ears — slightly lighter
            println!("  {}", line.with(PURPLE_LIGHT));
        } else {
            println!("  {}", line.with(PURPLE));
        }
    }
    stdout.flush().ok();
}

// ── in-place animation ───────────────────────────────────────────────────────
//
// The animation thread loops:
//   1. print frame (FRAME_HEIGHT lines)
//   2. sleep
//   3. move cursor back up FRAME_HEIGHT lines (in-place overwrite next iter)
//
// On drop we set the stop flag, wait for the thread to finish its current
// iteration (cursor ends at TOP of rabbit area), then clear all lines.

pub struct AnimationHandle {
    stop: Arc<AtomicBool>,
    thread: Option<thread::JoinHandle<()>>,
}

impl Drop for AnimationHandle {
    fn drop(&mut self) {
        self.stop.store(true, Ordering::Relaxed);
        if let Some(t) = self.thread.take() {
            let _ = t.join();
        }
        // Cursor is at the TOP of the rabbit area after thread exits.
        // Clear every line going down, then return cursor to top.
        let mut stdout = std::io::stdout();
        for _ in 0..FRAME_HEIGHT {
            print!("\x1B[2K\n");  // clear line + move down
        }
        // Move back up to the line where rabbit started
        print!("\x1B[{}A", FRAME_HEIGHT);
        stdout.flush().ok();
    }
}

pub fn start_animation(state: RabbitState) -> AnimationHandle {
    let stop = Arc::new(AtomicBool::new(false));
    let s = stop.clone();

    // Print first frame immediately so area is established
    print_rabbit(state, 0);
    // Move cursor back up for the animation thread to overwrite from top
    print!("\x1B[{}A", FRAME_HEIGHT);
    std::io::stdout().flush().ok();

    let thread = thread::spawn(move || {
        let mut frame: usize = 0;
        loop {
            // Print current frame
            print_rabbit(state, frame);
            frame = frame.wrapping_add(1);
            std::io::stdout().flush().ok();

            thread::sleep(Duration::from_millis(220));

            // Always move cursor back up — whether we continue or stop
            print!("\x1B[{}A", FRAME_HEIGHT);
            std::io::stdout().flush().ok();

            if s.load(Ordering::Relaxed) {
                break;
            }
        }
        // Cursor is at TOP of rabbit area — Drop will clear from here
    });

    AnimationHandle {
        stop,
        thread: Some(thread),
    }
}
