###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class SaleOrderTemplate(models.Model):
    _inherit = 'sale.order.template'

    title = fields.Text(
        string='Title',
        translate=True,
    )
    header_note = fields.Text(
        string='Header note',
        translate=True,
    )
