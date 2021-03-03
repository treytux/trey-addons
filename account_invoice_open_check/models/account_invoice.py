###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.exceptions import ValidationError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def check_invoice_data(self):
        errors = []
        if not self.partner_id.vat:
            errors.append(_('The \'Vat\' field of partner must be filled.'))
        if (
                self.type in ['out_invoice', 'out_refund']
                and not self.partner_shipping_id):
            errors.append(_('The \'Delivery address\' field must be filled.'))
        if not self.fiscal_position_id:
            errors.append(_('The \'Fiscal position\' field must be filled.'))
        if errors:
            msg = _(
                'The invoice can not be validated. Review:\n %s') % (
                    '\n'.join(errors))
            raise ValidationError(msg)

    @api.multi
    def action_invoice_open(self):
        for invoice in self:
            invoice.check_invoice_data()
        return super(AccountInvoice, self).action_invoice_open()
