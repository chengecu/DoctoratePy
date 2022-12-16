@echo off
 
:: BatchGotAdmin
:-------------------------------------
REM  --> Check for permissions
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
 
REM --> If error flag set, we do not have admin.
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    goto UACPrompt
) else ( goto gotAdmin )
 
:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
 
    "%temp%\getadmin.vbs"
    exit /B
 
:gotAdmin
    if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )
    pushd "%CD%"
    CD /D "%~dp0"
:--------------------------------------

title Doctorate - MySQL
cd /d %~dp0

echo [client] > my.ini
echo port=3306 >> my.ini
echo default-character-set=utf8mb4 >> my.ini
echo [mysqld] >> my.ini
echo default_authentication_plugin=mysql_native_password >> my.ini
echo max_allowed_packet=500M >> my.ini
echo wait_timeout=2880000 >> my.ini
echo interactive_timeout=2880000 >> my.ini
echo max_connect_errors=10 >> my.ini
echo max_connections=20 >> my.ini
echo port=3306 >> my.ini
echo character_set_server=utf8mb4 >> my.ini
echo basedir="%cd:\=/%" >> my.ini
echo datadir="%cd:\=/%/data" >> my.ini
echo default-storage-engine=INNODB >> my.ini
echo [WinMySQLAdmin] >> my.ini
echo "%cd:\=/%/bin/"mysqld.exe >> my.ini

net stop mysql
"%cd:\=/%/bin/"mysqld remove MySQL
"%cd:\=/%/bin/"mysqld install MySQL
"%cd:\=/%/bin/"mysqld --initialize --user=root --console
net start MySQL

goto main

:main
set choice=""
set /p choice="Enter stop to close:"
if "%choice%" == "stop" goto end
goto main

:end
net stop mysql
"%cd:\=/%/bin/"mysqld remove MySQL

