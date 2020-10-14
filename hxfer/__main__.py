import os
import pprint
import re
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


if __name__ == '__main__':
    logger.debug(pprint.pformat(os.environ.copy()))
    main()
