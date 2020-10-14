import queue
import struct
import threading
import time

from bluepy.btle import BTLEException
from bluepy.btle import Peripheral
from bluepy.btle import DefaultDelegate
from loguru import logger

from queuemanager import QueueManager
CONFIG_HND1 = 0x000e
CONFIG_HND2 = 0x0010
CONFIG_HND3 = 0x000d

class MyDelegate(DefaultDelegate):
    def __init__(
                self,
                peripheral,
                interval,
                ble_addr,
                experiment_id,
                publish,
                index,
                qm,
                ):
        DefaultDelegate.__init__(self)
        self._peripheral = peripheral
        self._interval_secs = interval
        self._ble_addr = ble_addr
        self._experiment_id = experiment_id
        self._publish = publish
        self._set_interval_done = False
        self._q = queue.Queue(1)
        self.lock = threading.Lock()
        self.index = index
        self._qm = qm

    def handleNotification(self, cHandle, data):
        logger.debug({
            'ble_Addr': self._ble_addr,
            'cHandle': cHandle,
            'data': data,
        })
        
        if data == b'\xfd\x00\xff' and self._set_interval_done == False:

            self._set_interval()

            # logger.debug({
            #     'event': 'interval',
            #     'write_data': write_data,
            #     'detail': 'set interval',
            #     # 'status': status,
            # })

            self._set_interval_done = True
            return

        if data == b'\xfd\x00\xff' and self._set_interval_done == True:


            # logger.debug({
            #     'event': 'nack!!!',
            #     'write_data': write_data,
            # })

            self._nack_timeing_interval()
            self._set_interval_done = False
            return

        if data == bytearray.fromhex(f'fd 02 00 {self._interval_secs:02x} fe'):
            self._ack_timeing_interval()

            # logger.debug({
            #     'event': 'ack!!!',
            #     'write_data': write_data,
            # })
            return


        if data[0] == 0xf9:
            ch1, ch2, ch3 = self._convert_glucose(data)
            items = {
                    'ch1': ch1,
                    'ch2': ch2,
                    'ch3': ch3,
                    'ble_name': self._ble_addr['name'],
                    'ble_mac': self._ble_addr['mac'],
                    'experiment_id': self._experiment_id,
                }
            logger.debug({
                'event': 'put',
                'value': items,
            })
            self._qm.put(self.index, items)



    def _set_interval(self):
        logger.info({
            'mac_addr': self._ble_addr,
            'interval_secs': self._interval_secs,
        })

        return self._peripheral.writeCharacteristic(
            CONFIG_HND2,
            bytearray.fromhex(
                f'fd 02 00 {self._interval_secs:02x} ff',
            ),
        )

    def _nack_timeing_interval(self):
        logger.info({
            'mac_addr': self._ble_addr,
        })

        return self._peripheral.writeCharacteristic(
            CONFIG_HND2,
            bytearray.fromhex('ff 01 fd ff'),
        )

    def _ack_timeing_interval(self):
        logger.info({
            'mac_addr': self._ble_addr,
        })

        return self._peripheral.writeCharacteristic(
            CONFIG_HND2,
            bytearray.fromhex('fd 00 fd'),
        )
    
    def _convert_glucose(self, data):
        hexdata = [int(x) for x in data]
        hexdata1 = hexdata[2:6]
        hexdata2 = hexdata[6:10]

        channel1 = bytearray(hexdata1)
        channel2 = bytearray(hexdata2)
        channel1 = struct.unpack('<f', channel1)
        channel2 = struct.unpack('<f', channel2)
        channel3 = channel1[0] - channel2[0]

        return str(channel1[0]), str(channel2[0]), str(channel3)



class BlePeripheral(threading.Thread):
    def __init__(
        self,
        ble_addr,
        interval_secs,
        experiment_id,
        publish,
        index,
        qm,
        ):
        threading.Thread.__init__(self)
        self._per = Peripheral()
        self._is_run = True
        self._ble_addr = ble_addr
        self._interval_secs = interval_secs
        self._publish = publish
        self._experiment_id = experiment_id
        self._flag = 0
        self._index= index
        self._qm = qm
        

# XXX 
    def _connect(self):
        # logger.debug({
        #     'mac_addr': self._ble_addr['mac'],
        # })

        try:
            self._per.connect(self._ble_addr['mac'])
            self._per.withDelegate(
                                    MyDelegate(
                                            self._per,
                                            self._interval_secs,
                                            self._ble_addr,
                                            self._experiment_id,
                                            self._publish,
                                            self._index,
                                            self._qm,
                                            )
                                    )

        except Exception as e:
            logger.exception(e)

    def _set_notify(self):

        return self._per.writeCharacteristic(
            CONFIG_HND1,
            bytearray.fromhex('01 00'),
        )


    def get_status(self):
        return {self._ble_addr['mac']: self._is_run}

    def run(self):
        while self._is_run:
            try:
                self._connect()
                self._set_notify()

                while self._is_run:
                    if self._per.waitForNotifications(1.0):
                        continue
        
            except BTLEException as e:
                logger.exception(e)

            # finally:
            #     time.sleep(1)

    def stop(self):
        self._is_run = False


