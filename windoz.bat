@echo off
echo.
echo Notes about how to run pySDR on Windoze 10
echo.
echo !!!!!!!!!!!!!! WORK IN PROGRESS !!!!!!!!!!!!!!!!!
echo.
echo Need the following standard Python libraries:
echo            pip install
echo,
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

