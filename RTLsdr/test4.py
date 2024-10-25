#! /usr/bin/python3 -u

# Simple esample taken from librtlsdr website.
# Open RTL device and use async i/o to read some samples.

import asyncio
from rtlsdr import RtlSdr

async def streaming():

    async for samples in sdr.stream():
        print(samples,len(samples))

sdr = RtlSdr()
    
loop = asyncio.get_event_loop()
loop.run_until_complete(streaming())

# to stop streaming:
sdr.stop()

# done
sdr.close()

