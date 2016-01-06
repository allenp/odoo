# -*- coding: utf-8 -*-
import logging

from scale.scale import Scale

import openerp
import openerp.addons.hw_proxy.controllers.main as hw_proxy
from openerp import http
from openerp.http import request
from openerp.tools.translate import _


_logger = logging.getLogger(__name__)

usb_scale = Scale()
hw_proxy.drivers['scale'] = usb_scale

class ScaleDriver(hw_proxy.Proxy):
    @http.route('/hw_proxy/scale_read/', type='json', auth='none', cors='*')
    def scale_read(self):
        if usb_scale:
          reading = usb_scale.weigh()
          return { 'weight': reading.weight, 'unit': reading.unit, 'info': reading.status }
        return None

    @http.route('/hw_proxy/scale_zero/', type='json', auth='none', cors='*')
    def scale_zero(self):
        return True

    @http.route('/hw_proxy/scale_tare/', type='json', auth='none', cors='*')
    def scale_tare(self):
        return True

    @http.route('/hw_proxy/scale_clear_tare/', type='json', auth='none', cors='*')
    def scale_clear_tare(self):
        return True

