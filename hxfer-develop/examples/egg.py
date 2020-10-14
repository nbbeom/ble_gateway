from loguru import logger
import paho.mqtt.client as mqtt
from enum import Enum
import json
import time
import ast
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ValidationError
from starlette.middleware.cors import CORSMiddleware
from starlette.status import (
    HTTP_200_OK, HTTP_201_CREATED, HTTP_202_ACCEPTED,
    HTTP_404_NOT_FOUND, HTTP_409_CONFLICT)


app = FastAPI()

MQTT_KEEP_ALIVE = 5


class MqttRequester(mqtt.Client):
    def __init__(
        self,
        url,
        port,
        dev_id,
    ):
        mqtt.Client.__init__(self)
        self._url = url
        self._port = port
        self._sub_topic = dev_id + '/srw/#'
        self._pub_topic = dev_id + '/wrs/'
        self.data =[]
        self.connect('localhost', self._port, MQTT_KEEP_ALIVE)
        self.loop_start()

    def on_connect(self, mqttc, obj, flags, rc):
        logger.info({
            'event': 'on_connect',
            'rc': str(rc),
        })

    def on_disconnect(self, client, userdata, rc):
        logger.info({
            'event': 'on_disconnect',
            'userdata': userdata,
            'rc': str(rc),
        })

    def on_message(self, mqttc, obj, msg):
        logger.info({
            'event': 'on_message',
            'topic': msg.topic,
            'qos': str(msg.qos),
            'payload': msg.payload.decode(),
        })
        x= ast.literal_eval(msg.payload.decode())
        self.data.append(x)

    def on_publish(self, mqttc, obj, mid):
        logger.debug({
            'event': 'on_publish',
            'mid': str(mid),
        })

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

    def run(self, pub):
        msg_id = str(time.time())

        self.subscribe(self._sub_topic)
        self.publish(self._pub_topic, pub)

        try:
            time.sleep(7)
            get_data = self.data
            resmsg = {
                'msg_id': msg_id,
                'resmsg': get_data[0],
            }
            logger.debug({
                'msg_id': msg_id,
                'resmsg': get_data[0],
            })
            return resmsg

        except Exception as e:
            logger.warning({
                'title': 'mqtt',
                'action': 'timeout',
            })
            raise e

        finally:
            self.disconnect()


@app.get(
    '/devices')
def get_device(dev_id: str):
    resmsg = None

    try:
        logger.info({
            'method': 'GET',
            'dev-id': dev_id,
        })

        mr = MqttRequester(
            'localhost',
            1883,
            dev_id,
        )

        ad = mr.run("scan")
        return ad

    except ValidationError as e:
        logger.exception(e.json())


    if resmsg.status_code == HTTP_200_OK:
        return resmsg.body

    raise HTTPException(
        status_code=resmsg.status_code,
        detail=resmsg.body)

@app.post(
    '/connect_ble',
    )
def get_device(dev_id: str):
    resmsg = None

    try:
        logger.info({
            'method': 'GET',
            'dev-id': dev_id,
        })

        mr = MqttRequester(
            'localhost',
            1883,
            dev_id,
        )

        ad = mr.run("connect")
        return ad

    except ValidationError as e:
        logger.exception(e.json())


    if resmsg.status_code == HTTP_200_OK:
        return resmsg.body

    raise HTTPException(
        status_code=resmsg.status_code,
        detail=resmsg.body)
