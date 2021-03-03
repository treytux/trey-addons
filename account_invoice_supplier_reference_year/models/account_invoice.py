###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _check_duplicate_supplier_reference(self):
        for inv in self:
            if inv.type not in ('in_invoice', 'in_refund'):
                continue
            if not inv.reference:
                continue
            domain = [
                ('date_invoice', '>=', '%s-01-01' % inv.date_invoice.year),
                ('date_invoice', '<=', '%s-12-31' % inv.date_invoice.year),
                ('type', '=', inv.type),
                ('reference', '=', inv.reference),
                ('company_id', '=', inv.company_id.id),
                ('commercial_partner_id', '=', inv.commercial_partner_id.id),
                ('id', '!=', inv.id)
            ]
            if self.search(domain):
                raise exceptions.UserError(_(
                    'Duplicated vendor reference detected. You probably '
                    'encoded twice the same vendor bill/credit note.'))
