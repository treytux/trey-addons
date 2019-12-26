# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    commercial_campaign_id = fields.Many2one(
        comodel_name='marketing.campaign',
        string='Commercial campaign')
