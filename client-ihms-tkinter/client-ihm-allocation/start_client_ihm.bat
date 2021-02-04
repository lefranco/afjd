@echo off


python client_ihm_allocation.py
if %errorlevel% NEQ 0 pause

exit
