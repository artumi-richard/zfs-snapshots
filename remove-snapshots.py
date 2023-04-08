import json
import subprocess
import os
from datetime import datetime
from collections import namedtuple

max_hourly_snapshots = 12
max_daily_snapshots = 10
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

def remove_devices_snapshots(devices):
    for device in devices:
        snapshots = get_device_snapshots(device);
        if not len(snapshots):
            continue
        hourly_snapshots = get_hourly_snapshots(snapshots);
        remove_snapshots_fromlist(hourly_snapshots, max_hourly_snapshots);
        daily_snapshots = get_daily_snapshots(snapshots);
        remove_snapshots_fromlist(daily_snapshots, max_daily_snapshots);

def get_device_snapshots(device):
    result = []
    snapshots=subprocess.Popen('zfs list -t snapshot | grep '+device.device+'@snap', shell=True, stdout=subprocess.PIPE)
    snapshotsout, err = snapshots.communicate()
    lines =  snapshotsout.split("\n");
    for line in lines:
        cells = line.split()
        if len(cells):
            result.append(cells[0])
    return result;

def is_7am_snapshot(snapName):
    return snapName[-3:] == '-07'

def get_hourly_snapshots(snapshots):
    result = []
    for snapName in snapshots:
        if not is_7am_snapshot(snapName) :
            result.append(snapName)
    return result

def get_daily_snapshots(snapshots):
    result = []
    for snapName in snapshots:
        if is_7am_snapshot(snapName) :
            result.append(snapName)
    return result

def remove_snapshots_fromlist(snapshotNames, limit):
    toRemove = snapshotNames[:-limit]
    for snapName in toRemove:
        remove_snapshot(snapName)

def remove_snapshot(snapName):
    snapshots=subprocess.Popen('zfs destroy '+snapName, shell=True, stdout=subprocess.PIPE)
    snapshotsout, err = snapshots.communicate()
    return snapshotsout, err

for poolname in listOfZFSPools:
    devices = mounted_physical_devices()
    poolDevices = pool_devices(poolname, devices)
    if len(poolDevices):
        remove_devices_snapshots(poolDevices)
