"""啟動 claude -p 分析一張照片（架構文件第 3.3 節）。

防護 1、2 的內容都在 guards.py，這裡只負責呼叫。
"""

import asyncio
import json
import shutil
import tempfile
from pathlib import Path

from . import guards, schema
from .config import CLAUDE_TIMEOUT_SECONDS, HINT_MAX_CHARS, Config
from .schema import AnalysisError


async def analyze(cfg: Config, photo: bytes, ext: str, uploader_text: str) -> dict:
    """回傳 claude 的結構化答案（尚未檢查）。任何問題都丟 AnalysisError。"""
    claude_exe = shutil.which("claude")
    if claude_exe is None:
        raise AnalysisError("找不到 claude 指令")
    workdir = Path(tempfile.mkdtemp(prefix="foodbot-"))
    try:
        photo_path = workdir / f"photo.{ext}"
        photo_path.write_bytes(photo)
        cwd = guards.claude_cwd(workdir, cfg.data_dir)
        prompt = guards.build_prompt(
            guards.claude_photo_ref(photo_path, cwd), uploader_text, HINT_MAX_CHARS)
        args = [
            claude_exe, "-p",
            "--model", cfg.claude_model,
            "--output-format", "json",
            "--json-schema", json.dumps(schema.JSON_SCHEMA),
            "--no-session-persistence",
            "--system-prompt", guards.system_prompt(),
            *guards.claude_tool_args(),
        ]
        try:
            proc = await asyncio.create_subprocess_exec(
                *args, cwd=cwd, env=guards.claude_env(),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except OSError as e:
            raise AnalysisError(f"無法啟動 claude：{e.strerror}") from None
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(prompt.encode("utf-8")), CLAUDE_TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise AnalysisError(f"claude 逾時（{CLAUDE_TIMEOUT_SECONDS} 秒）") from None
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    if proc.returncode != 0:
        tail = stderr.decode("utf-8", "replace").strip()[-200:]
        raise AnalysisError(f"claude 結束碼 {proc.returncode}：{tail}")
    try:
        outer = json.loads(stdout.decode("utf-8"))
    except ValueError:
        raise AnalysisError("claude 外層輸出不是合法 JSON") from None
    if not isinstance(outer, dict) or outer.get("is_error"):
        raise AnalysisError("claude 回報錯誤")
    answer = outer.get("structured_output")
    if not isinstance(answer, dict):
        raise AnalysisError("claude 沒有回結構化答案")
    return answer
