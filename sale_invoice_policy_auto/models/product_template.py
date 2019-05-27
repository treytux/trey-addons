###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    invoice_policy = fields.Selection(
        compute='_compute_invoice_policy')

    @api.one
    @api.depends('type')
    def _compute_invoice_policy(self):
        if self.type == 'product':
            self.invoice_policy = 'delivery'
        else:
            self.invoice_policy = 'order'
