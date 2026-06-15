# -*- coding: utf-8 -*-
"""
옵시디언 볼트에서 📅 날짜가 붙은 미완료 할 일을 골라 calendar.ics 로 만든다.

지원하는 날짜 표기 (할 일 줄 어디에 있어도 됨):
    - [ ] 교수님 미팅 📅 2026-06-20 14:00     ← 시간 있으면 1시간짜리 일정
    - [ ] G*Power 재확인 📅 2026-06-18         ← 시간 없으면 종일 일정
완료된 줄 ( - [x] ) 은 제외한다.
"""

import hashlib
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # 콘솔에 한글/특수문자 출력

# ── 설정 ────────────────────────────────────────────────
VAULT = Path(r"C:\Users\kohyu\Documents\Obsidian Vault")
OUTPUT = Path(__file__).with_name("calendar.ics")
CAL_NAME = "옵시디언 할일"
# ────────────────────────────────────────────────────────

# - [ ] ...  (미완료 체크박스만)
TASK_RE = re.compile(r"^\s*[-*]\s*\[\s\]\s*(.+)$")
# 📅 2026-06-20  또는  📅 2026-06-20 14:00
DATE_RE = re.compile(r"📅\s*(\d{4}-\d{2}-\d{2})(?:\s+(\d{1,2}):(\d{2}))?")


def clean_title(text: str) -> str:
    text = DATE_RE.sub("", text)                       # 날짜 토큰 제거
    text = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", text)  # [[link|alias]] -> alias
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)     # [[link]] -> link
    text = re.sub(r"\[[^\]]+::[^\]]*\]", "", text)      # [key:: val] dataview 인라인 제거
    text = re.sub(r"\s+", " ", text).strip(" -—·")
    return text or "(제목 없음)"


def esc(text: str) -> str:
    return (text.replace("\\", "\\\\").replace(";", "\\;")
                .replace(",", "\\,").replace("\n", "\\n"))


def fold(line: str) -> str:
    """RFC5545 라인 폴딩 (UTF-8 바이트 기준 75옥텟)."""
    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return line
    out, chunk = [], b""
    for ch in line:
        b = ch.encode("utf-8")
        limit = 75 if not out else 74  # 이어지는 줄은 앞에 공백 1칸
        if len(chunk) + len(b) > limit:
            out.append(chunk)
            chunk = b
        else:
            chunk += b
    out.append(chunk)
    return "\r\n ".join(c.decode("utf-8") for c in out)


def collect_events():
    events = []
    for md in VAULT.rglob("*.md"):
        if ".obsidian" in md.parts or ".tools" in md.parts:
            continue
        try:
            lines = md.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for line in lines:
            m = TASK_RE.match(line)
            if not m:
                continue
            body = m.group(1)
            d = DATE_RE.search(body)
            if not d:
                continue
            date_s, hh, mm = d.group(1), d.group(2), d.group(3)
            title = clean_title(body)
            uid = hashlib.sha1(
                (str(md.relative_to(VAULT)) + "|" + title).encode("utf-8")
            ).hexdigest()[:16] + "@obsidian"
            events.append((date_s, hh, mm, title, uid))
    return events


def build_ics(events) -> str:
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    out = [
        "BEGIN:VCALENDAR", "VERSION:2.0",
        "PRODID:-//obsidian-calendar//KR", "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH", f"X-WR-CALNAME:{CAL_NAME}",
    ]
    for date_s, hh, mm, title, uid in events:
        ymd = date_s.replace("-", "")
        out += ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{stamp}"]
        if hh is not None:
            start = f"{ymd}T{int(hh):02d}{int(mm):02d}00"
            dt = datetime.strptime(start, "%Y%m%dT%H%M%S") + timedelta(hours=1)
            out += [f"DTSTART:{start}", f"DTEND:{dt:%Y%m%dT%H%M%S}"]
        else:
            nxt = (datetime.strptime(ymd, "%Y%m%d") + timedelta(days=1))
            out += [f"DTSTART;VALUE=DATE:{ymd}", f"DTEND;VALUE=DATE:{nxt:%Y%m%d}"]
        out += [fold(f"SUMMARY:{esc(title)}"), "END:VEVENT"]
    out.append("END:VCALENDAR")
    return "\r\n".join(out) + "\r\n"


def main():
    events = collect_events()
    OUTPUT.write_text(build_ics(events), encoding="utf-8", newline="")
    print(f"할 일 {len(events)}건 -> {OUTPUT}")
    for date_s, hh, mm, title, _ in sorted(events):
        t = f" {hh}:{mm}" if hh else ""
        print(f"  {date_s}{t}  {title}")


if __name__ == "__main__":
    main()
