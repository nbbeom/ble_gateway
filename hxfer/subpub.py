import json
import queue
import re
import signal
import time
import uuid

from loguru import logger
import paho.mqtt.client as mqtt
import scann
from dbm import DbManager
from blem import BlePeripheral
from stats import DisplayOled
from dbm import Ipc

from queuemanager import QueueManager

def get_mac_addr():
    return ':'.join(re.findall('..', '%012x' % uuid.getnode()))


class BleManager():
    def __init__(self):
        self._bps = []

    def start(self):
        rasp_id = get_mac_addr()
        qm = QueueManager()

        if not rasp_id:
            return -1
        dm = DbManager(rasp_id)

        interval, ble_addrs, experiment_id, rpi_name, exp_name = dm.get_props()

        self.ipc = Ipc(get_mac_addr(), len(ble_addrs), qm, interval)

        if not experiment_id:
            return -2

        index = 0
        for ble_addr in ble_addrs:
            bp = BlePeripheral(
                            ble_addr,
                            interval,
                            experiment_id,
                            self.ipc.convert_db_format,
                            index,
                            qm,
                            )
            bp.start()
            self._bps.append(bp)
            index += 1
        self.ipc.start()
        do.run()
        logger.info(self._bps)

        return 0

    def stop(self):
        for bp in self._bps:
            bp.stop()
            bp.join()
            del bp

        self.ipc.stop()
        do.run()
        self._bps.clear()

    def get_status_list(self):
        status_list = {}
        for bp in self._bps:
            status_list.update(bp.get_status())
        return status_list


# TODO Singleton 적용
man = BleManager()
do = DisplayOled()

class MqttResponser(mqtt.Client):
    def __init__(
        self,
        url,
        port,
        dev_id,
        ca_certs,
        certfile,
        keyfile,

    ):
        mqtt.Client.__init__(self)
        self._url = url
        self._port = int(port)
        self._ca_certs = ca_certs
        self._certfile = certfile
        self._keyfile = keyfile

        self.tls_set(
            ca_certs=ca_certs,
            certfile=certfile,
            keyfile=keyfile
        )
        self.tls_insecure_set(True)

        self._sub_topic = '/dev_id/' + dev_id + '/wrs/#'
        self._pub_topic = '/dev_id/' + dev_id + '/srw/'

    def on_connect(self, mqttc, obj, flags, rc):
        logger.info({
            'event': 'on_connect',
            'rc': str(rc),
        })
        man.start()
        do.run()

    def on_disconnect(self, client, userdata, rc):
        logger.info({
            'event': 'on_disconnect',
            'userdata': userdata,
            'rc': str(rc),
        })

        # signal.signal(signal.SIGINT)

    def on_message(self, mqttc, obj, msg):
        decodemsg = msg.payload.decode()
        # logger.info({
        #     'event': 'on_message',
        #     'topic': msg.topic,
        #     'qos': str(msg.qos),
        #     'payload': decodemsg,
        # })

        if decodemsg == 'scan':
            self._scan(mqttc, msg)

        if decodemsg == 'update':
            self._update(mqttc, msg)

        if decodemsg == 'get_status':
            self._get_status(mqttc, msg)

    # def on_publish(self, mqttc, obj, mid):
    #     logger.debug({
    #         'event': 'on_publish',
    #         'mid': str(mid),
    #     })

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        logger.debug({
            'event': 'on_subscribe',
            'mid': str(mid),
            'qos': str(granted_qos),
        })

    def on_log(self, mqttc, obj, level, string):
        if level is mqtt.MQTT_LOG_ERR:
            logger.error({
                'event': 'on_log',
                'level': level,
                'string': string,
            })

    def run(self):
        try:
            self.connect(self._url, self._port)
            logger.info({
                'event': 'scan start',
            })

            self.subscribe(self._sub_topic)
            logger.info({
                'event': 'sub',
                'topic': self._sub_topic
            })

            while True:  
                self.loop(timeout=1.0)

        except Exception as e:
            logger.error({
                'event': 'mqtt.connect',
                'url': self._url,
                'port': self._port,
                'detail': e,
            })

    # XXX 시간이 오래 걸리는 작업이라 blocking ~~~ 최소 5초 이상!!!
    def _update(self, mqttc, msg):
        msg_id = msg.topic.split('/')[2]
        resmsg = {
                'status': 'update success'
        }
        logger.info(resmsg)
        mqttc.publish(self._pub_topic + msg_id, json.dumps(resmsg))
        man.stop()
        man.start()
        do.run()

    def _get_status(self, mqttc, msg): 
        msg_id = msg.topic.split('/')[2]
        resmsg = man.get_status_list()
        # logger.info(resmsg)
        mqttc.publish(self._pub_topic + msg_id, json.dumps(resmsg))

    # XXX 시간이 오래 걸리는 작업이라 blocking ~~~ 최소 2초 이상!!!
    def _scan(self, mqttc, msg):
        resmsg = scann.scan_start()
        msg_id = msg.topic.split('/')[2]
        logger.info(resmsg)
        mqttc.publish(self._pub_topic + msg_id, json.dumps(resmsg))

    def handler(signum):
        logger.info("signal")
