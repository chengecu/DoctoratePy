@echo off
@title Doctorate - Local Server

call env\scripts\activate.bat
start cmd /k mysql\bin\mysqld.exe
py server\app.py
