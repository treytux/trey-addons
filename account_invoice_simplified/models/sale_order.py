###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        if self.partner_id.vat:
            return res
        if not self.env.user.company_id.simplified_journal_id:
            raise exceptions.Warning(_(
                'Please define a journal for simplified invoices in the '
                'company setting'))
        res['journal_id'] = self.env.user.company_id.simplified_journal_id.id
        return res
