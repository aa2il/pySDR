@echo off
echo.
echo Notes about how to run pySDR on Windoze 11
echo.
echo This is actually almost working using the "fake" RTL driver
echo Main problem is that the audio is glitchy but the panadapter seems ok.
echo.
echo  pip install pyrtlsdrlib
echo.
echo Run using the "fake" RTL driver:
echo.
echo    pySDR.py -fake
echo.
echo =======================================================================
echo. 
echo OLD NOTES - these may or may not be relavent?!
echo .
echo Need to build the SoapySDR stuff
echo   - Download and install swigwin  from swig.org
echo     -- It comes as a built dir, not an installed
echo     -- Add it to the system path
echo   - Download and install git for windows
echo     -- This one seems to do everything it needs all by itself
echo.
echo Open cmd and run BUILD.Soapy.bat
echo.
echo  - Next step is to build drivers for the SDR(s)
echo.
echo To compile (works under linux):
echo.
echo         pyinstaller --onefile pySDR.py
echo         dist\pySDR.exe
echo.

