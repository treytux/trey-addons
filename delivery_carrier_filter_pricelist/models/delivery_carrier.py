###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist')
