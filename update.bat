@echo off
rem 옵시디언 할일 -> calendar.ics 재생성 후 GitHub에 push
cd /d "%~dp0"
echo ---- %date% %time% ---- >> update.log
py generate_ics.py >> update.log 2>&1
git add calendar.ics >> update.log 2>&1
git diff --cached --quiet && (echo 바뀐 할일 없음, push 생략 >> update.log & goto :end)
git commit -m "할일 캘린더 갱신" >> update.log 2>&1
git push >> update.log 2>&1
echo push 완료 >> update.log
:end
