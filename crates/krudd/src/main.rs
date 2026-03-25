use std::fs;
use std::io::{BufRead, BufReader, ErrorKind, Write};
use std::os::unix::net::UnixListener;
use std::process::Command;
use std::thread;
use std::time::Duration;

use anyhow::Result;
use krud_core::{
    complete_task, init_local_db, pop_next_task, queue_local_task, AppPaths, IpcRequest,
    IpcResponse,
};

fn main() -> Result<()> {
    let paths = AppPaths::discover()?;
    paths.ensure()?;
    init_local_db(&paths)?;

    if paths.socket_path.exists() {
        fs::remove_file(&paths.socket_path)?;
    }

    let listener = UnixListener::bind(&paths.socket_path)?;
    listener.set_nonblocking(true)?;
    println!("krudd listening on {}", paths.socket_path.display());

    loop {
        match listener.accept() {
            Ok((mut stream, _)) => {
                let request: IpcRequest = {
                    let mut reader = BufReader::new(&stream);
                    let mut line = String::new();
                    reader.read_line(&mut line)?;
                    serde_json::from_str(&line)?
                };

                let response = match request {
                    IpcRequest::Ping => IpcResponse {
                        ok: true,
                        message: "running".to_string(),
                    },
                    IpcRequest::QueueCommand { command, cwd } => {
                        let task_id = queue_local_task(&paths, &command, &cwd)?;
                        IpcResponse {
                            ok: true,
                            message: format!("Queued task {task_id}: {command}"),
                        }
                    }
                };

                stream.write_all(serde_json::to_string(&response)?.as_bytes())?;
            }
            Err(error) if error.kind() == ErrorKind::WouldBlock => {
                if let Some(task) = pop_next_task(&paths)? {
                    let output = Command::new("zsh")
                        .current_dir(&task.cwd)
                        .args(["-lc", &task.command])
                        .output()?;
                    let mut combined = String::new();
                    if !output.stdout.is_empty() {
                        combined.push_str(&String::from_utf8_lossy(&output.stdout));
                    }
                    if !output.stderr.is_empty() {
                        combined.push_str(&String::from_utf8_lossy(&output.stderr));
                    }
                    let final_status = if output.status.success() {
                        "completed"
                    } else {
                        "failed"
                    };
                    complete_task(&paths, &task.id, final_status, &combined)?;
                } else {
                    thread::sleep(Duration::from_millis(500));
                }
            }
            Err(error) => return Err(error.into()),
        }
    }
}
