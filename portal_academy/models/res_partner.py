###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _portal_enrollment_requirement_error(self):
        self.ensure_one()
        if not (self.name or '').strip() or not (self.vat or '').strip():
            return _(
                'Please complete your customer name and VAT number before '
                'enrolling.')
        bank_accounts = self.bank_ids.filtered('active')
        if not bank_accounts:
            return _('Please add a bank account before enrolling.')
        valid_mandate = self.env['account.banking.mandate'].sudo().search([
            ('partner_bank_id', 'in', bank_accounts.ids),
            ('state', '=', 'valid'),
        ], limit=1)
        if not valid_mandate:
            return _('A valid SEPA mandate is required before enrolling.')
        return False
