import os
from bluepy.btle import Scanner, DefaultDelegate
from loguru import logger


ble_scan_timeout = float(os.getenv('HOBS_BLE_SCAN_TIMEOUT', 3.0))
ble_filter2 = '0000fff0-0000-1000-8000-00805f9b34fb'


class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)


def scan_start():
    device = []
    scanner = Scanner().withDelegate(ScanDelegate())
    devices = scanner.scan(ble_scan_timeout)
    for dev in devices:
        for (adtype, desc, value) in dev.getScanData():
            if desc == "Complete 16b Services" and value == ble_filter2:
                for (adtype, desc, value) in dev.getScanData():
                    if desc == "Complete Local Name":
                        device.append({
                            'name': value,
                            'mac': dev.addr,
                        })

    device_info = {
        'bles': device,
    }

    logger.debug(device_info)

    return device_info
