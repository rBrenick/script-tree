@ECHO OFF
:BEGIN
CLS

ECHO Welcome to TOOL_NAME
ECHO Here are the options for install
ECHO.


ECHO    1. Install
ECHO    2. Uninstall
ECHO    3. Get Latest version of tool

ECHO.
SET /P AREYOUSURE=Choice: 
IF /I "%AREYOUSURE%" EQU "1" GOTO :Install
IF /I "%AREYOUSURE%" EQU "2" GOTO :Uninstall
IF /I "%AREYOUSURE%" EQU "3" GOTO :GetLatest

:Install
CALL _install_\install_maya_module.bat
GOTO END

:Uninstall
CALL _install_\uninstall_maya_module.bat
GOTO END

:GetLatest
Powershell.exe -executionpolicy remotesigned -File  _install_\get_latest_version.ps1
GOTO END


:END
PAUSE