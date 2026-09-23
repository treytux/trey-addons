# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
###############################################################################
from openerp import models, fields


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist',
    )
