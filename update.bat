@echo off
rem 옵시디언 할일 -> calendar.ics 재생성 후 GitHub에 push
cd /d "%~dp0"
py generate_ics.py
git add calendar.ics
git diff --cached --quiet && (echo 바뀐 할일 없음. & goto :end)
git commit -m "할일 캘린더 갱신"
git push
:end
