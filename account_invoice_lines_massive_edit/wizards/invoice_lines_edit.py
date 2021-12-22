###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class InvoiceLinesEdit(models.TransientModel):
    _name = 'invoice.lines.edit'
    _description = 'Invoice lines edit'

    line_ids = fields.One2many(
        comodel_name='invoice.lines.edit.lines',
        inverse_name='wizard_id',
        string='Lines',
    )

    @api.multi
    def button_accept(self):
        for line in self.line_ids:
            line.line_id.write({
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
                'discount': line.discount})
