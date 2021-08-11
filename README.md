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
                                                                                
