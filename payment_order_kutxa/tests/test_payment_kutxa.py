# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields
from openerp.addons.l10n_es_payment_order.wizard.converter import \
    PaymentConverterSpain
from tempfile import NamedTemporaryFile
import base64
import csv
import datetime
import openerp.tests.common as common


class TestPaymentKutxa(common.TransactionCase):
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
                'payment_order_kutxa.export_kutxa').id,
            'contract_number': 'CT235679',
            'payment_kutxa_type': '56'})

    def create_payment_check_mode(self):
        self.check_payment_mode = self.env['payment.mode'].create({
            'name': 'kutxa_payment_check',
            'bank_id': self.bank_payment_mode.id,
            'journal': self.account_journal.id,
            'type': self.env.ref(
                'payment_order_kutxa.export_kutxa').id,
            'contract_number': 'CT235679',
            'payment_kutxa_type': '57'})

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
            'communication': 'reference21'})
        self.payment_line.bank_id = self.partner_bank

    def configure_payment_order(self, payment_order):
        self.payment_order.signal_workflow('open')
        self.assertEqual(self.payment_order.state, 'open')
        self.payment_order.signal_workflow('done')
        self.assertEqual(self.payment_order.state, 'done')

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
        today = datetime.date.today().strftime('%d%m%y')
        line1 = data[0][0]
        self.assertEqual('5101', line1[0:4])
        self.assertEqual('A31109267', line1[5:14])
        self.assertEqual(today, line1[14:20])
        ref = payment_order.reference.replace('/', '_')
        self.assertEqual(ref, line1[20:28])
        company = self.bank_payment_mode.partner_id
        company_name_csv = line1[28:(28 + len(company.name))].decode('utf-8')
        self.assertEqual(company.name, company_name_csv)
        self.assertEqual('208058011234567891', line1[68:86])
        line5 = data[1][0]
        self.assertEqual('5102', line5[0:4])
        self.assertEqual(company.vat[2:], line5[5:14])
        company_str_csv = line5[14:(15 + len(company.street))].decode('utf-8')
        self.assertEqual(company.street, company_str_csv)
        line3 = data[2][0]
        self.assertEqual('5103', line3[0:4])
        self.assertEqual(company.vat[2:], line3[5:14])
        self.assertEqual(company.zip, line3[14:(14 + len(company.zip))])
        company_city_csv = line3[19:(19 + len(company.city))].decode('utf-8')
        self.assertEqual(company.city, company_city_csv)
        state_name = company.state_id.name
        company_state_csv = line3[55:(55 + len(state_name))].decode('utf-8')
        self.assertEqual(state_name, company_state_csv)
        line4 = data[3][0]
        self.assertEqual('5301', line4[0:4])
        suppl = self.supplier_01
        self.assertEqual(suppl.vat[2:], line4[5:14])
        self.assertEqual(5 * '0', line4[14:19])
        ref = self.payment_order.reference
        ref = ref[2:].replace("/", "")
        ref = ref.zfill(7)
        self.assertEqual(ref, line4[19:(19 + len(ref))])
        self.assertEqual(suppl.name, line4[26:(26 + len(suppl.name))])
        quantity = self.converter.convert(abs(self.payment_order.total), 10)
        self.assertEqual(quantity, line4[66:76])
        self.assertEqual(today, line4[76:82])
        due_date = self.inv_suppl_01.date_due.replace('-', '')
        due_day = due_date[6:8]
        due_month = due_date[4:6]
        due_year = due_date[2:4]
        due_date = due_day + due_month + due_year
        self.assertEqual(due_date, line4[82:88])
        if self.payment_order.mode.payment_kutxa_type == '56':
            self.assertEqual('1', line4[88])
        else:
            self.assertEqual('2', line4[88])
        line5 = data[4][0]
        self.assertEqual('5302', line5[0:4])
        self.assertEqual(suppl.vat[2:], line5[5:14])
        self.assertEqual(suppl.street, line5[14:(14 + len(suppl.street))])
        line6 = data[5][0]
        self.assertEqual('5303', line6[0:4])
        self.assertEqual(suppl.vat[2:], line6[5:14])
        self.assertEqual(suppl.zip, line6[14:(14 + len(suppl.zip))])
        self.assertEqual(suppl.city, line6[19:(19 + len(suppl.city))])
        state_name = suppl.state_id.name
        state_file_csv = line6[55:(55 + len(state_name))].decode('utf-8')
        self.assertEqual(state_name, state_file_csv)
        if self.payment_order.mode.payment_kutxa_type == '56':
            acc_partner = self.partner_bank.acc_number.replace(' ', '')
            if self.partner_bank.state == 'iban':
                acc_partner = acc_partner[4:]
            self.assertEqual(acc_partner, line6[70:91])
        line7 = data[6][0]
        self.assertEqual('5601', line7[0:4])
        self.assertEqual(suppl.vat[2:], line7[5:14])
        communication = self.payment_line.communication
        self.assertEqual(communication, line7[20:(20 + len(communication))])
        line8 = data[7][0]
        self.assertEqual('5901', line8[0:4])
        self.assertEqual(company.vat[2:], line8[5:14])
        self.assertEqual(quantity, line8[16:26])
        self.assertEqual('000000000001', line8[26:38])
        self.assertEqual('000000000008', line8[38:50])
        self.assertEqual(len(wiz_export.file), 997)

    def common_functions(self):
        self.create_payment_line(self.payment_order.id)
        self.assertEqual(len(self.payment_order.line_ids), 1)
        self.configure_payment_order(self.payment_order)
        self.generate_and_test_file(self.payment_order)

    def test_transfer_kutxa(self):
        self.create_and_validate_invoice()
        self.create_bank_payment_mode()
        self.create_payment_transfer_mode()
        self.create_payment_order(self.transfer_payment_mode)
        self.common_functions()

    def test_check_kutxa(self):
        self.create_and_validate_invoice()
        self.create_bank_payment_mode()
        self.create_payment_check_mode()
        self.create_payment_order(self.check_payment_mode)
        self.common_functions()
