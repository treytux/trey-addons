###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64

from odoo import _, exceptions, fields, models


class AccountInvoiceExportA3Erp(models.TransientModel):
    _name = 'account.invoice.export.a3erp'
    _description = 'Wizard to export invoice to a3ERP format'

    generated_file = fields.Binary(
        string='Generated file',
    )
    filename = fields.Char(
        string='Filename',
    )
    step = fields.Integer(
        string='Wizard steps',
    )

    def get_invoice_type(self, invoice):
        return '6200' if invoice.refund_invoice_id else '6100'

    def check_invoice_lenght(self):
        if len(self.env.context.get('active_ids', [])) != 1:
            raise exceptions.ValidationError(
                _('No more than one invoice can be generated per file.'))
        return True

    def check_company_and_office_code(self, invoice):
        if not invoice.company_id.company_code_a3erp:
            raise exceptions.ValidationError(
                _('Company code for a3ERP is not defined in company %s.') % (
                    invoice.company_id.name))
        if not invoice.company_id.office_code_a3erp:
            raise exceptions.ValidationError(
                _('Office code for a3ERP is not defined in company %s.') % (
                    invoice.company_id.name))

    def check_invoice_payment_mode(self, invoice):
        if not invoice.payment_mode_id:
            raise exceptions.ValidationError(
                _('The invoice has no payment method.'))

    def check_invoice_payment_operation_type(self, invoice):
        if not invoice.payment_mode_id.operation_type_a3erp:
            raise exceptions.ValidationError(
                _('The payment mode has no operation code for a3ERP.'))

    def check_invoice_payment_tax_type(self, invoice):
        if not invoice.payment_mode_id.tax_type_a3erp:
            raise exceptions.ValidationError(
                _('The payment mode has no tax type for a3ERP.'))

    def check_invoice_payment_exists(self):
        active_ids = self.env.context.get('active_ids', [])
        invoice = self.env['account.invoice'].browse(active_ids)
        if len(invoice.payment_ids) == 0:
            raise exceptions.ValidationError(
                _('The invoice has no payment.'))

    def set_filename(self, invoice):
        return 'account_invoice_export_a3erp_%s' % invoice.number

    def generate_operations_a3erp_file(self, invoice):
        data = ''
        data += invoice.company_id.company_code_a3erp and (
            invoice.company_id.company_code_a3erp.zfill(4)) or ''.zfill(4)
        data += invoice.company_id.office_code_a3erp and (
            invoice.company_id.office_code_a3erp.zfill(4)) or ''.zfill(4)
        data += invoice.date_invoice.strftime('%Y%m%d')
        data += invoice.date_invoice.strftime('%Y%m%d')
        data += '00'
        data += invoice.payment_mode_id.operation_type_a3erp.zfill(4)
        data += invoice.reference and (
            invoice.reference.zfill(14)) or ''.zfill(14)
        data += invoice.number.zfill(14)
        data += '00000000000000'
        data += invoice.partner_id.vat and (
            invoice.partner_id.vat.zfill(14)) or 'ES12345678Z'.zfill(14)
        data += invoice.number.zfill(50)
        data += invoice.payment_mode_id.tax_type_a3erp.zfill(4)
        sign = '-' if invoice.refund_invoice_id else '+'
        data += '0001%s' % sign
        price_total = str(invoice.payment_ids[0].amount).replace('.', '')
        data += price_total.zfill(12)
        for _i in range(9):
            data += '00000001+000000000000'
        return data

    def generate_invoice_a3erp_file(self, invoice):
        sign = '-' if invoice.refund_invoice_id else '+'
        data = ''
        data += invoice.company_id.company_code_a3erp and (
            invoice.company_id.company_code_a3erp.zfill(4)) or ''.zfill(4)
        data += invoice.company_id.office_code_a3erp and (
            invoice.company_id.office_code_a3erp.zfill(4)) or ''.zfill(4)
        data += invoice.date_invoice.strftime('%Y%m%d')
        data += invoice.date_invoice.strftime('%Y%m%d')
        data += '02'
        data += self.get_invoice_type(invoice)
        data += invoice.number.zfill(14)
        data += invoice.number.zfill(14)
        data += '00000000000000'
        data += invoice.partner_id.vat and (
            invoice.partner_id.vat.zfill(14)) or ''.zfill(14)
        data += invoice.number.zfill(50)
        data += '00020001%s' % sign
        amount_total = str(invoice.amount_total).replace('.', '')
        data += amount_total.zfill(12)
        data += '00000001%s' % sign
        amount_tax = str(invoice.amount_tax).replace('.', '')
        data += amount_tax.zfill(12)
        data += '00000001%s' % sign
        amount_untaxed = str(invoice.amount_untaxed).replace('.', '')
        data += amount_untaxed.zfill(12)
        for _i in range(7):
            data += '00000001%s000000000000' % sign
        return data

    def _reopen_view(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.ids[0],
            'res_model': self._name,
            'target': 'new',
            'context': {},
        }

    def check_required_fields_and_lenght(self):
        self.ensure_one()
        self.check_invoice_lenght()
        active_ids = self.env.context.get('active_ids', [])
        invoices = self.env['account.invoice'].browse(active_ids)
        self.check_company_and_office_code(invoices[0])
        return invoices

    def generate_file_and_next_step(self, invoices, data):
        content = base64.b64encode(data.encode('utf-8'))
        self.write({
            'generated_file': content,
            'step': 1,
            'filename': self.set_filename(invoices[0])
        })

    def button_generate_invoice_a3erp_file(self):
        invoices = self.check_required_fields_and_lenght()
        data = self.generate_invoice_a3erp_file(invoices[0])
        self.generate_file_and_next_step(invoices, data)
        return self._reopen_view()

    def button_generate_operation_a3erp_file(self):
        invoices = self.check_required_fields_and_lenght()
        self.check_invoice_payment_exists()
        self.check_invoice_payment_mode(invoices[0])
        self.check_invoice_payment_operation_type(invoices[0])
        self.check_invoice_payment_tax_type(invoices[0])
        data = self.generate_operations_a3erp_file(invoices[0])
        self.generate_file_and_next_step(invoices, data)
        return self._reopen_view()
