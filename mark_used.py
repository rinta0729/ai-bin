"""AI便: 号を出したあと、使ったブックマークを「使用済み」にする。
使い方: python3 mark_used.py <号の日付 YYYY-MM-DD> <id> [<id> ...]   （--all-in-material で素材ファイルの全件）
"""
from __future__ import annotations
import json, sys
from pathlib import Path
from collect import OPS, STATE, load_state


def main() -> None:
    date, ids = sys.argv[1], sys.argv[2:]
    if ids == ["--all-in-material"]:
        ids = [it["id"] for it in json.loads((OPS / "素材" / f"{date}.json").read_text(encoding="utf-8"))]
    state = load_state()
    state["used_ids"] = sorted(set(state["used_ids"]) | set(ids))
    if date not in state["issues"]:
        state["issues"].append(date)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"使用済みにした: {len(ids)}件 / 累計 {len(state['used_ids'])}件 / 号 {state['issues']}")


if __name__ == "__main__":
    main()
