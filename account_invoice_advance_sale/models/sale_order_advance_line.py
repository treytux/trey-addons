###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class SaleOrderAdvanceLine(models.Model):
    _name = 'sale.order.advance_line'
    _description = 'Sale Order Advance Line'

    name = fields.Char(
        string='Name',
        required=True,
    )
    sequence = fields.Integer(
        string='Sequence',
    )
    sale_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
    )
    percent = fields.Float(
        string='Percent',
    )
    date = fields.Date(
        string='Date',
        required=True,
    )

    def apply_invoice(self, invoice):
        self.ensure_one()
        invoice.update({
            'name': self.name,
            'date_invoice': self.date,
        })
        if not invoice.advance_invoice_id:
            return
        line = invoice.invoice_line_ids[0]
        line.name = self.name
        line.advance_line_ids.name = self.name
