#!/usr/bin/env python3
"""
Check every lesson folder in this repo without touching a network device.

For each lesson:
  1. YAML, JSON and Jinja2 files parse.
  2. Every Python import resolves: standard library, an installed package from
     the lesson's requirements.txt, or a module that exists in the lesson.
  3. Scripts that don't talk to devices or APIs run to completion.
  4. The lesson's own tests pass, where they don't need a device.

Run from the repo root:  python scripts/check_lessons.py [lesson-path ...]
Exit code is non-zero if anything fails.
"""

import ast
import base64
import importlib.util
import re
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError

ROOT = Path(__file__).resolve().parent.parent
TRACKS = ("beginner", "intermediate", "expert")

# A script importing any of these talks to a device, controller or cloud API,
# so it can only run against a lab. It is still parsed and import-checked.
NEEDS_NETWORK = {
    "netmiko", "nornir", "nornir_netmiko", "nornir_napalm", "nornir_utils",
    "napalm", "pyats", "genie", "unicon", "scrapli", "paramiko", "asyncssh",
    "requests", "httpx", "aiohttp", "hvac", "boto3", "botocore", "azure",
    "pynetbox", "dnacentersdk", "elasticsearch", "tacacs_plus", "sshtunnel",
}

# Scripts that are correct but can't run unattended, and why.
SKIP_RUN = {
    "expert/devops-observability-network-automation/prometheus_metrics.py":
        "starts a metrics HTTP server and serves until stopped",
}

# Scripts a lesson tells you to run before the others (they create a database
# or files the rest read). Run first, in the same working copy.
RUN_FIRST = {
    "intermediate/enterprise-config-backup-nornir": ["init_db.py"],
}

# Values the page tells you to set before running a script.
RUN_ENV = {
    "intermediate/credential-management-network-automation/encrypted_config_usage.py":
        {"ENCRYPTION_KEY": base64.urlsafe_b64encode(b"example-key-for-checks-only-32b!").decode()},
    "intermediate/pydantic-data-validation-network-automation/07_settings_and_secrets.py":
        {"NETAUTO_USERNAME": "admin", "NETAUTO_PASSWORD": "example"},
}

# Command-line tools that need arguments: prove they load and parse.
RUN_ARGS = {
    "expert/nornir-pyats-integration/main.py": ["--help"],
}

# Lessons whose tests need a lab (PyATS testbeds, live devices).
TESTS_NEED_LAB = {
    "intermediate/pyats-fundamentals",
    "intermediate/pyats-network-validation",
    "intermediate/building-reliable-automation-with-pyats",
}


def lessons(selected: list[str]) -> list[Path]:
    if selected:
        return [ROOT / s.rstrip("/") for s in selected]
    return sorted(p.parent for track in TRACKS
                  for p in (ROOT / track).glob("*/README.md"))


def top_level_imports(path: Path) -> list[tuple[str, int]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend((a.name, node.lineno) for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.append((node.module, node.lineno))
    return found


def pytest_pythonpath(lesson: Path) -> list[str]:
    config = lesson / "pyproject.toml"
    if not config.exists():
        return []
    match = re.search(r"pythonpath\s*=\s*\[([^\]]*)\]", config.read_text(encoding="utf-8"))
    return re.findall(r"[\"']([^\"']+)[\"']", match.group(1)) if match else []


def local_roots(lesson: Path, script: Path) -> list[Path]:
    """
    Where `import x` can come from when this file runs the way the lesson
    runs it: Python puts the script's own folder on the path, and pytest adds
    whatever the lesson's pyproject.toml lists. Nothing else.
    """
    roots = [script.parent]
    roots += [(lesson / entry).resolve() for entry in pytest_pythonpath(lesson)]
    return roots


def resolves_locally(module: str, roots: list[Path]) -> bool:
    parts = module.split(".")
    for root in roots:
        candidate = root.joinpath(*parts)
        if candidate.with_suffix(".py").is_file() or candidate.is_dir():
            return True
    return False


def check_data(lesson: Path, problems: list[str]) -> None:
    for path in sorted(lesson.rglob("*")):
        rel = path.relative_to(ROOT)
        try:
            if path.suffix in (".yaml", ".yml"):
                list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
            elif path.suffix == ".json":
                json.loads(path.read_text(encoding="utf-8"))
            elif path.suffix in (".j2", ".jinja2"):
                env = Environment(loader=FileSystemLoader([path.parent, lesson]))
                env.parse(path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, json.JSONDecodeError, TemplateSyntaxError) as exc:
            problems.append(f"{rel}: does not parse: {exc}")


def check_imports(lesson: Path, script: Path, problems: list[str]) -> set[str]:
    tops = set()
    for module, line in top_level_imports(script):
        top = module.split(".")[0]
        tops.add(top)
        if top in sys.stdlib_module_names:
            continue
        if resolves_locally(module, local_roots(lesson, script)):
            continue
        if importlib.util.find_spec(top) is not None:
            continue
        problems.append(f"{script.relative_to(ROOT)}:{line}: cannot import '{module}'")
    return tops


def run_script(copy: Path, lesson: Path, script: Path, problems: list[str]) -> None:
    """
    Run one script from the working copy, the way the lesson says to: from
    the lesson folder, or from src/ for lessons whose modules live there.
    """
    rel = script.relative_to(lesson)
    key = str(script.relative_to(ROOT))
    cwd = copy / "src" if rel.parts[0] == "src" else copy
    env = dict(os.environ, **RUN_ENV.get(key, {}))
    env.pop("PYTHONPATH", None)
    try:
        result = subprocess.run(
            [sys.executable, str(copy / rel), *RUN_ARGS.get(key, [])], cwd=cwd, env=env,
            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        problems.append(f"{key}: did not finish within 60s")
        return
    if result.returncode != 0:
        tail = (result.stderr or result.stdout).strip().splitlines()[-1:] or ["(no output)"]
        problems.append(f"{key}: exited {result.returncode}: {tail[0]}")


def run_tests(lesson: Path, problems: list[str]) -> str:
    key = str(lesson.relative_to(ROOT))
    tests = [p for p in lesson.rglob("test_*.py")]
    if not tests:
        return "no tests"
    if key in TESTS_NEED_LAB:
        return "tests need a lab (skipped)"
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / lesson.name
        shutil.copytree(lesson, copy)
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
            cwd=copy, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=300)
    summary = (result.stdout.strip().splitlines() or ["(no output)"])[-1]
    if result.returncode != 0:
        problems.append(f"{key}: tests failed: {summary}")
    return summary


def main(argv: list[str]) -> int:
    failures = 0
    for lesson in lessons(argv):
        key = str(lesson.relative_to(ROOT))
        problems: list[str] = []
        ran = 0

        check_data(lesson, problems)

        first = RUN_FIRST.get(key, [])
        scripts = sorted(lesson.rglob("*.py"),
                         key=lambda p: (str(p.relative_to(lesson)) not in first, str(p)))
        # One working copy per lesson, so a run can't leave files in the repo
        # and setup scripts (RUN_FIRST) can prepare what later scripts read.
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / lesson.name
            shutil.copytree(lesson, copy)
            for script in scripts:
                rel = str(script.relative_to(ROOT))
                try:
                    tops = check_imports(lesson, script, problems)
                except SyntaxError as exc:
                    problems.append(f"{rel}: syntax error: {exc}")
                    continue
                is_test = script.name.startswith("test_") or script.name == "conftest.py"
                if is_test or tops & NEEDS_NETWORK or rel in SKIP_RUN:
                    continue
                run_script(copy, lesson, script, problems)
                ran += 1

        tests = run_tests(lesson, problems)

        mark = "✗" if problems else "✓"
        print(f"{mark} {key}  ({ran} run offline; {tests})")
        for problem in problems:
            print(f"    {problem}")
        failures += bool(problems)

    print(f"\n{failures} lesson(s) with problems")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
