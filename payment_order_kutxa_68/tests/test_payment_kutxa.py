# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from datetime import datetime
from openerp import fields
from openerp.addons.l10n_es_payment_order.wizard.converter import \
    PaymentConverterSpain
from tempfile import NamedTemporaryFile
import base64
import csv
import openerp.tests.common as common


class TestPaymentKutxa68(common.TransactionCase):
    def create_and_validate_invoice(self):
        self.tax_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1})
        self.pricelist_default_purchase = self.env[
            'product.pricelist'].create({
                'name': 'Default purchase',
                'type': 'purchase'})
        version_default_purchase = self.env[
            'product.pricelist.version'].create({
                'pricelist_id': self.pricelist_default_purchase.id,
                'name': 'Default purchase'})
        self.env['product.pricelist.item'].create({
            'price_version_id': version_default_purchase.id,
            'name': 'Default purchase',
            'sequence': 10,
            'base': self.ref('product.list_price')})
        self.supplier_01 = self.env['res.partner'].create({
            'name': 'Supplier 01',
            'is_company': True,
            'supplier': True,
            'property_product_pricelist_purchase': (
                self.pricelist_default_purchase.id),
            'email': 'supplier1@test.com',
            'street': 'Plaza General, 2',
            'zip': '18500',
            'vat': 'ESA00000000',
            'city': 'Granada',
            'state_id': self.ref('l10n_es_toponyms.ES19'),
            'country_id': self.ref('base.es'),
            'phone': '666888999'})
        self.account = self.env['account.account'].create({
            'name': 'Account for test module',
            'type': 'payable',
            'user_type': self.ref('account.data_account_type_payable'),
            'code': '40000',
            'currency_mode': 'current',
            'reconcile': True,
            'company_id': self.ref('base.main_company')})
        self.pt_01 = self.env['product.template'].create({
            'name': 'Product 01',
            'type': 'consu',
            'taxes_id': [(6, 0, [self.tax_21.id])]})
        self.pp_01 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_01.id,
            'list_price': self.ref('product.list0')})
        self.account_journal = self.env['account.journal'].create({
            'code': 'JJJI',
            'name': 'bank journal',
            'type': 'sale',
            'sequence_id': self.ref(
                'account.sequence_refund_purchase_journal')})
        self.partner_bank = self.create_res_partner_bank()
        self.inv_suppl_01 = self.env['account.invoice'].create({
            'account_id': self.account.id,
            'type': 'in_invoice',
            'journal_id': self.account_journal.id,
            'partner_id': self.supplier_01.id,
            'partner_bank_id': self.partner_bank.id,
            'date_invoice': fields.Date.today()})
        self.invoice_line_01 = self.env['account.invoice.line'].create({
            'invoice_id': self.inv_suppl_01.id,
            'invoice_line_tax_id': [(6, 0, [self.tax_21.id])],
            'name': self.pp_01.name_template,
            'price_unit': self.pp_01.list_price,
            'product_id': self.pp_01.id,
            'quantity': 1})
        self.inv_suppl_01.button_reset_taxes()
        self.inv_suppl_01.signal_workflow('invoice_open')
        self.assertEqual(self.inv_suppl_01.state, 'open')

    def create_res_partner_bank(self):
        return self.env['res.partner.bank'].create({
            'state': 'iban',
            'partner_id': self.supplier_01.id,
            'bank_name': 'MyBank',
            'acc_country_id': self.ref('base.es'),
            'acc_number': 'ES43 3035 0114 1811 4001 6797'})

    def create_bank_payment_mode(self):
        company = self.ref('base.main_company')
        self.bank_payment_mode = self.env['res.partner.bank'].create({
            'partner_id': company,
            'bank_name': 'MyBank Kutxa',
            'state': 'iban',
            'acc_number': 'ES94 2080 5801 1012 3456 7891'})

    def create_payment_transfer_mode(self):
        self.transfer_payment_mode = self.env['payment.mode'].create({
            'name': 'kutxa_payment_transfer',
            'bank_id': self.bank_payment_mode.id,
            'journal': self.account_journal.id,
            'type': self.env.ref(
                'payment_order_kutxa_68.export_payment').id,
            'contract_number': 'CT235679',
            'payment_type_68': '56'})

    def create_payment_order(self, payment_mode):
        self.payment_order = self.env['payment.order'].create({
            'mode': payment_mode.id,
            'reference': 2019034})

    def create_payment_line(self, payment_order_id):
        move_line = self.env['account.move.line'].search([
            ('invoice', '=', self.inv_suppl_01.id),
            ('name', '=', '/')], limit=1)
        self.payment_line = self.env['payment.line'].create({
            'order_id': payment_order_id,
            'move_line_id': move_line.id,
            'amount_currency': 156,
            'partner_id': self.supplier_01.id,
            'communication': 'reference21'})
        self.payment_line.bank_id = self.partner_bank

    def configure_payment_order(self, payment_order):
        self.payment_order.signal_workflow('open')
        self.assertEqual(self.payment_order.state, 'open')
        self.payment_order.signal_workflow('done')
        self.assertEqual(self.payment_order.state, 'done')

    def compute_ref(self, ref, len):
        return ref.replace('/', '').zfill(len)[:len]

    def get_ref(self):
        ref = self.payment_line['ml_inv_ref'][0].number
        ref = ''.join([x for x in ref if x.isdigit()])
        ref = self.compute_ref(ref, 7)
        dc = '9000' + ref
        dc = int(dc) % 7
        ref += self.converter.convert(str(dc), 1)
        return ref

    def pop_beneficiary_test(self, payment_order, line, i):
        suppl = self.supplier_01
        self.assertEqual('06', line[0:2])
        self.assertEqual('59', line[2:4])
        payment_mode = payment_order.mode
        self.assertEqual(payment_mode.bank_id.partner_id.vat[2:], line[4:13])
        self.assertEqual(payment_mode.csb_suffix, line[13:16])
        self.assertEqual(suppl.vat, line[17:28])
        self.assertEqual('0' + (str(i + 10)), line[28:31])
        if (i + 1) == 1:
            self.assertEqual(suppl.name, line[31:(31 + len(suppl.name))])
            self.assertEqual(29 * ' ', line[71:100])
        if (i + 1) == 2:
            self.assertEqual(suppl.street, line[31:(31 + len(suppl.street))])
            self.assertEqual(24 * ' ', line[76:100])
        if (i + 1) == 3:
            self.assertEqual(suppl.zip, line[31:(31 + len(suppl.zip))])
            self.assertEqual(suppl.city, line[36:(36 + len(suppl.city))])
            self.assertEqual(24 * ' ', line[76:100])
        if (i + 1) == 4:
            self.assertEqual(suppl.zip, line[31:(31 + len(suppl.zip))])
            self.assertEqual(
                suppl.state_id.name, line[40:(40 + len(suppl.state_id.name))])
            self.assertEqual(suppl.country_id.name, line[70:(70 + len(
                suppl.country_id.name))])
            self.assertEqual(10 * ' ', line[90:100])
        if (i + 1) == 5:
            self.assertEqual(self.get_ref(), line[31:39])
            today = datetime.today().strftime('%d%m%Y')
            self.assertEqual(today, line[39:47])
            imp = self.converter.convert(abs(self.payment_order.total), 12)
            self.assertEqual(imp, line[47:59])
            self.assertEqual('0', line[59:60])
            self.assertEqual(40 * ' ', line[60:100])
        if (i + 1) == 6:
            self.assertEqual(self.get_ref(), line[31:39])
            ref_order = self.compute_ref(
                payment_order.line_ids[0].ml_inv_ref.number, 12)
            self.assertEqual(ref_order, line[39:51])
            dat_order = datetime.strptime(
                payment_order.line_ids[0].ml_date_created, '%Y-%m-%d')
            dat_order = self.converter.convert(dat_order.strftime('%d%m%Y'), 8)
            self.assertEqual(dat_order, line[51:59])
            amount = self.converter.convert(abs(self.payment_order.total), 12)
            self.assertEqual(amount, line[59:71])
            if 'in' in self.inv_suppl_01.type:
                self.assertEqual('H', line[71:72])
            else:
                self.assertEqual('D', line[71:72])
            self.assertEqual(self.compute_ref(
                payment_order.line_ids[0].ml_inv_ref.number, 8), line[72:80])

    def generate_and_test_file(self, payment_order):
        self.converter = PaymentConverterSpain()
        wiz_export = self.env['banking.export.csb.wizard'].with_context({
            'active_ids': [payment_order.id],
            'active_model': 'payment.order',
            'active_id': payment_order.id}).create({})
        wiz_export.create_csb()
        self.assertTrue(wiz_export.file)
        data = base64.decodestring(wiz_export.file)
        file_obj = NamedTemporaryFile(
            'w+', suffix='.text', delete=False)
        file_obj.write(base64.decodestring(wiz_export.file))
        path = file_obj.name
        file_obj.close()
        with open(path, "rb") as fp:
            doc = csv.reader(
                fp, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
            data = [ln for ln in doc]
        today = datetime.today().strftime('%d%m%y')
        line1 = data[0][0]
        self.assertEqual('03', line1[0:2])
        self.assertEqual('59', line1[2:4])
        payment_mode = payment_order.mode
        bank_id = payment_mode.bank_id
        self.assertEqual(bank_id.partner_id.vat[2:], line1[4:13])
        self.assertEqual(payment_mode.csb_suffix, line1[13:16])
        self.assertEqual(12 * ' ', line1[16:28])
        self.assertEqual('001', line1[28:31])
        self.assertEqual(today, line1[31:37])
        self.assertEqual(9 * ' ', line1[37:46])
        self.assertEqual(bank_id.acc_number.replace(' ', ''), line1[46:70])
        self.assertEqual(30 * ' ', line1[70:100])
        for i in range(6):
            line = data[i + 1][0]
            self.pop_beneficiary_test(payment_order, line, i)
        line8 = data[7][0]
        self.assertEqual('08', line8[0:2])
        self.assertEqual('59', line8[2:4])
        self.assertEqual(bank_id.partner_id.vat[2:], line8[4:13])
        self.assertEqual(payment_mode.csb_suffix, line8[13:16])
        amount = self.converter.convert(abs(self.payment_order.total), 12)
        self.assertEqual(amount, line8[31:43])
        self.assertEqual(amount, line8[31:43])
        self.assertEqual('0000000008', line8[43:53])
        self.assertEqual(47 * ' ', line8[53:100])

    def test_transfer_kutxa(self):
        self.create_and_validate_invoice()
        self.create_bank_payment_mode()
        self.create_payment_transfer_mode()
        self.create_payment_order(self.transfer_payment_mode)
        self.create_payment_line(self.payment_order.id)
        self.assertEqual(len(self.payment_order.line_ids), 1)
        self.configure_payment_order(self.payment_order)
        self.generate_and_test_file(self.payment_order)
