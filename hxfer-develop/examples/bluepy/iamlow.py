import os
import pprint
import re
import time
import uuid

from loguru import logger

from __init__ import __version__
from subpub import MqttResponser


def get_mac_addr():
    return ':'.join(re.findall('..', '%012x' % uuid.getnode()))


def main():
    logger.critical({
        'event': 'launch',
        'service': 'hxfer',
        'version': __version__,
    })

    # TODO 기기 시작시 DB에 넣기 없으면,
    dev_id = get_mac_addr()

    mqtt_port = os.getenv('HOBS_MQTT_PORT')
    mqtt_host = os.getenv('HOBS_MQTT_HOST')
    ca_certs = os.getenv('HOBS_CA_CERTS')
    certifile = os.getenv('HOBS_CERTFILE')
    keyfile = os.getenv('HOBS_KEYFILE')

    MqttResponser(  # run 중
        mqtt_host,
        mqtt_port,
        dev_id,
        ca_certs,
        certifile,
        keyfile,
    ).run()

    logger.critical({
        'event': 'terminate',
        'service': 'hxfer',
        'version': __version__,
    })


import bluepy.btle as btle


BLE_MAC = '5C:F2:86:40:46:1A'

CONFIG_HND1 = 0x000e
CONFIG_HND2 = 0x0010
CONFIG_HND3 = 0x000d


class MyDelegate(btle.DefaultDelegate):
    def __init__(self, params):
        btle.DefaultDelegate.__init__(self)
        self._p = params
        # ... initialise here
        logger.debug('')
        self._set_interval_done = False

    def handleNotification(self, cHandle, data):
        # ... perhaps check cHandle
        # ... process 'data'
        logger.debug({
            'event': 'READ',
            'cHandle': cHandle,
            'data': data,
            '_set_interval_done': self._set_interval_done,
        })

        if data == b'\xfd\x00\xff' and self._set_interval_done == False:
            # set interval
            write_data = b'\xfd\x02\x00\x10\xff' # bytearray.fromhex('fd 02 00 0a ff')
            self._p.writeCharacteristic(
                CONFIG_HND2,
                write_data,
            )

            logger.debug({
                'event': 'interval',
                'write_data': write_data,
                'detail': 'set interval',
                # 'status': status,
            })

            self._set_interval_done = True
            return

        if data == b'\xfd\x00\xff' and self._set_interval_done == True:
            # nack ff01fdff
            write_data = b'\xff\x01\xfd\xff'
            self._p.writeCharacteristic(
                CONFIG_HND2,
                write_data,
            )

            logger.debug({
                'event': 'nack!!!',
                'write_data': write_data,
            })

            # self._set_interval_done = False
            return

        if data == b'\xfd\x02\x00\x10\xfe':
            write_data = bytearray.fromhex('fd 00 fd')
            self._p.writeCharacteristic(
                CONFIG_HND2,
                write_data,
            )
            logger.debug({
                'event': 'ack!!!',
                'write_data': write_data,
            })
            return


def main2():
    try:
        logger.debug('Start!!')
        p = btle.Peripheral()
        p.connect(BLE_MAC)
        # time.sleep(5)
        p.withDelegate(MyDelegate(p))

        # status = 1

        # set notify
        write_data = bytearray.fromhex('01 00')
        logger.debug({
            'event': 'write',
            'write_data': write_data,
            'detail': 'set notify and start notify event!!!',
            # 'status': status,
        })

        p.writeCharacteristic(
            CONFIG_HND1,
            write_data,
            withResponse=True,
        )

        # # set interval
        # write_data = bytearray.fromhex('fd 02 00 05 ff')
        # logger.debug({
        #     'event': 'write',
        #     'write_data': write_data,
        #     'detail': 'set interval',
        #     # 'status': status,
        # })

        # p.writeCharacteristic(
        #     CONFIG_HND2,
        #     write_data,
        # )

        while True:
            if p.waitForNotifications(1.0):
                continue

    except Exception as e:
        logger.exception(e)


if __name__ == '__main__':
    logger.debug(pprint.pformat(os.environ.copy()))
    main2()
    # main()
