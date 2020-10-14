import struct
import time

from bluepy.btle import Peripheral
from boto3.dynamodb.conditions import  Attr
import boto3
import uuid

from loguru import logger

ConfigHndl = 0x000e
ConfigHnd2 = 0x0010
ConfigHnd3 = 0x00d


def startAll(beackernum):
    dyn_resource = boto3.resource('dynamodb')
    table = dyn_resource.Table('uxn_lab_connect')

    response = table.scan(
        FilterExpression=Attr('beacker').eq(beackernum)
    )
    items = response['Items']
    items = items[0]
    if items['in_experiment'] == True:
        set_all_interval(items['mac'], int(items['interval']))

    else:
        logger.debug(items)


def set_all_interval(item_list, interval):
    try:
        p = []
        p[0] = Peripheral()
        p[0] = p[0].connect(item_list[0])

        logger.info({
            'object': 'ble',
            'event': 'connected',
            'details': {
                'mac': item_list[0],
            }})
    except Exception as e:
        logger.exception(e)

    print("connected")
    p.writeCharacteristic(ConfigHndl, bytearray.fromhex('01 00'))
    set_all_interval(p, interval)

    while True:
        data = p[0].readCharacteristic(ConfigHnd3)

        print({
            'device': item_list[i],
            'len': len(data),
            'data': [hex(x) for x in data],
        })

        if data[0] == 0xfd:
            if data[1] == 0x00 and data[2] == 0xff:
                def set_interval_secs(secs):
                    return p[0].writeCharacteristic(
                        ConfigHnd2,
                        bytearray.fromhex(f'fd 02 00 {secs:02x} ff'),
                    )
                set_interval_secs(interval)

            # Timing Interval ACK
        if data[1] == 0x02 and data[4] == 0xfe:
            p.writeCharacteristic(ConfigHnd2, b"\xfd\x00\xfd")

        if data[0] == 0xf9:
            hexdata = [int(x) for x in data]
            hexdata1 = hexdata[2:6]
            hexdata2 = hexdata[6:10]

            chanel1 = bytearray(hexdata1)
            chanel2 = bytearray(hexdata2)
            chanel1 = struct.unpack('<f', chanel1)
            chanel2 = struct.unpack('<f', chanel2)
            chanel3 = chanel1[0] - chanel2[0]

            put_dynamo(str(chanel1[0]), str(chanel2[0]), str(chanel3), item_list[i])


def put_dynamo(ch1, ch2, ch3, mac):
    uuid2 = str(uuid.uuid1())
    dyn_resource = boto3.resource('dynamodb')
    table = dyn_resource.Table('uxn_lab_glucose')
    table.put_item(

        Item={
            'uuid': uuid2,
            'ch1': ch1,
            'ch2': ch2,
            'ch3': ch3,
            'mac': mac,
            'beaker': 1,
            'time': time.ctime(time.time()),
        }
    )


startAll(1)