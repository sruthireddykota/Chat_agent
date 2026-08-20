import subprocess
import sys
import json
from pathlib import Path
from agent_framework import FileSkill, FileSkillScript
from app.utils.logger import get_logger

logger = get_logger()


def script_runner(skill: FileSkill, script: FileSkillScript, args: dict | None = None) -> str:

    # 1. Input validation
    stdin_input = None
    if args and "input" in args:
        stdin_input = args["input"]
        if len(stdin_input) > 50_000:
            raise ValueError("Input too large — max 50,000 characters")

    # 2. Build command
    # script_path = str(Path(skill.path) / script.path)
    script_path = Path(script.full_path)
    cmd = [sys.executable, str(script_path)]

    if args:
        if "command" in args and args["command"]:
            cmd.append(str(args["command"]))
        if "query" in args and args["query"]:
            cmd.append(str(args["query"]))
        
        for key, value in args.items():
            if key not in ("command", "query", "input") and value is not None:
                cmd.extend([f"--{key}", str(value)])

    # 3. Log start
    logger.info(json.dumps({
        "event": "skill_script_start",
        "script": str(script.full_path),
        "cmd": cmd,
        "input_length": len(stdin_input) if stdin_input else 0,
    }))

    # 4. Run
    try:
        result = subprocess.run(
            cmd,
            input=stdin_input,
            capture_output=True,
            text=True,
            timeout=90,
        )

    except subprocess.TimeoutExpired:
        logger.error(json.dumps({
            "event": "skill_script_timeout",
            "script": str(script.full_path),
        }))
        raise RuntimeError(f"Script timed out after 90s: {script_path}")

    # 5. Log complete
    logger.info(json.dumps({
        "event": "skill_script_complete",
        "script": str(script.full_path),
        "exit_code": result.returncode,
        "output_length": len(result.stdout),
        "stderr": result.stderr[:500] if result.stderr else None,
    }))

    # 6. Surface stderr if script failed
    if result.returncode != 0:
        if result.stderr and result.stderr.strip():
            logger.error(json.dumps({
                "event": "skill_script_failed",
                "exit_code": result.returncode,
                "stderr": result.stderr[:1000],
            }))
            raise RuntimeError(
                f"Script failed (exit {result.returncode}): {result.stderr[:500]}"
            )
        else:
            logger.warning(json.dumps({
                "event": "skill_script_no_input",
                "exit_code": result.returncode,
                "stdout": result.stdout[:200],
            }))
            return result.stdout.strip()



