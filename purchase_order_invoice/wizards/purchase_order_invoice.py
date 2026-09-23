###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_log = logging.getLogger(__name__)


MAGIC_COLUMNS = ('id', 'create_uid', 'create_date', 'write_uid', 'write_date')
TYPE2REFUND = {
    'out_invoice': 'out_refund',
    'in_invoice': 'in_refund',
    'out_refund': 'out_invoice',
    'in_refund': 'in_invoice',
}


class PurchaseOrderInvoice(models.TransientModel):
    _name = 'purchase.order.invoice'
    _description = 'Wizard for invoice purchase order'

    method = fields.Selection(
        selection=[
            ('received', 'Invoice received not invoiced'),
            ('all-not-invoiced', 'Invoice all lines not invoiced'),
            ('all', 'Invoice all lines'),
        ],
        string='Invoice method',
        default='received',
    )
    join_purchases = fields.Boolean(
        string='Join purchases same supplier',
        default=True,
    )

    def purchases_get(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            raise UserError(_('Nothing to invoice.'))
        purchases = self.env['purchase.order'].browse(
            self._context['active_ids'])
        return purchases

    def action_view_invoice(self):
        purchases = self.purchases_get()
        if len(purchases) == 1:
            return purchases.with_context(
                create_bill=False).action_view_invoice()
        self.action_invoice()
        action = self.env.ref('account.action_move_in_invoice_type').read()[0]
        action['domain'] = '[("id", "in", %s)]' % str(
            purchases.mapped('invoice_ids.id'))
        action['view_type'] = 'tree'
        return action

    def _get_refund_common_fields(self):
        return [
            'partner_id', 'invoice_payment_term_id',
            'currency_id', 'journal_id']

    def _get_refund_prepare_fields(self):
        return ['name', 'ref', 'invoice_date_due']

    def _get_refund_copy_fields(self):
        copy_fields = ['company_id', 'user_id', 'fiscal_position_id']
        common_fields = self._get_refund_common_fields()
        prepare_fields = self._get_refund_prepare_fields()
        return common_fields + prepare_fields + copy_fields

    def _refund_cleanup_lines(self, lines):
        result = []
        for line in lines:
            values = {}
            for name, field in line._fields.items():
                if name in MAGIC_COLUMNS:
                    continue
                elif field.type == 'many2one':
                    values[name] = line[name].id
                elif field.type not in ['many2many', 'one2many']:
                    values[name] = line[name]
                elif name == 'invoice_line_tax_ids':
                    values[name] = [(6, 0, line[name].ids)]
                elif name == 'analytic_tag_ids':
                    values[name] = [(6, 0, line[name].ids)]
            result.append((0, 0, values))
        return result

    def _refund_tax_lines_account_change(self, lines, taxes_to_change):
        if not taxes_to_change:
            return lines
        for line in lines:
            if isinstance(
                    line[2], dict) and line[2]['tax_id'] in taxes_to_change:
                line[2]['account_id'] = taxes_to_change[line[2]['tax_id']]
        return lines

    def _get_partner_bank_id(self, company_id):
        company = self.env['res.company'].browse(company_id)
        if company.partner_id:
            bank = self.env['res.partner.bank'].search([
                ('partner_id', '=', company.partner_id.id),
                ('company_id', '=', company.id)
            ], limit=1)
            if not bank:
                bank = self.env['res.partner.bank'].search([
                    ('partner_id', '=', company.partner_id.id),
                    ('company_id', '=', False)
                ], limit=1)
            return bank

    def _prepare_refund(
            self, invoice, date_invoice=None, date=None,
            description=None, journal_id=None):
        values = {}
        for field in self._get_refund_copy_fields():
            if invoice._fields[field].type == 'many2one':
                values[field] = invoice[field].id
            else:
                values[field] = invoice[field] or False
        values['invoice_line_ids'] = self._refund_cleanup_lines(
            invoice.invoice_line_ids)
        if journal_id:
            journal = self.env['account.journal'].browse(journal_id)
        elif invoice['move_type'] == 'in_invoice':
            journal = self.env['account.journal'].search([
                ('type', '=', 'purchase')
            ], limit=1)
        else:
            journal = self.env['account.journal'].search([
                ('type', '=', 'sale')
            ], limit=1)
        values['journal_id'] = journal.id
        values['move_type'] = TYPE2REFUND[invoice['move_type']]
        values['invoice_date'] = date_invoice or fields.Date.context_today(
            invoice)
        values['invoice_date_due'] = values['invoice_date']
        values['state'] = 'draft'
        values['sequence_number'] = False
        values['invoice_origin'] = invoice.sequence_number
        values['reversal_move_id'] = invoice.id
        values['ref'] = False
        if values['move_type'] == 'in_refund':
            values['invoice_payment_term_id'] = (
                invoice.partner_id.property_supplier_payment_term_id.id)
            partner_bank_result = self._get_partner_bank_id(
                values['company_id'])
            if partner_bank_result:
                values['partner_bank_id'] = partner_bank_result.id
        else:
            values['invoice_payment_term_id'] = (
                invoice.partner_id.property_payment_term_id.id)
        if date:
            values['date'] = date
        if description:
            values['name'] = description
        return values

    def create_refund_invoice(self, invoice):
        for line in invoice.invoice_line_ids:
            line.quantity *= -1
        refund = self._prepare_refund(invoice)
        invoice.invoice_line_ids = [(6, 0, [])]
        del refund['reversal_move_id']
        del refund['invoice_origin']
        for _op, _code, vals in refund['invoice_line_ids']:
            if 'origin_line_ids' in vals:
                vals['origin_line_ids'] = False
        invoice.update(refund)
        invoice._compute_tax_totals()

    def action_invoice(self):
        def join_invoices(new_invoice, invoices):
            invoice = invoices.filtered(
                lambda inv: inv.partner_id == new_invoice.partner_id)
            if not invoice:
                return new_invoice
            invoice.invoice_origin = '%s,%s' % (
                invoice.invoice_origin, purchase.name)
            invoice.purchase_id = False
            for line in new_invoice.invoice_line_ids:
                data = line._convert_to_write(line._cache)
                data['move_id'] = invoice.id
                line.create(data)
            invoice._compute_tax_totals()
            return invoice

        invoices = self.env['account.move']
        purchases = self.purchases_get()
        for index, purchase in enumerate(purchases):
            _log.info('[%s/%s] Invoice purchase %s' % (
                index + 1, len(purchases), purchase.name))
            invoice = invoices.new({
                'invoice_origin': purchase.name,
                'purchase_id': purchase.id,
                'move_type': 'in_invoice',
                'currency_id': purchase.currency_id.id,
                'company_id': purchase.company_id.id,
            })
            invoice._onchange_purchase_auto_complete()
            invoice._onchange_partner_id()
            if self.method == 'all':
                for line in invoice.invoice_line_ids:
                    line.quantity = line.purchase_line_id.product_qty
            elif self.method == 'all-not-invoiced':
                for line in invoice.invoice_line_ids:
                    line.quantity = (
                        line.purchase_line_id.product_qty
                        - line.purchase_line_id.qty_invoiced)
            lines_to_delete = invoice.invoice_line_ids.filtered(
                lambda ln: ln.quantity == 0)
            invoice.invoice_line_ids = (
                invoice.invoice_line_ids - lines_to_delete)
            if not invoice.invoice_line_ids:
                continue
            if self.join_purchases:
                invoice = join_invoices(invoice, invoices)
            if invoice.id not in invoices.ids:
                data = invoices._convert_to_write(invoice._cache)
                data['invoice_line_ids'].pop(0)
                invoice = invoices.create(data)
                invoice._compute_tax_totals()
                invoices |= invoice
        for invoice in invoices:
            if invoice.amount_total < 0:
                self.create_refund_invoice(invoice)
        if len(invoices) > 1:
            return True
        return purchase.with_context(create_bill=False).action_view_invoice()
