import json
import subprocess
import os
from datetime import datetime
from collections import namedtuple

_ntuple_diskusage = namedtuple('diskusage',['device','size','used','free','percentage','mount']);

listOfZFSPools=['tank'];

def mounted_devices():
    listdrives=subprocess.Popen('df', shell=True, stdout=subprocess.PIPE)
    listdrivesout, err = listdrives.communicate()
    lines =  listdrivesout.split("\n");
    # first line is a header
    lines.pop();
    result = []
    for line in lines:
        cells = line.split()
        if len(cells) ==6:
            result.append(_ntuple_diskusage(cells[0], cells[1], cells[2], cells[3], cells[4], cells[5]))
    return result

def mounted_physical_devices():
    devices = mounted_devices();
    result = []
    for device in devices:
        if device.device == 'tmpfs':
            continue
        if device.device == 'None':
            continue
        if device.device == 'udev':
            continue
        if device.device[0:9] == '/dev/loop':
            continue
        result.append(device);
    return result

def pool_devices(poolname, devices):
    if len(poolname)==0:
        return []
    result = []
    for device in devices:
        if device.device[0:len(poolname)+1] == poolname+'/':
            result.append(device);
    return result

def make_snapshots(devices):
    date = datetime.now().strftime('%Y%m%d-%H')
    for device in devices:
        snap=subprocess.Popen('zfs snapshot -r '+device.device+'@snap'+date, shell=True, stdout=subprocess.PIPE)
        snapout, err = snap.communicate()


devices = mounted_physical_devices()
for poolname in listOfZFSPools:
    poolDevices = pool_devices(poolname, devices)
    if len(poolDevices):
        make_snapshots(poolDevices)

