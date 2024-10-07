@echo off
color 3

set /p webhook="Enter the webhook URL: "

copy "SRC\script.py" "SRC\script_backup.py" >nul

powershell -Command "(Get-Content 'SRC\script.py') -replace '{{WEBHOOK}}', '%webhook%' | Set-Content 'SRC\script.py'"

echo Building the executable...
pyinstaller --onefile --noconsole --distpath dist --workpath build --specpath build SRC\script.py

copy "SRC\script_backup.py" "SRC\script.py" >nul

del "SRC\script_backup.py" >nul

echo Build complete! The executable is in the 'dist' folder.
pause
