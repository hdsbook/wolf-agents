"""印出本專案的 session 對話紀錄目錄（*.jsonl 所在處）。

Claude Code 把專案路徑中每個非英數字元換成「-」當目錄名，
放在 ~/.claude/projects/ 底下。由專案路徑推算，換機器、換使用者都不必改文件。

用法：python .claude/skills/god-audit/transcript_dir.py
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

project = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))
name = re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(project))
path = os.path.join(os.path.expanduser("~"), ".claude", "projects", name)
print(path)
if not os.path.isdir(path):
    print("警告：此目錄不存在，請確認專案路徑。", file=sys.stderr)
    sys.exit(1)
