@echo off
REM ============================================================
REM  Builds KAVASU_PostofficeCalcy EXE + MSI (32-bit and 64-bit)
REM  Needs: Python 3.8 x86 AND x64 (py launcher), WiX Toolset 3.11
REM ============================================================
setlocal
cd /d "%~dp0"
set NAME=KAVASU_PostofficeCalcy

if not exist assets\logo.png (echo Missing assets\logo.png & exit /b 1)
if not exist assets\logo_header.png (echo Missing assets\logo_header.png & exit /b 1)
if not exist assets\kavasu.ico (echo Put your icon at assets\kavasu.ico & exit /b 1)
if "%WIX%"=="" (echo WiX Toolset 3.11 not found - install it first & exit /b 1)
if not exist build mkdir build
if not exist dist_msi mkdir dist_msi

call :build 32 x86 || exit /b 1
call :build 64 x64 || exit /b 1
echo.
echo DONE. MSI files are in dist_msi\
exit /b 0

:build
echo === Building %2 ===
py -3.8-%1 -m pip install -r requirements.txt || exit /b 1
py -3.8-%1 -m PyInstaller --noconfirm --clean --onefile --windowed --name %NAME% ^
  --icon "%CD%\assets\kavasu.ico" ^
  --distpath "%CD%\build\dist%1" --workpath "%CD%\build\work%1" ^
  --add-data "%CD%\assets\logo.png;assets" --add-data "%CD%\assets\logo_header.png;assets" --add-data "%CD%\assets\kavasu.ico;assets" app.py || exit /b 1
"%WIX%bin\candle.exe" -nologo -arch %2 -dSourceExe="%CD%\build\dist%1\%NAME%.exe" -dIconFile="%CD%\assets\kavasu.ico" ^
  -out "%CD%\build\Product_%2.wixobj" installer\Product.wxs || exit /b 1
"%WIX%bin\light.exe" -nologo -out "%CD%\dist_msi\%NAME%_%2.msi" "%CD%\build\Product_%2.wixobj" || exit /b 1
exit /b 0
