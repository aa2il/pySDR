# Software Defined Receiver

A complete SDR written in Python.  Supports both SDR Play RSP and RTL Dongle via Soapy SDR.  Can be used as stand alone or as a pan adaptor.  Rig interfacing accomplished via direct connection, flrig, fldigi or hamlib.

![Waterfall]( Docs/waterfall.png)
![Screen Shot]( Docs/pysdr.png)

Background

A few years ago, I purchased an RTL dongle as a curiosity and shortly there after, I purchased an SDRplay RSP2.  Having spent my entire professional career working in signal procesing R&D (including SDR), I was quite interested in how well such inexpensive devices performed and how to program them.  Needless to say, I was pleasently surprised to find out that what use to take room full of specialized equipment when I started my career some 35-years ago can now be accomplished with one of these device connected to a laptop or even a Raspberry Pi - and with superior performance!

There are number of very good SDR applications available for these devices, both for Windoze and Linux.  The intent of this project is not to replicate or compete with these.  Rather, it is to 1) demonstrate that high-fidelity processing can be done on modest hardware using code entirely written in Python and 2) develop an application that is closely integrated with the equipment in my "ham shack."  To this end, only devices/equipment that I own or have ready access to are supported.  However, it is believed that additional 1) SDR devices can be supported as SoapySDR is used for all low-level device i/o and 2) tranceivers can be used as flrig or hamlib can be selected for the i/o for these device.

Features

This project initially started out as a simple demodulator for broadcast AM radio.  The remminants of this are found in the file am.py.  As the effort progress, a gui and graphics were added as well as different demodulation techniques, processing schemes and other capabilities.  In its current form, this project support the following features:

- Written entirely in Python, developed under recent version of Linux Mint, use readiliy avaible libraries
- Use with SDRPlay RSP2 and RTL Dongle
- Uses SoapySDR for low-level control and I/o to SDR device
- All the configuration of the SDR device can be controlled via GUI or commandline parameters
- All significant processing parameters (e.g. center frequencies, demodulator type, filter bandwidths, etc.) can be controlled via command-line arguements thereby facilitating easy scripting
- Demodulators for AM, narrowband FM, Upper and Lower Sideband, CW, and IQ basebanding.  A preliminary demodulator for wideband stereo FM is also included but has not been refined as I generally do not listen to very much commercial FM radio (too many commercials!).
- Adjustable filter and processing bandwidths and sampling rates
- GUI resembles old-style push-button radio rather than a graphics-intensive interfaces common with most SDR programs.  This is to minimize impact on the CPU.  While not refined, spectral plots, waterfalls, etc. are avaiable via a mouse-click when desired.
- Up to four independent receivers can be tuned to anywhere within the SDR device instantaneous bandwidth (~8-MHz for SDRPlay and ~2-MHz for RTL Dongle).
- Demodulated audio can be routed to a physical device (e.g. computer speakers) or loopback sound device (e.g. to pipe to another application)
- Can be closely integrated with several ham rigs including the Yaesu FTdx3000 and FT991a, ICOM 706 and 9700 and Kenwood TS850.
- Rig communication can be via either direct USB connection, flrig, fldigi, or hamlib.

To be continued....
                                                                                
# Installation under Linux:

1) Uses python3 and pyqt5
2) Clone gitub pySDR, libs and data repositories
    - cd
    - mkdir Python
    - cd Python
    - git clone https://github.com/aa2il/pySDR
    - git clone https://github.com/aa2il/libs
    - git clone https://github.com/aa2il/data
3) Build components that deal with the SDR device:    
    - cd ~/Python/pySDR
    - BUILD_Soapy
    - BUILD_RTL
    - BUILD_SDRplay
4) Install packages needed for pySDR:
   - cd ~/Python/pySDR
   - pip3 install -r requirements.txt
5) Make sure its executable:
   - chmod +x pySDR.py start start_cw
6) Set PYTHON PATH so os can find libraries:
   - Under tcsh:      setenv PYTHONPATH $HOME/Python/libs
   - Under bash:      export PYTHONPATH="$HOME/Python/libs"
7) Bombs away:
   - ./pySDR.py

# Installation under Mini-conda:

   As of Python 3.12, there are a lot more restrictions imposed on using pip,
   to the point where it is becoming difficult to get things going.  Perhaps
   its time to start migrating toward a "sandbox."
   
0) Good video:  https://www.youtube.com/watch?v=23aQdrS58e0&t=552s

1) Miniconda homepage: https://docs.conda.io/en/latest/miniconda.html

   - google-chrome-stable https://docs.conda.io/en/latest/miniconda.html
      
2) Download and install latest & greatest Mini-conda for your particular OS:

   - I used the bash installer for linux
   - As of July 2023: Conda 23.5.2 Python 3.11.3 released July 13, 2023
   - As of Aug 2024:  Conda 24.7.1 Python 3.12.4 released Aug 22, 2024
   
   - mkdir -p ~/miniconda3
   - cd ~/miniconda3
   - wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O 
   - bash ~/miniconda3/Miniconda3-latest-Linux-x86_64.sh -b -u -p ~/miniconda3
   - rm ~/miniconda3/Miniconda3-latest-Linux-x86_64.sh

   - Follow the prompts

   - If you'd prefer that conda's base environment not be activated on startup, 
      set the auto_activate_base parameter to false: 

      conda config --set auto_activate_base false

   - To get it to work under tcsh:
       - cd    
       - bash
       - conda init tcsh
       - This creates ~/.tcshrc - move its contents to .cshrc if need be
       - relaunch tcsh and all should be fine!
       - Test with:
           - conda list

3) Create a working enviroment for ham radio stuff:

     !!! These instructions will be cleaned-up when the migration to miniconda
         is complete !!!!!!!
     
     !!! As of July 2023, the conda libraries for the SDR device were not
         completely up to date to need to use python 3.10 !!!
   - conda create --name aa2il_10 python=3.10

                   or 
   
     !!! As of Aug 2024, it seems that these libraries have caught up -
         Code has been migrated to Python 3.12 and QT 6 but not thoroughly tested...
   - conda create --name aa2il_12 python=3.12

     !!! By default, conda does not include very many fonts for tk and therefore the
         tk guis look like crap.  Do this when creating the sandbox to avoid this:

   - conda create -y --prefix "aa2il" -c conda-forge "python==3.12.*" "tk[build=xft_*]"

     Existing sandboxes can be upgraded via 

   - conda install --prefix "aa2il" -c conda-forge "tk=*=xft_* "
 
     although there may be downgrades some of the packages - who cares!  
         
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
        
4) Clone gitub pySDR, libs and data repositories:
    - cd
    - mkdir Python
    - cd Python
    - git clone https://github.com/aa2il/pySDR
    - git clone https://github.com/aa2il/libs
    - git clone https://github.com/aa2il/data

5) Install packages needed by pySDR:
   - cd ~/Python/pySDR
   - conda activate aa2il
   - pip3 install -r requirements.txt

   From conda repository - this only gives us the RTL dongle:
   - conda install -c conda-forge soapysdr
   - conda install -c conda-forge soapysdr-module-rtlsdr

   or from local build (see Installation under Linux, step 3 above) - this gives both RTL dongle and sdrplay:
   cp ~/Dev/SoapySDR/build/swig/python/SoapySDR.py ~/miniconda3/envs/aa2il_12/lib/python3.12/site-packages
   cp ~/Dev/SoapySDR/build/swig/python/_SoapySDR.so ~/miniconda3/envs/aa2il_12/lib/python3.12/site-packages
   
6) Need to "blacklist" the RTL Dongle:

      sudo ln -s /home/joea/miniconda3/envs/aa2il_2/lib/udev/rules.d/rtl-sdr.rules /etc/udev/rules.d/
      sudo udevadm control --reload && sudo udevadm trigger

7) Set PYTHON PATH so os can find libraries:
   - Under tcsh:      setenv PYTHONPATH $HOME/Python/libs
   - Under bash:      export PYTHONPATH="$HOME/Python/libs"

8) To run pySDR, we need to specify python interpreter so it doesn't run in
   the default system environment:
   - cd ~/Python/pySDR
   - conda activate aa2il
   - python pySDR.py

9) Known issues using this (as of Aug 2024):
   - None (but not rigorously tested either!)

# Installation for Windoz:

1) Best bet is to use mini-conda and follow the instructions above.
2) I have not had success building an executable for windoz.
