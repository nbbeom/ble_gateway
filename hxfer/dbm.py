import queue
import time
import threading
import uuid
from datetime import datetime

import boto3
from dynamodb_json import json_util
from loguru import logger


class DbManager():
    def __init__(self, rpi_id):
        self._dyn_resource = boto3.resource('dynamodb')
        self._table_rpi = self._dyn_resource.Table('lab_rpi')
        self._table_exp = self._dyn_resource.Table('lab_experiment')
        self._table_glu = self._dyn_resource.Table('lab_glucose')
        self._rpi_id = rpi_id
        

    def get_props(self):
        flag = self.new_rpi()
        item = self._scan_rpi(flag)


        exp_id = item[0]['experiment_id']
        try:
            exp_item = self._scan_exp(exp_id)
            exp_name = exp_item[0]['name']
        except Exception:
            exp_name = ""
        logger.debug({
            'item': item,
        })
        interval = int(item[0]['interval'])
        ble_addrs = item[0]['ble']
        rpi_name = item[0]['name']
        
        self._ble_len = len(ble_addrs)
        logger.debug({
            'rpi_name' : rpi_name,
            'interval': interval,
            'ble_addrs': ble_addrs,
            'exp_id': exp_id
        })

        return interval, ble_addrs, exp_id , rpi_name, exp_name
    

    def put_props(self, item):
        logger.debug("put_db!!!")
        self._table_glu.put_item(
            Item=item
        )

    def new_rpi(self):
        response = self._table_rpi.scan()
        items = json_util.loads(response['Items'])
        logger.debug(self._rpi_id)
        logger.debug(items)
        flag = -1
        for i in range(len(items)):
            if self._rpi_id in items[i]['rpi_id']:
                flag = i

        if flag == -1:
            item = {
                'rpi_id': self._rpi_id,
                'ble': [],
                'experiment_id': '',
                'interval': '40',
                'name': 'gateway',
            }
            logger.debug(item)

            self._table_rpi.put_item(
                Item=item
            )
        return flag

    def _scan_rpi(self, flag):
        response = self._table_rpi.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('rpi_id').
            eq(self._rpi_id) 
        )

        items = json_util.loads(response['Items'])

        logger.debug({
            'event': '_table_con.rpi',
            'response': response,
            'items': items,
        })
        return items
    def _scan_exp(self, exp_id):
        response = self._table_exp.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('experiment_id').
            eq(exp_id) 
        )

        items = json_util.loads(response['Items'])
        logger.debug(items)
        return items

class Ipc(threading.Thread):
    def __init__(self, rpi_id, ble_len, q, interval):
        threading.Thread.__init__(self)
        self._rpi_id = rpi_id
        self._ble_len = ble_len
        self._dm = DbManager(self._rpi_id)
        self._is_run = True
        self._q = q
        self._interval = interval
        self._index = 0

    def convert_db_format(self):
        items = self._q.get()
        if items:
            date = "{:%Y-%m-%d %H:%M:%S}".format(datetime.now())
            for key in items:
                item = items[key]
                logger.debug(item)
                item['timestamp'] = round(time.time()*1000)
                item['date'] = str(date)
                item['rpi_id'] = self._rpi_id
                item['index'] = self._index
                logger.debug(item)
                self._dm.put_props(item)
            

    def run(self):
        while self._is_run:
            time.sleep(self._interval)
            self.convert_db_format()
            self._index += 1


    def stop(self):
        self._is_run = False

