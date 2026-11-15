@echo off
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul
if %errorlevel%==0 (
  python server.py
) else (
  where py >nul 2>nul
  if %errorlevel%==0 (
    py server.py
  ) else (
    echo Khong tim thay Python. Hay cai Python tai python.org roi chay lai.
  )
)
pause
