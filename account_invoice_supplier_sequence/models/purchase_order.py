###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def action_view_invoice(self):
        result = super().action_view_invoice()
        sequence = self.partner_id.invoice_supplier_sequence_id
        if not sequence:
            return result
        reference = result['context']['default_reference']
        if reference:
            return result
        sequence = sequence.with_context(
            ir_sequence_date=fields.Date.today(),
            ir_sequence_date_range=fields.Date.today(),
        )
        result['context']['default_reference'] = sequence.next_by_id()
        return result
