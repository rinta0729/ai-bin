"""AI便: Xブックマークから「まだ号に使っていないもの」を集めて素材ファイルにする。AIは使わない。
使い方: python3 collect.py [--days 21]
出力: デスクトップ/AI便_運用/素材/<今日>.json
"""
from __future__ import annotations
import argparse, datetime, glob, json
from pathlib import Path

DESK = Path.home() / "Library/CloudStorage/OneDrive-岡山大学/デスクトップ"
BOOKMARKS = DESK / "りんた個人X_100日AI豆知識/_api/bookmarks"
OPS = DESK / "AI便_運用"
STATE = OPS / "state.json"


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"used_ids": [], "issues": []}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=21, help="何日前までのブックマークを対象にするか")
    args = ap.parse_args()

    state = load_state()
    used = set(state["used_ids"])
    since = (datetime.date.today() - datetime.timedelta(days=args.days)).isoformat()

    seen: dict[str, dict] = {}
    for f in sorted(glob.glob(str(BOOKMARKS / "2026-*.json")) + glob.glob(str(BOOKMARKS / "2027-*.json"))):
        for it in json.loads(Path(f).read_text(encoding="utf-8")):
            seen[it["id"]] = it

    items = [
        {
            "id": it["id"],
            "date": it.get("created_at", "")[:10],
            "author": it.get("author_username"),
            "url": it.get("url"),
            "text": it.get("text", ""),
            "links": it.get("links") or [],
            "bookmarks": (it.get("public_metrics") or {}).get("bookmark_count", 0),
        }
        for it in seen.values()
        if it["id"] not in used and it.get("created_at", "")[:10] >= since
    ]
    items.sort(key=lambda x: (x["date"], x["bookmarks"]), reverse=True)

    out = OPS / "素材" / f"{datetime.date.today().isoformat()}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"未使用のブックマーク {len(items)}件（{since} 以降）→ {out}")
    if state["issues"]:
        print(f"前回の号: {state['issues'][-1]}")


if __name__ == "__main__":
    main()
