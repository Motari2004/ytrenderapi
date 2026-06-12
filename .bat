echo @echo off > encode.bat
echo setlocal enabledelayedexpansion >> encode.bat
echo set "base64=" >> encode.bat
echo for /f "delims=" %%%%i in ('certutil -encode cookies.txt temp.txt ^^^> nul ^^^& type temp.txt') do ( >> encode.bat
echo     set "line=%%%%i" >> encode.bat
echo     if not "!line:~0,1!"=="-" if not "!line:~0,10!"=="-----BEGIN" if not "!line:~0,8!"=="-----END" ( >> encode.bat
echo         set "base64=!base64!!line!" >> encode.bat
echo     ) >> encode.bat
echo ) >> encode.bat
echo echo !base64! > cookies_base64.txt >> encode.bat
echo echo Base64 saved to cookies_base64.txt >> encode.bat
echo type cookies_base64.txt >> encode.bat
echo del temp.txt 2^>nul >> encode.bat