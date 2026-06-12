@echo off 
setlocal enabledelayedexpansion 
set "base64=" 
for /f "delims=" %%i in ('certutil -encode cookies.txt temp.txt ^> nul ^& type temp.txt') do ( 
    set "line=%%i" 
    if not "!line:~0,1!"=="-" if not "!line:~0,10!"=="-----BEGIN" if not "!line:~0,8!"=="-----END" ( 
        set "base64=!base64!!line!" 
    ) 
) 
echo !base64! 
echo Base64 saved to cookies_base64.txt 
type cookies_base64.txt 
del temp.txt 2>nul 
