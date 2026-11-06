#!/usr/bin/env python3
"""Commit and push saved working-tree changes for this repository."""

from __future__ import annotations

import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
POLL_SECONDS = 2
QUIET_SECONDS = 3
LOG_FILE = REPOSITORY / ".git" / "auto-push.log"
running = True


def log(message: str) -> None:
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(f"{timestamp} {message}\n")


def run_git(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=REPOSITORY,
        check=False,
        capture_output=True,
        text=True,
    )


def status() -> str:
    result = run_git("status", "--porcelain")
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git status failed")
    return result.stdout


def commit_and_push() -> None:
    if not status():
        return

    staged = run_git("add", "--all")
    if staged.returncode != 0:
        raise RuntimeError(staged.stderr.strip() or "git add failed")

    message = f"Auto-save changes {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %z')}"
    committed = run_git(
        "-c",
        "user.name=rattnak",
        "-c",
        "user.email=rattnak@users.noreply.github.com",
        "commit",
        "-m",
        message,
        "-m",
        "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>",
    )
    if committed.returncode != 0:
        raise RuntimeError(committed.stderr.strip() or "git commit failed")

    pushed = run_git("push", "origin", "HEAD")
    if pushed.returncode != 0:
        raise RuntimeError(pushed.stderr.strip() or "git push failed")

    log(f"committed and pushed: {message}")


def stop(_signum: int, _frame: object) -> None:
    global running
    running = False


def main() -> int:
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    log("watcher started")
    previous_status = ""
    changed_at: float | None = None

    while running:
        try:
            current_status = status()
            if current_status != previous_status:
                previous_status = current_status
                changed_at = time.monotonic()
            elif changed_at is not None and time.monotonic() - changed_at >= QUIET_SECONDS:
                commit_and_push()
                previous_status = status()
                changed_at = None
        except Exception as error:
            log(f"error: {error}")
            changed_at = None
        time.sleep(POLL_SECONDS)

    log("watcher stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
