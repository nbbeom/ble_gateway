import re
import socket
import subprocess
import time
import uuid

import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
from dbm import DbManager

i2c = busio.I2C(board.SCL, board.SDA)
disp = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
disp.fill(0)
disp.show()
width = disp.width
height = disp.height
image = Image.new("1", (width, height))
draw = ImageDraw.Draw(image)
draw.rectangle((0, 0, width, height), outline=0, fill=0)
padding = -2
top = padding
bottom = height - padding
x = 0
font = ImageFont.load_default()

# XXX IP 가져오는거 해결해야함. 
class DisplayOled():
    def __init__(self):
        self._dev_id = self.get_mac_addr()
        self.dm = DbManager(self._dev_id)
        self._is_run = True

    def get_mac_addr(self):
        return ':'.join(re.findall('..', '%012x' % uuid.getnode()))

    def get_ip_status(self):
        testIP = "8.8.8.8"
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((testIP, 0))
        ipaddr = s.getsockname()[0]
        return ipaddr

    def draw_text(self, ip, dev_id, rpi_name):
        draw.text((x, top + 0), "IP: " + ip, font=font, fill=255)
        draw.text((x, top + 8), "DEV:" + self.rpi_name, font=font, fill=255)
        draw.text((x, top + 16), "EXP: " + str(self.exp_name), font=font, fill=255)
        draw.text((x, top + 25), "CONNECTED BLE:"+ str(self._bles), font=font, fill=255)

    def display_status(self):
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
        ip = self.get_ip_status()
        dev_id = self._dev_id
        rpi_name = self.rpi_name
        self.draw_text(ip, dev_id, rpi_name)

        disp.image(image)
        disp.show()

    def run(self):
        self.interval, self.ble_addrs, self.experiment_id, self.rpi_name, self.exp_name = self.dm.get_props()
        if self.exp_name == '' :
            self._bles = '0'
        else :
            self._bles = len(self.ble_addrs)
        self.display_status()
        time.sleep(1)

    def stop(self):
        self._is_run = False

