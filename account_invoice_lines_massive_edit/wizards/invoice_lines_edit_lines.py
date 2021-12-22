###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class InvoiceLinesEditLines(models.TransientModel):
    _name = 'invoice.lines.edit.lines'
    _description = 'Invoice lines edit, lines'

    wizard_id = fields.Many2one(
        comodel_name='invoice.lines.edit',
        string='Wizard',
    )
    line_id = fields.Many2one(
        comodel_name='account.invoice.line',
        string='Invoice line',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
    )
    quantity = fields.Float()
    price_unit = fields.Float()
    discount = fields.Float()
