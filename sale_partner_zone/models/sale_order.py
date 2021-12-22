###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    zone_id = fields.Many2one(
        comodel_name='res.partner.zone',
        related='partner_id.zone_id',
        string='Zone',
        store=True,
    )
