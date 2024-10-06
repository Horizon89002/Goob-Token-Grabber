@echo off
color D

:choose_pip
echo Do you want to use pip or pip3?
set /p choice= 

if /i "%choice%"=="pip" (
    set "PIP_COMMAND=pip"
) else if /i "%choice%"=="pip3" (
    set "PIP_COMMAND=pip3"
) else (
    echo Invalid choice. Please type pip or pip3.
    goto choose_pip
)

echo Installing required packages using %PIP_COMMAND%...

%PIP_COMMAND% install requests
%PIP_COMMAND% install discord
%PIP_COMMAND% install pyinstaller
%PIP_COMMAND% install pyautogui
%PIP_COMMAND% install psutil


echo All required packages installed. You may now use the builder.
pause