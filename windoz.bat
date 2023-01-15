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
echo.
echo   - Download & unpack the source code from github
echo     -- mkdir build          Make build dir
echo     -- cd build             Make dependancies
echo     -- cmake ..
echo     -- cmake --build my_build_dir --config Release
echo     -- Open a cmd prompt as admin and do this:
echo         cmake --build my_build_dir --config Release --target install
echo     -- In lower left coner of screen, search for "Advanced System Settings:
echo     -- Click environ vars and add C:\Program Files (x86)\SoapySDR\bin to the %PATH%
echo     -- Add C:\Program Files (x86)\SoapySDR\lib\site-packages to $PYTHON
echo  - Open a cmd prompt and run SoapySDRUtil --info
echo  - At this point, should be aable to run pySDR but it won't find an SDR
echo.
echo  - Next step is to build drivers for the SDR(s)
echo.
echo To compile (works under linux):
echo.
echo         pyinstaller --onefile pySDR.py
echo         dist\pySDR.exe
echo.

