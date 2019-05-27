# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    group_collect_by_partner = fields.Boolean(
        string='Group collect by partner')
