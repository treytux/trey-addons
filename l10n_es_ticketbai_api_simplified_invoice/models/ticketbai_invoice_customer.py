###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, models


class TicketBaiInvoiceCustomer(models.Model):
    _inherit = 'tbai.invoice.customer'

    def _try_nif_validation(self):
        for record in self:
            partner = record.tbai_invoice_id.invoice_id.partner_id
            if partner.aeat_anonymous_cash_customer:
                record.tbai_invoice_id.simplified_invoice = 'S'
                continue
            else:
                raise exceptions.ValidationError(
                    _('TicketBAI Invoice %s:\n Spanish Fiscal Identification '
                      'Number or Identification Number for non spanish '
                      'customers is required.') % record.tbai_invoice_id.name)

    @api.constrains('nif')
    def _check_nif(self):
        try:
            super()._check_nif()
        except exceptions.ValidationError:
            self._try_nif_validation()

    @api.constrains('identification_number')
    def _check_identification_number(self):
        try:
            super()._check_identification_number()
        except exceptions.ValidationError:
            self._try_nif_validation()

    @api.constrains('idtype')
    def _check_idtype(self):
        try:
            super()._check_idtype()
        except exceptions.ValidationError:
            self._try_nif_validation()
