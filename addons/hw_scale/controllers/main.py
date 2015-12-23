# -*- coding: utf-8 -*-
import logging
import os
import time
from os.path import join
from threading import Thread, Lock
from select import select
from Queue import Queue, Empty

import openerp
import openerp.addons.hw_proxy.controllers.main as hw_proxy
from openerp import http
from openerp.http import request
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)

VENDOR_ID = 0x0922
PRODUCT_ID = 0x8003
DATA_MODE_GRAMS = 2
DATA_MODE_OUNCES = 11

try:
    import usb.core as usbcore;
    import usb.util
    usbcore = True
except ImportError:
    _logger.error('Odoo module hw_scale_usb depends on the usb.core and usb.util modules')
    usbcore = False


class UsbScale(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.lock = Lock()
        self.scalelock = Lock()
        self.status = {'status':'connecting', 'messages':[]}
        self.weight = 0
        self.weight_info = 'ok'
        self.device = None

    def lockedstart(self):
        with self.lock:
            if not self.isAlive():
                self.daemon = True
                self.start()

    def set_status(self, status, message = None):
        if status == self.status['status']:
            if message != None and message != self.status['messages'][-1]:
                self.status['messages'].append(message)

                if status == 'error' and message:
                    _logger.error('Scale Error: '+message)
                elif status == 'disconnected' and message:
                    _logger.warning('Disconnected Scale: '+message)
        else:
            self.status['status'] = status
            if message:
                self.status['messages'] = [message]
            else:
                self.status['messages'] = []

            if status == 'error' and message:
                _logger.error('Scale Error: '+message)
            elif status == 'disconnected' and message:
                _logger.warning('Disconnected Scale: %s', message)

    def get_device(self):
        try:
            device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
            device.set_configuration()
            self.set_status('connected','Connected to '+ 'Device name here')
            return device
        except Exception as e:
            self.set_status('error',str(e))
            return None

    def get_weight(self):
        self.lockedstart()
        return self.weight

    def get_weight_info(self):
        self.lockedstart()
        return self.weight_info

    def get_status(self):
        self.lockedstart()
        return self.status

    def read_weight(self):
        with self.scalelock:
            if self.device:
                try:
                  endpoint = self.device[0][(0,0)][0]
                  preload = 3
                  while preload > 0:
                    device.read(endpoint.bEndpointAddress,
                                endpoint.wMaxPacketSize)
                    preload -= 1

                    attempts = 10
                    data = None
                    while data is None and attemps > 0:
                      try:
                        data = device.read(endpoint.bEndpointAddress,
                                            endpoint.wMaxPacketSize)
                      except usb.core.USBError as e:
                        data = None
                        if e.args == ('Operation timed out',):
                          attempts -= 10
                          continue

                    raw_weight = data[4] + data[5] * 256
                    if data[2] == DATA_MODE_OUNCES:
                      ounces = raw_weight * 0.1
                      weight = ounces
                    elif data[2] == DATA_MODE_GRAMS:
                      grams = raw_weight
                      weight = grams * .035274
                      return weight
                except Exception as e:
                    self.set_status('error',str(e))
                    self.device = None

    def set_zero(self):
        with self.scalelock:
            if self.device:
                try:
                  print('Not implemented')
                except Exception as e:
                    self.set_status('error',str(e))
                    self.device = None

    def set_tare(self):
        with self.scalelock:
            if self.device:
                try:
                  print('Not implemented')
                except Exception as e:
                    self.set_status('error',str(e))
                    self.device = None

    def clear_tare(self):
        with self.scalelock:
            if self.device:
                try:
                  print('Not implemented')
                except Exception as e:
                    self.set_status('error',str(e))
                    self.device = None

    def run(self):
        self.device = None

        while True:
            if self.device:
                self.read_weight()
                time.sleep(0.3)
            else:
                with self.scalelock:
                    self.device = self.get_device()
                if not self.device:
                    time.sleep(5)

scale_thread = None

if usbcore:
    scale_thread = UsbScale()
    hw_proxy.drivers['scale'] = scale_thread

class ScaleDriver(hw_proxy.Proxy):
    @http.route('/hw_proxy/scale_read/', type='json', auth='none', cors='*')
    def scale_read(self):
        if scale_thread:
            return {'weight': scale_thread.get_weight(), 'unit':'kg', 'info': scale_thread.get_weight_info()}
        return None

    @http.route('/hw_proxy/scale_zero/', type='json', auth='none', cors='*')
    def scale_zero(self):
        if scale_thread:
            scale_thread.set_zero()
        return True

    @http.route('/hw_proxy/scale_tare/', type='json', auth='none', cors='*')
    def scale_tare(self):
        if scale_thread:
            scale_thread.set_tare()
        return True

    @http.route('/hw_proxy/scale_clear_tare/', type='json', auth='none', cors='*')
    def scale_clear_tare(self):
        if scale_thread:
            scale_thread.clear_tare()
        return True

