#!/usr/bin/env python3
import argparse
import fcntl
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
QUIET_PERIOD_SECONDS = 30
POLL_INTERVAL_SECONDS = 2
RETRY_INTERVAL_SECONDS = 30
COMMIT_MESSAGE = "Automated update"


class GitCommandError(Exception):
    pass


def git(*args):
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True,
        text=True,
        errors="replace",
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise GitCommandError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def current_status():
    return git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--ignore-submodules=dirty",
    )


def log(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    print(f"[{timestamp} UTC] {message}", flush=True)


def push_commit(branch, commit):
    git("push", "origin", f"{commit}:refs/heads/{branch}")


def watch():
    try:
        previous_status = current_status()
    except GitCommandError as error:
        log(str(error))
        return 1

    last_change = time.monotonic() if previous_status else None
    if previous_status:
        log("Pending changes found; committing after 30 seconds without changes.")
    log("Watching the main repository for file changes.")

    pending_push = None
    next_push_retry = 0

    while True:
        time.sleep(POLL_INTERVAL_SECONDS)
        now = time.monotonic()

        try:
            status = current_status()
        except GitCommandError as error:
            log(str(error))
            continue

        if status != previous_status:
            previous_status = status
            last_change = now if status else None
            if status:
                log("File changes detected; waiting for a quiet period.")

        if status and last_change is not None and now - last_change >= QUIET_PERIOD_SECONDS:
            last_change = now
            try:
                branch = git("branch", "--show-current")
                if not branch:
                    log("Cannot auto-commit while HEAD is detached.")
                    continue
                git("add", "--all")
                if not current_status():
                    continue
                git("commit", "-m", COMMIT_MESSAGE)
                commit = git("rev-parse", "HEAD")
                pending_push = (branch, commit)
                next_push_retry = 0
                previous_status = current_status()
                last_change = time.monotonic() if previous_status else None
                log(f"Committed {commit[:12]} on {branch}.")
            except GitCommandError as error:
                log(str(error))

        if pending_push is not None and now >= next_push_retry:
            branch, commit = pending_push
            try:
                push_commit(branch, commit)
                log(f"Pushed {commit[:12]} to origin/{branch}.")
                pending_push = None
            except GitCommandError as error:
                log(str(error))
                next_push_retry = now + RETRY_INTERVAL_SECONDS


def start_background():
    git_dir = Path(git("rev-parse", "--absolute-git-dir"))
    log_path = git_dir / "codespaces-auto-push.log"
    with log_path.open("a", encoding="utf-8") as output:
        process = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--foreground"],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=output,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            close_fds=True,
        )
    print(f"Auto-push watcher started (pid {process.pid}); log: {log_path}")


def run_foreground():
    git_dir = Path(git("rev-parse", "--absolute-git-dir"))
    with (git_dir / "codespaces-auto-push.lock").open("a", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            log("Auto-push watcher is already running.")
            return 0
        return watch()


def main():
    parser = argparse.ArgumentParser(description="Commit and push quiet-period changes.")
    parser.add_argument(
        "--foreground",
        action="store_true",
        help="run the watcher in the current process",
    )
    args = parser.parse_args()
    if args.foreground:
        return run_foreground()
    try:
        start_background()
    except GitCommandError as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
