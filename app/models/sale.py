# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, _
import logging
_log = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create_order(self, order_data):
        '''Create a order with data dictionary given as a parameter.'''
        if 'partner_id' not in order_data:
            _log.warning(_('Field partner_id is required!'))
            return None
        elif 'partner_invoice_id' not in order_data:
            _log.warning(_(
                'Field partner_invoice_id is required!'))
            return None
        elif 'partner_shipping_id' not in order_data:
            _log.warning(_(
                'Field partner_shipping_id is required!'))
            return None
        elif 'warehouse_id' not in order_data:
            _log.warning(_(
                'Field warehouse_id is required!'))
            return None
        return self.env['sale.order'].create(order_data)
