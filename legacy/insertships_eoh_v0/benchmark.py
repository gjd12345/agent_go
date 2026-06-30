from __future__ import annotations

import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any


DEFAULT_TIMEOUT_SECONDS = 1200


def _kill_process_tree(pid: int) -> None:
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        try:
            os.kill(pid, 9)
        except OSError:
            pass


def parse_final_cost(output: str):
    for line in output.splitlines():
        lower_line = line.lower()
        if "final cost" in lower_line:
            idx = lower_line.find("final cost")
            return line[idx + len("final cost") :].strip(" :")
    return None


def parse_numeric_cost(cost_text):
    try:
        return float(cost_text)
    except (TypeError, ValueError):
        return None


def parse_go_duration_seconds(duration_text: str) -> float | None:
    """Parse Go-style duration strings such as 12.3ms, 1.2s, or 1m2.3s."""
    if not duration_text:
        return None
    total = 0.0
    matched = False
    units = {
        "h": 3600.0,
        "m": 60.0,
        "s": 1.0,
        "ms": 1e-3,
        "us": 1e-6,
        "µs": 1e-6,
        "ns": 1e-9,
    }
    for match in re.finditer(r"([0-9]+(?:\.[0-9]+)?)(ns|µs|us|ms|s|m|h)", duration_text):
        matched = True
        total += float(match.group(1)) * units[match.group(2)]
    return total if matched else None


def parse_first_response_time(output: str, mode: str = "cumulative") -> float | None:
    """
    Parse the solver's first-feasible response metric.

    Most current Go solvers print a final line like:
        12 9.8085783s
    where the first value is the number of insertion events and the second value
    is the cumulative time until the first feasible response for those events.
    For paper-style Res, we report cumulative/count by default.
    """
    for line in reversed(output.splitlines()):
        stripped = line.strip()
        match = re.match(r"^(\d+)\s+([0-9].*)$", stripped)
        if not match:
            continue
        count = int(match.group(1))
        seconds = parse_go_duration_seconds(match.group(2))
        if seconds is None:
            continue
        if mode == "average":
            return seconds
        return seconds / count if count > 0 else None
    return None


def parse_res_wall_time(output: str) -> float | None:
    match = re.search(r"RES\s+(-?\d+(?:\.\d+)?)", output)
    if not match:
        return None
    return float(match.group(1))


def run_subprocess(
    cmd: list[str],
    cwd: str | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    start_time = time.time()
    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
    proc: subprocess.Popen[str] | None = None
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=creationflags,
        )
        stdout, stderr = proc.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        if proc is not None:
            _kill_process_tree(proc.pid)
            try:
                stdout, stderr = proc.communicate(timeout=5)
            except Exception:
                stdout, stderr = "", ""
        return {
            "ok": False,
            "return_code": None,
            "stdout": stdout or "",
            "stderr": stderr or "",
            "duration": time.time() - start_time,
            "error": f"TIMEOUT({timeout_seconds}s)",
            "cmd": cmd,
            "cwd": cwd,
        }
    except Exception as e:
        return {
            "ok": False,
            "return_code": None,
            "stdout": "",
            "stderr": str(e),
            "duration": time.time() - start_time,
            "error": f"ERROR({type(e).__name__})",
            "cmd": cmd,
            "cwd": cwd,
        }

    return {
        "ok": proc.returncode == 0,
        "return_code": proc.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "duration": time.time() - start_time,
        "error": None,
        "cmd": cmd,
        "cwd": cwd,
    }


def build_go_binary(project_dir: str | Path, output_bin: str | Path, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    project_dir = str(Path(project_dir).resolve())
    output_bin = str(Path(output_bin).resolve())
    cmd = ["go", "build", "-o", output_bin, "."]
    result = run_subprocess(cmd, cwd=project_dir, timeout_seconds=timeout_seconds)
    result["output_bin"] = output_bin
    return result


def run_test(
    bin_path: str,
    data_path: str,
    t: int,
    extra_args: list[str] | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    abs_bin = os.path.abspath(bin_path)
    abs_data = os.path.abspath(data_path)
    cmd = [abs_bin, abs_data, str(t)]
    if extra_args:
        cmd.extend(extra_args)

    result = run_subprocess(cmd, timeout_seconds=timeout_seconds)
    if not result["ok"] and result["error"]:
        return {
            "cost": result["error"],
            "response_time": result["duration"],
            "return_code": result["return_code"],
            "stdout": result["stdout"],
            "stderr": result["stderr"],
        }

    cost = parse_final_cost(result["stdout"])
    if cost is None and result["return_code"] != 0:
        cost = f"RC{result['return_code']}"
    elif cost is None:
        cost = "NO_FINAL_COST"

    return {
        "cost": cost,
        "response_time": result["duration"],
        "first_response_time": parse_first_response_time(result["stdout"]),
        "res_wall_time": parse_res_wall_time(result["stdout"]),
        "return_code": result["return_code"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
    }
