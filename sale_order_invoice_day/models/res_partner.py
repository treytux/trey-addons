###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sale_invoice_day_id = fields.Many2one(
        comodel_name='res.partner.invoice_day',
        string='Invoicing day',
    )
