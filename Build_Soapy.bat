@echo off
set ARGS=-A x64
:: @goto RTL2
echo.
echo Script to build Soapy SDR on Windoz
echo.
echo Part 1 - Build Soapy SDR
echo 1) Open Browser, download and install git for windows
echo.
echo 2) Download source
:: rmdir /s /q SoapySDR
:: git clone https://github.com/pothosware/SoapySDR
:: goto :EOF
echo.
echo 3) Build it
cd SoapySDR
:: rmdir /s /q build
:: mkdir build
cd build
:: cmake %ARGS% ..
cd ..
cmake --build build --config Release
echo.
echo. 4) Install Soapy SDR:
echo     This should be possible from cmd line but having trouble ....
rem runas /user:Administrator "cmd.exe dir"
echo     For now, open a cmd prompt as admin and
echo cd \Users\Joea\Python\pySDR\SoapySDR
echo cmake --build build --config Release --target install
echo     -- In lower left coner of screen, search for "Advanced System Settings:
echo     -- Click environ vars and add C:\Program Files (x86)\SoapySDR\bin to the %PATH%
echo     -- Add C:\Program Files (x86)\SoapySDR\lib\site-packages to $PYTHON
echo.
echo  5) Test if
echo  Re-open a cmd prompt (to get new path) and run 
SoapySDRUtil --info
echo.
echo  - At this point, should be aable to run pySDR but it won't find an SDR
echo.
cd ..

:RTL1
echo.
echo Part 2 - Build RTL driver for Soapy
echo.
echo First, we need USB driver
echo Open a browser and goto to https://inst.eecs.berkeley.edu/~ee123/sp16/rtl_sdr_install.html
echo Download and unpack rtlsdr_win.zip
echo Move it to pySDR dir and unzip it
echo cd rtlsdr-win
echo From the RTL SDR blog: Plug in the RTL-SDR.
echo    Run Zadig as administrator by right clicking it and choosing run as administrator.
echo    Go to Options -> List all devices and make sure it is checked.
echo    In the drop down box choose Bulk-In, Interface (Interface 0). 
echo    This may also sometimes show up as something prefixed with ?RTL28328U?. That choice is also valid.
echo    Make sure that WinUSB is selected as the target driver and click on Replace Driver.
echo cd..
echo.

:RTL2
echo 6) Download source
:: rmdir /s /q SoapyRTLSDR
:: git clone https://github.com/pothosware/SoapyRTLSDR.git
:: goto :EOF
echo.
echo 7) Build it
cd SoapyRTLSDR
rmdir /s /q build
mkdir build
cd build
cmake %ARGS% ..
cd ..
cmake --build build --config Release
echo.
echo. 4) Install Soapy RTLSDR:
echo     This should be possible from cmd line but having trouble ....
rem runas /user:Administrator "cmd.exe dir"
echo     For now, open a cmd prompt as admin and
echo cd \Users\Joea\Python\pySDR\SoapyRTLSDR
echo cmake --build build --config Release --target install
echo     -- In lower left coner of screen, search for "Advanced System Settings:
echo     -- Click environ vars and add C:\Program Files (x86)\SoapySDR\bin to the %PATH%
echo     -- Add C:\Program Files (x86)\SoapySDR\lib\site-packages to $PYTHON
echo.
echo  - Open a cmd prompt and run SoapySDRUtil --info
echo.
echo  - At this point, should be aable to run pySDR but it won't find an SDR
echo.
cd ..




