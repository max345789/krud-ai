//! Legacy mascot module for krud.
//!
//! The old rabbit has been replaced with an original "Krud Core" reactor
//! animation, but the module name is kept to avoid touching the rest of the
//! CLI wiring. Each frame is 9 lines tall and uses fixed-width rows within a
//! state so in-place animation stays clean.

use crossterm::style::{Color, Stylize};
use std::io::Write;
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc,
};
use std::thread;
use std::time::Duration;

const PURPLE: Color = Color::Rgb {
    r: 168,
    g: 85,
    b: 247,
};
const PURPLE_LIGHT: Color = Color::Rgb {
    r: 221,
    g: 174,
    b: 255,
};
const CYAN: Color = Color::Rgb {
    r: 103,
    g: 232,
    b: 249,
};
const DANGER: Color = Color::Rgb {
    r: 248,
    g: 113,
    b: 113,
};
const WHITE: Color = Color::White;

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
        RabbitState::Idle => [
            [
                "      ╱╲       ",
                "    ╭╱██╲╮     ",
                "   ╱██◇◇██╲    ",
                "   │█████▓│    ",
                "   │▓█████│    ",
                "   ╲██◇◇██╱    ",
                "    ╰╲██╱╯     ",
                "      • •      ",
                "               ",
            ],
            [
                "      ╱╲       ",
                "    ╭╱██╲╮     ",
                "   ╱██◇◇██╲    ",
                "   │▓█████│    ",
                "   │█████▓│    ",
                "   ╲██◇◇██╱    ",
                "    ╰╲██╱╯     ",
                "     •   •     ",
                "               ",
            ],
        ],
        RabbitState::Thinking => [
            [
                "    • ╱╲       ",
                "    ╭╱██╲╮     ",
                "   ╱██◐◑██╲    ",
                "   │██▓███│    ",
                "   │████▓█│    ",
                "   ╲██◐◑██╱    ",
                "    ╰╲██╱╯ •   ",
                "       •       ",
                "               ",
            ],
            [
                "      ╱╲ •     ",
                "    ╭╱██╲╮     ",
                "   ╱██◑◐██╲    ",
                "   │████▓█│    ",
                "   │██▓███│    ",
                "   ╲██◑◐██╱    ",
                "  • ╰╲██╱╯     ",
                "       •       ",
                "               ",
            ],
        ],
        RabbitState::Running => [
            [
                "      ╱╲═══    ",
                "    ╭╱██╲╮══   ",
                "   ╱██◆◆██╲═   ",
                "   │██████▓│   ",
                "   │▓██████│   ",
                "   ╲██◆◆██╱═   ",
                "    ╰╲██╱╯══   ",
                "     ▝▝  ▝▝    ",
                "               ",
            ],
            [
                "   ═══╱╲       ",
                "   ══╭╱██╲╮    ",
                "   ═╱██◆◆██╲   ",
                "   │▓██████│   ",
                "   │██████▓│   ",
                "   ═╲██◆◆██╱   ",
                "   ══╰╲██╱╯    ",
                "    ▝▝  ▝▝     ",
                "               ",
            ],
        ],
        RabbitState::Success => [
            [
                "   ✦  ╱╲  ✦    ",
                "    ╭╱██╲╮     ",
                "  ✦╱██◈◈██╲✦   ",
                "   │██████│    ",
                "   │██████│    ",
                "  ✦╲██◈◈██╱✦   ",
                "    ╰╲██╱╯     ",
                "   ✦  ▀▀  ✦    ",
                "               ",
            ],
            [
                "    ✦╱╲✦       ",
                "    ╭╱██╲╮  ✦  ",
                "   ╱██◈◈██╲    ",
                " ✦ │██████│    ",
                "   │██████│ ✦  ",
                "   ╲██◈◈██╱    ",
                "  ✦ ╰╲██╱╯     ",
                "     ▀▀   ✦    ",
                "               ",
            ],
        ],
        RabbitState::Error => [
            [
                "      ╱╲       ",
                "    ╭╱██╲╮     ",
                "   ╱██××██╲    ",
                "   │██╳███│    ",
                "   │██!███│    ",
                "   ╲██××██╱    ",
                "    ╰╲██╱╯     ",
                "      ▂▂       ",
                "               ",
            ],
            [
                "      ╱╲       ",
                "    ╭╱██╲╮     ",
                "   ╱██××██╲    ",
                "   │██!███│    ",
                "   │██╳███│    ",
                "   ╲██××██╱    ",
                "    ╰╲██╱╯     ",
                "      ▂▂       ",
                "               ",
            ],
        ],
    }
}

fn is_frame_char(ch: char) -> bool {
    matches!(ch, '╱' | '╲' | '╭' | '╮' | '╰' | '╯' | '│')
}

fn is_core_char(ch: char) -> bool {
    matches!(ch, '█' | '▓' | '◆' | '◇' | '◈' | '◉' | '◐' | '◑')
}

fn is_spark_char(ch: char) -> bool {
    matches!(ch, '•' | '✦' | '✶' | '▀' | '▝')
}

fn is_alert_char(ch: char) -> bool {
    matches!(ch, '×' | '╳' | '!')
}

pub fn print_rabbit(state: RabbitState, frame: usize) {
    let f = frames(state);
    let lines = &f[frame % 2];
    let mut stdout = std::io::stdout();

    for line in lines {
        print!("  ");
        for ch in line.chars() {
            if is_alert_char(ch) {
                print!("{}", ch.to_string().with(DANGER).bold());
            } else if is_spark_char(ch) {
                print!("{}", ch.to_string().with(CYAN).bold());
            } else if is_core_char(ch) {
                print!("{}", ch.to_string().with(PURPLE_LIGHT).bold());
            } else if is_frame_char(ch) {
                print!("{}", ch.to_string().with(PURPLE));
            } else if ch == ' ' {
                print!(" ");
            } else {
                print!("{}", ch.to_string().with(WHITE));
            }
        }
        println!();
    }
    stdout.flush().ok();
}

pub struct AnimationHandle {
    stop: Arc<AtomicBool>,
    thread: Option<thread::JoinHandle<()>>,
}

impl Drop for AnimationHandle {
    fn drop(&mut self) {
        self.stop.store(true, Ordering::Relaxed);
        if let Some(thread) = self.thread.take() {
            let _ = thread.join();
        }

        let mut stdout = std::io::stdout();
        for _ in 0..FRAME_HEIGHT {
            print!("\x1B[2K\n");
        }
        print!("\x1B[{}A", FRAME_HEIGHT);
        stdout.flush().ok();
    }
}

pub fn start_animation(state: RabbitState) -> AnimationHandle {
    let stop = Arc::new(AtomicBool::new(false));
    let stop_flag = stop.clone();

    print_rabbit(state, 0);
    print!("\x1B[{}A", FRAME_HEIGHT);
    std::io::stdout().flush().ok();

    let thread = thread::spawn(move || {
        let mut frame = 0usize;
        loop {
            print_rabbit(state, frame);
            frame = frame.wrapping_add(1);
            std::io::stdout().flush().ok();

            thread::sleep(Duration::from_millis(220));

            print!("\x1B[{}A", FRAME_HEIGHT);
            std::io::stdout().flush().ok();

            if stop_flag.load(Ordering::Relaxed) {
                break;
            }
        }
    });

    AnimationHandle {
        stop,
        thread: Some(thread),
    }
}
