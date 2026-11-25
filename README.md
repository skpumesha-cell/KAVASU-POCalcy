# KAVASU PostofficeCalcy

## Before building
1. Logo and icon are already in `assets\` (logo.png, logo_header.png, kavasu.ico).
2. Install on a Windows build PC: Python 3.8 **32-bit and 64-bit** (3.8 is the last Python that runs on
   Windows 7), and WiX Toolset 3.11.
3. Run `build_all.bat`  ->  `dist_msi\KAVASU_PostofficeCalcy_x86.msi` and `..._x64.msi`.

## Install result
`C:\KAVASU\POCalcy\KAVASU_PostofficeCalcy.exe` + Start Menu and Desktop shortcuts.
Rates are saved per user in `%APPDATA%\KAVASU\POCalcy\rates.json`.
Reports are saved in `Documents\KAVASU_PostofficeCalcy_Reports`.

## Windows 7 notes
Needs Windows 7 SP1 and the "Universal C Runtime" update (KB2999226). The x86 MSI runs on both 32-bit and
64-bit Windows; use the x64 MSI only if you want a native 64-bit EXE.

## Online build (no tools needed on your PC)
Upload this folder to a GitHub repository; `.github/workflows/build.yml` builds the 32-bit and 64-bit
MSI on GitHub's Windows servers. Run it from Actions -> Build MSI -> Run workflow, then download the artifacts.
