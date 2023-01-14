@echo off
@title Doctorate - Frida Hook

call env\scripts\activate.bat
py fridahook.py %*
