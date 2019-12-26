# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields
from tempfile import NamedTemporaryFile
import base64
import csv
import datetime
import openerp.tests.common as common


class TestConfirmingKutxa(common.TransactionCase):
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
            'state_id': self.ref('l10n_es_toponyms.ES15'),
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
        return self.env['res.partner.bank'].create({
            'partner_id': company,
            'bank_name': 'MyBank Kutxa',
            'state': 'iban',
            'acc_number': 'ES94 2080 5801 1012 3456 7891'})

    def create_payment_transfer_mode(self):
        self.transfer_payment_mode = self.env['payment.mode'].create({
            'name': 'kutxa_confirming_transfer',
            'bank_id': self.create_bank_payment_mode().id,
            'journal': self.account_journal.id,
            'type': self.env.ref(
                'payment_order_confirming_kutxa.export_kutxa').id,
            'contract_number': 'CT235679',
            'conf_kutxa_type': '56'})

    def create_payment_check_mode(self):
        self.check_payment_mode = self.env['payment.mode'].create({
            'name': 'kutxa_confirming_check',
            'bank_id': self.create_bank_payment_mode().id,
            'journal': self.account_journal.id,
            'type': self.env.ref(
                'payment_order_confirming_kutxa.export_kutxa').id,
            'contract_number': 'CT235679',
            'conf_kutxa_type': '57'})

    def create_payment_order(self, payment_mode):
        self.payment_order = self.env['payment.order'].create({
            'mode': payment_mode.id})

    def create_payment_line(self, payment_order_id):
        move_line = self.env['account.move.line'].search([
            ('invoice', '=', self.inv_suppl_01.id),
            ('name', '=', '/')], limit=1)
        self.payment_line = self.env['payment.line'].create({
            'order_id': payment_order_id,
            'move_line_id': move_line.id,
            'amount_currency': 156,
            'partner_id': self.supplier_01.id,
            'communication': self.inv_suppl_01.id})
        self.payment_line.bank_id = self.partner_bank

    def configure_payment_order(self, payment_order):
        self.payment_order.signal_workflow('open')
        self.assertEqual(self.payment_order.state, 'open')
        self.payment_order.signal_workflow('done')
        self.assertEqual(self.payment_order.state, 'done')

    def generate_and_test_confirming_file(self, payment_order):
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
        today = datetime.date.today().strftime('%Y%m%d')
        line1 = data[0][0]
        self.assertEqual('Caldereria Navarra S.A.L.', line1[1:26])
        self.assertEqual('A31109267', line1[51:60])
        due_date = self.inv_suppl_01.date_due.replace('-', '')
        self.assertEqual(due_date, line1[66:74])
        self.assertEqual('CT235679', line1[94:102])
        self.assertEqual('ES9420805801101234567891', line1[102:126])
        self.assertEqual('EUR', line1[136:139])
        self.assertEqual('1', line1[139:140])
        self.assertEqual('confkutxa', line1[140:149])
        ref = payment_order.reference.replace('/', '')
        self.assertEqual(ref, line1[149:156])
        line2 = data[1][0]
        self.assertEqual('Polígono Landaben C/ C, 6', line2[1:27])
        self.assertEqual('Pamplona', line2[67:75])
        self.assertEqual('31012', line2[107:112])
        line3 = data[2][0]
        self.assertEqual('Supplier 01', line3[1:12])
        self.assertEqual('A00000000', line3[71:80])
        self.assertEqual('Plaza General, 2', line3[91:107])
        self.assertEqual('Granada', line3[156:163])
        self.assertEqual('18500', line3[196:201])
        self.assertEqual('ES', line3[206:208])
        line4 = data[3][0]
        self.assertEqual('supplier1@test.com', line4[1:19])
        self.assertEqual('666888999', line4[101:110])
        line5 = data[4][0]
        if self.payment_order.mode.conf_kutxa_type == '56':
            self.assertEqual('T', line5[1:2])
            self.assertEqual('ES4330350114181140016797', line5[2:26])
        else:
            self.assertEqual('C', line5[1:2])
            self.assertEqual('                        ', line5[2:26])
        self.assertEqual('ES', line5[81:83])
        line6 = data[5][0]
        self.assertEqual(self.inv_suppl_01.number, line6[1:14])
        self.assertEqual('+', line6[21:22])
        self.assertEqual('000000000015600', line6[22:37])
        self.assertEqual(today, line6[37:45])
        self.assertEqual(today, line6[45:53])
        line7 = data[6][0]
        self.assertEqual('000000000001', line7[1:13])
        self.assertEqual('000000000015600', line7[13:28])
        self.assertEqual(len(wiz_export.file), 2387)

    def common_functions(self):
        self.create_payment_line(self.payment_order.id)
        self.assertEqual(len(self.payment_order.line_ids), 1)
        self.configure_payment_order(self.payment_order)
        self.generate_and_test_confirming_file(self.payment_order)

    def test_transfer_kutxa(self):
        self.create_and_validate_invoice()
        self.create_payment_transfer_mode()
        self.create_payment_order(self.transfer_payment_mode)
        self.common_functions()

    def test_check_kutxa(self):
        self.create_and_validate_invoice()
        self.create_payment_check_mode()
        self.create_payment_order(self.check_payment_mode)
        self.common_functions()
