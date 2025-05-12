# Software Defined Receiver

A complete SDR written in Python.  Supports both SDR Play RSP and RTL Dongle via Soapy SDR.  Can be used as stand alone or as a pan adaptor.  Rig interfacing accomplished via direct connection, flrig, fldigi or hamlib.

![Waterfall]( Docs/waterfall.png)
![Screen Shot]( Docs/pysdr.png)

Background

Several years ago, I purchased an RTL dongle as a curiosity and shortly there after, I purchased an SDRplay RSP2.  Having spent my entire professional career working in signal procesing R&D (including SDR), I was quite interested in how well such inexpensive devices performed and how to program them.  Needless to say, I was pleasently surprised to find out that, what use to take room full of specialized equipment when I started my career some 40-years ago, can now be accomplished with one of these device connected to a laptop or even a Raspberry Pi - and with superior performance!

There are number of very good SDR applications available for these devices, both for Windoze and Linux.  The intent of this project is not to replicate or compete with these.  Rather, it is to 1) demonstrate that high-fidelity processing can be done on modest hardware using code entirely written in Python and 2) develop an application that is closely integrated with the equipment in my "ham shack."  To this end, only devices/equipment that I own or have ready access to are supported.  However, it is believed that additional 1) SDR devices can be supported as SoapySDR is used for all low-level device i/o and 2) tranceivers can be used as flrig or hamlib can be selected for the i/o for these device.
                                                                                Like all codes found in this repository, this SDR code was developed for my own amusement and enrichment.  Feel free to make use of this for personal non-commercial purposes AT YOUR OWN RISK.  I only ask that proper attribution be given to the original source.  These codes are provide without any implied guarrentees and are not meant to compete with or be alternatives to any other similar or related projects. I welcome any CONSTRUCTIVE feedback and/or suggested improvements but I am not of a mindset to provide much in the way of "tech support" or additional documentation.

Features

This project initially started out (circa 2017) as a simple demodulator for broadcast AM radio.  The remminants of this are found in the file am.py.  As the effort progress, a gui and graphics were added as well as different demodulation techniques, processing schemes and other capabilities.  In its current form, this project support the following features:

- Written entirely in Python, developed under recent version of Linux Mint, use readiliy available libraries
- Use with SDRPlay RSP2 and RTL Dongle
- Uses SoapySDR for low-level control and I/O to SDR device
- All the configuration of the SDR device can be controlled via GUI or commandline parameters
- All significant processing parameters (e.g. center frequencies, demodulator type, filter bandwidths, etc.) can be controlled via command-line arguements thereby facilitating easy scripting
- Demodulators for AM, narrowband FM, Upper and Lower Sideband, CW, and IQ basebanding.  A preliminary demodulator for wideband stereo FM is also included but has not been refined as I generally do not listen to very much commercial FM radio (too many commercials!).
- Adjustable filter and processing bandwidths and sampling rates
- GUI resembles old-style push-button radio rather than a graphics-intensive interfaces common with most SDR programs.  This is to minimize impact on the CPU.  While not refined, spectral plots, waterfalls, etc. are avaiable via a mouse-click when desired.
- Up to four independent receivers can be tuned to anywhere within the SDR device instantaneous bandwidth (~8-MHz for SDRPlay and ~2-MHz for RTL Dongle).
- Demodulated audio can be routed to a physical device (e.g. computer speakers) or loopback sound device (e.g. to pipe to another application)
- Can be closely integrated with several ham rigs including the Yaesu FTdx3000 and FT991a, ICOM IC706 and IC9700 and Kenwood TS850.
- Rig communication can be via either direct USB connection, flrig, fldigi, or hamlib.
- My primary use for this code is as a Pan-Adapter for my FTdx3000.  As such, this code is intgrated with the logger and bandmap codes found in this repository.  These code communicate via UDP messages to display information such as DX spots, potential contest mulitpliers, etc.

To be continued....
                                                                                
# Installation under Linux using uv:

0) This seems to be the easiest/best solution.  You will need to install uv on your system (once):

      curl -LsSf https://astral.sh/uv/install.sh | sh      
      rehash     

1) Clone gitub pySDR, libs and data repositories
      
      cd
      mkdir Python
      cd Python
      git clone https://github.com/aa2il/pySDR
      git clone https://github.com/aa2il/libs
      git clone https://github.com/aa2il/data

2) One of the features of uv is that the virtual environment is included in the github repository.  You should NOT have to do anything since uv will install the environment and required packages the first time you run wclock.:

For the record, here is how I set up the environment:

     cd ~/Python/pySDR
     uv init
     rm main.py
     uv add -r requirements.txt

Note: pySDR.py uses qt, not tk, so there is no problem with the recent versions of python (e.g. 3.13).

3) Patch-up SoapySDR: uv does not seem to have a version of SoapySDR so we need to cobbled this together:

     cd ~/Python/pySDR/.venv/lib/python3.13/site-packages
     rm -f SoapySDR.py _SoapySDR.so 
     ln -s ~/Dev/SoapySDR/build/swig/python/SoapySDR.py 
     ln -s ~/Dev/SoapySDR/build/swig/python/_SoapySDR.so 

3) Make sure pySDR.py is executable and set PYTHON PATH so os can find libraries:

     cd ~/Python/pySDR
     chmod +x pySDR.py

   - Under tcsh:      setenv PYTHONPATH $HOME/Python/libs
   - Under bash:      export PYTHONPATH="$HOME/Python/libs"
   
4) Bombs away:

     uv run pySDR.py

   or, 

     ./pySDR.py

# Installation under Linux:

1) Uses python3 and pyqt5
2) Clone gitub pySDR, libs and data repositories
      
      cd
      mkdir Python
      cd Python
      git clone https://github.com/aa2il/pySDR
      git clone https://github.com/aa2il/libs
      git clone https://github.com/aa2il/data

      You will also need to make sure that the python interpretor can find the libraries.
      Under tcsh, execute the following and/or add it to your .cshrc file:

              setenv PYTHONPATH $HOME/Python/libs

      Under bash, the equivalent is something like this:

              export PYTHONPATH="$HOME/Python/libs"
      
3) Build components that deal with the SDR device:
   Note! As of October 2024, the latest version of Soapy is broken.  I'm using an older build.
         
      cd ~/Python/pySDR
      BUILD_Soapy
      BUILD_RTL
      BUILD_SDRplay
      
4) Install packages needed for pySDR:
   Note! As of python 3.11, its very difficult to install pacakges on the system or user level.  Hence,
   As of Oct 2024, the "sandbox" outline below is recommened.
                                   
      cd ~/Python/pySDR
      pip3 install -r requirements.txt
      
5) Make sure its executable:
         
      chmod +x pySDR.py start start_cw
   
6) Set PYTHON PATH so os can find libraries:
         
   - Under tcsh:      setenv PYTHONPATH $HOME/Python/libs
   - Under bash:      export PYTHONPATH="$HOME/Python/libs"
   
7) Bombs away:
      ./pySDR.py

# Installation under Mini-conda - the "sandbox" approach:

   As of Python 3.12, there are a lot more restrictions imposed on using pip,
   to the point where it is becoming difficult to get things going.  Accordingly,
   it is time to start migrating toward a "sandbox."
   
0) Good video:  https://www.youtube.com/watch?v=23aQdrS58e0&t=552s

1) Miniconda homepage: https://docs.conda.io/en/latest/miniconda.html

2) Download and install latest & greatest Mini-conda for your particular OS:

   - I used the bash installer for linux - Follow the prompts:

       mkdir -p ~/miniconda3
       cd ~/miniconda3
       wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O 
       bash ~/miniconda3/Miniconda3-latest-Linux-x86_64.sh -b -u -p ~/miniconda3
       #rm ~/miniconda3/Miniconda3-latest-Linux-x86_64.sh

   - If you'd prefer that conda's base environment not be activated on startup,
     set the auto_activate_base parameter to false:
   
       conda config --set auto_activate_base false

   - To get it to work under tcsh:

       cd    
       bash
       conda init tcsh
       
    - This creates ~/.tcshrc - move its contents to .cshrc if need be.
    - Relaunch tcsh and all should be fine!  Test it with:
       
       conda list

3) Create a working enviroment for ham radio stuff:

    -  !!! By default, conda does not include very many fonts for tk and therefore the
           Tk GUIs look like crap.  Do this when creating the sandbox to avoid this problem:

       bash
       cd ~/miniconda3/envs/
       conda create -y --prefix "aa2il" -c conda-forge "python==3.12.*" "tk[build=xft_*]"
       exit

    - The fonts on an existing sandbox can be upgraded via:

       bash
       conda install --prefix "aa2il" -c conda-forge "tk=*=xft_* "
       exit
       
    - Note: there may be downgrades some of the packages - who cares!  
         
    - To activate this environment, use:
         conda activate aa2il
    - To deactivate an active environment, use:
         conda deactivate
    - To see all the available envirnoments:
         conda env list
    - To remove an environment:
        conda remove -n aa2il --all
    - To see conda and python versions:
        conda info
        
4) Clone the gitub pySDR, libs and data repositories:

       cd
       mkdir Python
       cd Python
       git clone https://github.com/aa2il/pySDR
       git clone https://github.com/aa2il/libs
       git clone https://github.com/aa2il/data

5) Install packages needed by pySDR:

       cd ~/Python/pySDR
       conda activate aa2il
       pip3 install -r requirements.txt

   - !!! As of Oct 2024, the latest version of SoapySDR is hosed up and doesn't work.
     I'm still using an older version which seems just fine.  If/when this ever does get resolved,
     there are two options:
     
     -- From conda repository - this only gives us the RTL dongle:
        This worked in July 2024 but no longer works in Oct 2024 - ugh!
     
          conda install -c conda-forge soapysdr
          conda install -c conda-forge soapysdr-module-rtlsdr

     -- From the local build (see Installation under Linux, step 3 above) - this gives both RTL dongle and sdrplay:
        This is what I am currently using (and still works under python 3.13):
          
          cd ~/miniconda3/envs/aa2il/lib/python3.12/site-packages/
          rm -f SoapySDR.py _SoapySDR.so 
          ln -s ~/Dev/SoapySDR/build/swig/python/SoapySDR.py 
          ln -s ~/Dev/SoapySDR/build/swig/python/_SoapySDR.so 
   
6) Need to "blacklist" the RTL Dongle:

      sudo ln -s /home/joea/miniconda3/envs/aa2il/lib/udev/rules.d/rtl-sdr.rules /etc/udev/rules.d/
      sudo udevadm control --reload && sudo udevadm trigger

7) Set PYTHON PATH so os can find libraries:
         
   - Under tcsh:      setenv PYTHONPATH $HOME/Python/libs
   - Under bash:      export PYTHONPATH="$HOME/Python/libs"

8) To run pySDR, we need to specify python interpreter so it doesn't run in
   the default system environment:
   
      cd ~/Python/pySDR
      conda activate aa2il
      python pySDR.py

9) Known issues using this (as of Oct 2024):
   - Latest version of SoapySDR is broke.
     A platform-independent drivers is a fine idea and noble goal but this
     package has been very problematic.  Specifically, each time I've
     upgraded my OS, the version of this package provided by the distribution
     never works and  I end up fiddling with this package to get it functioning.
     This was tolerable until this latest release which I can't even get to
     function properly. Accordingly, I am in the process of abandoning this
     package and developing my own drivers for the RTL and SDRPlay.
     The driver for the RTL is showing promise and needs further testing.
     Until these are ready, my recommendation is to use the older version
     of this package.
   - There can be a problem with the waterfall plots when pySDR is run for
     a while (hours).  I think this is due to the buffering of the samples
     from the SDR.  This needs to be changed to a "push" model instead of a
     separate timer thread that just fires - will be addressed soon...

# Installation for Windoz:

0) One option is to use miniconda and follow the directions above.
      
1) I had success installing Python (v3.12 as of Oct 2024) the Microslop Store
   (or directly from python.org).

2) Install dependancies:

   pip install -r requirements.txt
   pip install pyrtlsdrlib

3) Install RTL-SDR driver - follow instructions at https://www.rtl-sdr.com/getting-the-rtl-sdr-to-work-on-windows-10/
      
   3a) Download the latest version of Zadig from zadig.akeo.ie
   3b) Plug in the RTL-SDR.
   3c) Run Zadig as administrator
   3d) Go to Options -> List all devices and make sure it is checked.
   3e) In the drop down box choose Bulk-In, Interface (Interface 0). This may also sometimes show up as something prefixed with "RTL28328U". That choice is also valid.
   3f) Make sure that WinUSB is selected as the target driver and click on Replace Driver.

4) Run it using "fake" RTL driver

   pySDR.py -fake
   
5) I have not tried getting Soapy installed under winblows to have supprot for the SDRPlay device
                                                                                6) I have not tried building a stand-alone executable yet

7) The audio is still a bit glitchy under windoz
                                                                                8) THIS IS A WORK IN PROGRESS!
                                                                               
