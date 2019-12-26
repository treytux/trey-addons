# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import exceptions, _
from openerp.tests.common import TransactionCase
from tempfile import NamedTemporaryFile
import base64
import csv


class TestAccountInvoiceExport(TransactionCase):

    def setUp(self):
        super(TestAccountInvoiceExport, self).setUp()
        self.company = self.browse_ref('base.main_company')
        self.partner_01 = self.env['res.partner'].create({
            'name': 'Customer 01',
            'ref': 'CUST-123',
            'is_company': True,
            'customer': True,
            'email': 'customer1@test.com',
            'street': 'Calle Real, 33',
            'zip': 18008,
            'city': 'Granada',
            'phone': '666225522',
            'vat': 'ES12345678Z'})
        self.attribute1 = self.env['product.attribute'].create({
            'name': 'Test Attribute 1',
            'value_ids': [(0, 0, {'name': 'Value 1'}),
                          (0, 0, {'name': 'Value 2'})]})
        self.attribute2 = self.env['product.attribute'].create({
            'name': 'Test Attribute 2',
            'value_ids': [(0, 0, {'name': 'Value X'}),
                          (0, 0, {'name': 'Value Y'})]})
        self.product_tmpl1 = self.env['product.template'].create({
            'name': 'Test template 1',
            'default_code': 'T00001',
            'list_price': 1,
            'attribute_line_ids': [
                (0, 0, {'attribute_id': self.attribute1.id,
                        'value_ids': [(6, 0, self.attribute1.value_ids.ids)]}),
                (0, 0, {'attribute_id': self.attribute2.id,
                        'value_ids': [
                            (6, 0, self.attribute2.value_ids.ids)]})]})
        # Check products has 4 variants
        assert len(self.product_tmpl1.product_variant_ids) == 4
        self.product_tmpl2 = self.env['product.template'].create({
            'name': 'Test template 2',
            'default_code': 'T00002',
            'list_price': 5,
            'attribute_line_ids': [
                (0, 0, {'attribute_id': self.attribute1.id,
                        'value_ids': [
                            (6, 0, self.attribute1.value_ids[0].ids)]}),
                (0, 0, {'attribute_id': self.attribute2.id,
                        'value_ids': [
                            (6, 0, [
                                self.attribute2.value_ids[0].ids,
                                self.attribute2.value_ids[1].ids])]})]})
        # Check products has 2 variants
        assert len(self.product_tmpl2.product_variant_ids) == 2
        user_types = self.env['account.account.type'].search([])
        if not user_types:
            raise exceptions.Warning('Does not exist any account account type')
        self.user_type = user_types[0]
        self.account = self.env['account.account'].create({
            'name': 'Account for test module',
            'type': 'other',
            'user_type': self.user_type.id,
            'code': '11111',
            'currency_mode': 'current',
            'company_id': self.ref('base.main_company')})
        self.taxs_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.ref('base.main_company')})
        self.payment_mode_type = self.env['payment.mode.type'].create({
            'name': 'ManualBank',
            'code': 'OURSBANK'})
        self.partner_bank_01 = self.env['res.partner.bank'].create({
            'bank_name': 'MyBank',
            'state': 'iban',
            'acc_number': 'FR76 4242 4242 4242 4242 4242 424'})
        self.accounts_430 = self.env['account.account'].search([
            ('code', '=', '430000'),
            ('company_id', '=', self.ref('base.main_company'))])
        if not self.accounts_430.exists():
            raise exceptions.Warning(_(
                'Does not exist any account with \'430000\' code.'))
        self.account_journal = self.env['account.journal'].create({
            'code': 'JJJI',
            'name': 'bank journal',
            'type': 'sale',
            'default_debit_account_id': self.accounts_430.id,
            'default_credit_account_id': self.accounts_430.id,
            'sequence_id': self.ref(
                'account.sequence_refund_purchase_journal')})
        self.payment_mode_01 = self.env['payment.mode'].create({
            'name': 'Payment mode 01',
            'bank_id': self.partner_bank_01.id,
            'type': self.payment_mode_type.id,
            'journal': self.account_journal.id,
            'company_id': self.ref('base.main_company')})
        payment_terms = self.env['account.payment.term'].search([])
        if not payment_terms.exists():
            raise exceptions.Warning(_('Does not exist any payment_term.'))
        self.payment_term_01 = payment_terms[0]
        self.invoice_01 = self.env['account.invoice'].create({
            'account_id': self.account.id,
            'date_invoice': '11/08/17',
            'partner_id': self.partner_01.id,
            'payment_mode_id': self.payment_mode_01.id,
            'payment_term': self.payment_term_01.id})
        self.invoice_line_01 = self.env['account.invoice.line'].create({
            'invoice_id': self.invoice_01.id,
            'invoice_line_tax_id': [(6, 0, [self.taxs_21.id])],
            'name': self.product_tmpl1.product_variant_ids[0].name_template,
            'price_unit': self.product_tmpl1.product_variant_ids[0].list_price,
            'product_id': self.product_tmpl1.product_variant_ids[0].id,
            'quantity': 1})
        self.invoice_01.button_reset_taxes()
        self.invoice_02 = self.env['account.invoice'].create({
            'account_id': self.account.id,
            'date_invoice': '11/08/17',
            'partner_id': self.partner_01.id,
            'payment_mode_id': self.payment_mode_01.id,
            'payment_term': self.payment_term_01.id})
        self.invoice_line_02_1 = self.env['account.invoice.line'].create({
            'invoice_id': self.invoice_02.id,
            'invoice_line_tax_id': [(6, 0, [self.taxs_21.id])],
            'name': self.product_tmpl1.product_variant_ids[0].name_template,
            'price_unit': self.product_tmpl1.product_variant_ids[0].list_price,
            'product_id': self.product_tmpl1.product_variant_ids[0].id,
            'quantity': 1})
        self.invoice_line_02_2 = self.env['account.invoice.line'].create({
            'invoice_id': self.invoice_02.id,
            'invoice_line_tax_id': [(6, 0, [self.taxs_21.id])],
            'name': self.product_tmpl2.product_variant_ids[0].name_template,
            'price_unit': self.product_tmpl2.product_variant_ids[0].list_price,
            'product_id': self.product_tmpl2.product_variant_ids[0].id,
            'quantity': 2})
        self.invoice_02.button_reset_taxes()
        self.invoice_03 = self.env['account.invoice'].create({
            'account_id': self.account.id,
            'date_invoice': '11/08/17',
            'partner_id': self.partner_01.id,
            'payment_mode_id': self.payment_mode_01.id,
            'payment_term': self.payment_term_01.id})
        self.invoice_line_03_1 = self.env['account.invoice.line'].create({
            'invoice_id': self.invoice_03.id,
            'invoice_line_tax_id': [(6, 0, [self.taxs_21.id])],
            'name': self.product_tmpl1.product_variant_ids[0].name_template,
            'price_unit': self.product_tmpl1.product_variant_ids[0].list_price,
            'product_id': self.product_tmpl1.product_variant_ids[0].id,
            'quantity': 1})
        self.invoice_line_03_2 = self.env['account.invoice.line'].create({
            'invoice_id': self.invoice_03.id,
            'invoice_line_tax_id': [(6, 0, [self.taxs_21.id])],
            'name': self.product_tmpl1.product_variant_ids[0].name_template,
            'price_unit': self.product_tmpl1.product_variant_ids[0].list_price,
            'product_id': self.product_tmpl1.product_variant_ids[0].id,
            'quantity': 2})
        self.invoice_03.button_reset_taxes()
        self.invoice_04 = self.env['account.invoice'].create({
            'account_id': self.account.id,
            'date_invoice': '11/08/17',
            'partner_id': self.partner_01.id,
            'payment_mode_id': self.payment_mode_01.id,
            'payment_term': self.payment_term_01.id})
        self.invoice_line_04_1 = self.env['account.invoice.line'].create({
            'invoice_id': self.invoice_04.id,
            'invoice_line_tax_id': [(6, 0, [self.taxs_21.id])],
            'name': self.product_tmpl1.product_variant_ids[0].name_template,
            'price_unit': self.product_tmpl1.product_variant_ids[0].list_price,
            'product_id': self.product_tmpl1.product_variant_ids[0].id,
            'quantity': 1})
        self.invoice_line_04_2 = self.env['account.invoice.line'].create({
            'invoice_id': self.invoice_04.id,
            'invoice_line_tax_id': [(6, 0, [self.taxs_21.id])],
            'name': self.product_tmpl1.product_variant_ids[0].name_template,
            'price_unit': 10,
            'product_id': self.product_tmpl1.product_variant_ids[0].id,
            'quantity': 2})
        self.invoice_04.button_reset_taxes()
        self.invoice_05 = self.env['account.invoice'].create({
            'account_id': self.account.id,
            'date_invoice': '11/08/17',
            'partner_id': self.partner_01.id,
            'payment_mode_id': self.payment_mode_01.id,
            'payment_term': self.payment_term_01.id})
        self.invoice_line_05_1 = self.env['account.invoice.line'].create({
            'invoice_id': self.invoice_05.id,
            'invoice_line_tax_id': [(6, 0, [self.taxs_21.id])],
            'name': self.product_tmpl1.product_variant_ids[0].name_template,
            'price_unit': self.product_tmpl1.product_variant_ids[0].list_price,
            'product_id': self.product_tmpl1.product_variant_ids[0].id,
            'quantity': 1})
        self.invoice_line_05_1 = self.env['account.invoice.line'].create({
            'invoice_id': self.invoice_05.id,
            'invoice_line_tax_id': [(6, 0, [self.taxs_21.id])],
            'name': self.product_tmpl1.product_variant_ids[0].name_template,
            'price_unit': self.product_tmpl1.product_variant_ids[0].list_price,
            'product_id': self.product_tmpl1.product_variant_ids[0].id,
            'quantity': 4})
        self.invoice_line_05_2 = self.env['account.invoice.line'].create({
            'invoice_id': self.invoice_05.id,
            'invoice_line_tax_id': [(6, 0, [self.taxs_21.id])],
            'name': self.product_tmpl2.product_variant_ids[0].name_template,
            'price_unit': 10,
            'product_id': self.product_tmpl2.product_variant_ids[0].id,
            'quantity': 3})
        self.invoice_05.button_reset_taxes()

    def get_data_dict(self, wiz):
        file_obj = NamedTemporaryFile('w+', suffix='.csv', delete=False)
        file_obj.write(base64.decodestring(wiz.ffile))
        path = file_obj.name
        file_obj.close()
        with open(path, "rb") as fp:
            doc = csv.reader(
                fp, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
            count = 0
            data_dict = {}
            for row in doc:
                count += 1
                data_dict.update({count: row})
        return data_dict

    def test_export_01(self):
        '''File with one row'''
        wiz_export = self.env['wiz.account_invoice_export'].with_context({
            'active_ids': [self.invoice_01.id],
            'active_model': 'account.invoice',
            'active_id': self.invoice_01.id}).create({})
        wiz_export.button_accept()
        self.assertTrue(wiz_export.ffile)
        data_dict = self.get_data_dict(wiz_export)
        self.assertEqual(_(''), data_dict[1][1])
        self.assertEqual('', data_dict[1][1])
        self.assertEqual('11/08/2017', data_dict[2][1])
        self.assertEqual([], data_dict[3])
        self.assertEqual('CUST-123', data_dict[4][1])
        self.assertEqual(_('Customer 01'), data_dict[5][1])
        self.assertEqual(_('Calle Real, 33 18008'), data_dict[6][1])
        self.assertEqual(_('Granada'), data_dict[7][1])
        self.assertEqual('', data_dict[8][1])
        self.assertEqual('', data_dict[9][1])
        self.assertEqual('ES12345678Z', data_dict[10][1])
        self.assertEqual([], data_dict[11])
        self.assertEqual('T00001', data_dict[13][0])
        self.assertIn('Test template 1', data_dict[13][1])
        self.assertEqual('1,00', data_dict[13][2])
        self.assertEqual('1,00', data_dict[13][3])
        self.assertEqual('0,00', data_dict[13][4])
        self.assertEqual('1,00', data_dict[13][5])
        self.assertEqual([], data_dict[14])
        self.assertEqual('', data_dict[15][0])
        self.assertEqual('', data_dict[15][1])
        self.assertEqual('', data_dict[15][2])
        self.assertEqual('', data_dict[15][3])
        self.assertEqual('1,00', data_dict[15][5])
        self.assertEqual('0,21', data_dict[16][5])
        self.assertEqual('1,21', data_dict[17][5])
        self.assertEqual([], data_dict[18])
        self.assertIn('21%', data_dict[20][0])
        self.assertEqual('1,00', data_dict[20][1])
        self.assertEqual('0,21', data_dict[20][2])
        self.assertEqual([], data_dict[21])
        self.assertIn('Payment mode 01', data_dict[22][1])
        self.assertEqual('1,00', data_dict[26][1])
        self.assertEqual('', data_dict[27][1])

    def test_export_02(self):
        '''File with two rows (equal products, price and discount)'''
        wiz_export = self.env['wiz.account_invoice_export'].with_context({
            'active_ids': [self.invoice_02.id],
            'active_model': 'account.invoice',
            'active_id': self.invoice_02.id}).create({})
        wiz_export.button_accept()
        self.assertTrue(wiz_export.ffile)
        data_dict = self.get_data_dict(wiz_export)
        self.assertEqual(_(''), data_dict[1][1])
        self.assertEqual('', data_dict[1][1])
        self.assertEqual('11/08/2017', data_dict[2][1])
        self.assertEqual([], data_dict[3])
        self.assertEqual('CUST-123', data_dict[4][1])
        self.assertEqual(_('Customer 01'), data_dict[5][1])
        self.assertEqual(_('Calle Real, 33 18008'), data_dict[6][1])
        self.assertEqual(_('Granada'), data_dict[7][1])
        self.assertEqual('', data_dict[8][1])
        self.assertEqual('', data_dict[9][1])
        self.assertEqual('ES12345678Z', data_dict[10][1])
        self.assertEqual([], data_dict[11])
        self.assertEqual('T00001', data_dict[13][0])
        self.assertIn('Test template 1', data_dict[13][1])
        self.assertEqual('1,00', data_dict[13][2])
        self.assertEqual('1,00', data_dict[13][3])
        self.assertEqual('0,00', data_dict[13][4])
        self.assertEqual('1,00', data_dict[13][5])
        self.assertEqual('T00002', data_dict[14][0])
        self.assertIn('Test template 2', data_dict[14][1])
        self.assertEqual('2,00', data_dict[14][2])
        self.assertEqual('5,00', data_dict[14][3])
        self.assertEqual('0,00', data_dict[14][4])
        self.assertEqual('10,00', data_dict[14][5])
        self.assertEqual([], data_dict[15])
        self.assertEqual('', data_dict[16][0])
        self.assertEqual('', data_dict[16][1])
        self.assertEqual('', data_dict[16][2])
        self.assertEqual('', data_dict[16][3])
        self.assertEqual('11,00', data_dict[16][5])
        self.assertEqual('2,31', data_dict[17][5])
        self.assertEqual('13,31', data_dict[18][5])
        self.assertEqual([], data_dict[19])
        self.assertIn('21%', data_dict[21][0])
        self.assertEqual('11,00', data_dict[21][1])
        self.assertEqual('2,31', data_dict[21][2])
        self.assertEqual([], data_dict[22])
        self.assertIn('Payment mode 01', data_dict[23][1])
        self.assertEqual('3,00', data_dict[27][1])
        self.assertEqual('', data_dict[28][1])

    def test_export_03(self):
        '''File with two rows (equal product, equal price)'''
        wiz_export = self.env['wiz.account_invoice_export'].with_context({
            'active_ids': [self.invoice_03.id],
            'active_model': 'account.invoice',
            'active_id': self.invoice_03.id}).create({})
        wiz_export.button_accept()
        self.assertTrue(wiz_export.ffile)
        data_dict = self.get_data_dict(wiz_export)
        self.assertEqual(_(''), data_dict[1][1])
        self.assertEqual('', data_dict[1][1])
        self.assertEqual('11/08/2017', data_dict[2][1])
        self.assertEqual([], data_dict[3])
        self.assertEqual('CUST-123', data_dict[4][1])
        self.assertEqual(_('Customer 01'), data_dict[5][1])
        self.assertEqual(_('Calle Real, 33 18008'), data_dict[6][1])
        self.assertEqual(_('Granada'), data_dict[7][1])
        self.assertEqual('', data_dict[8][1])
        self.assertEqual('', data_dict[9][1])
        self.assertEqual('ES12345678Z', data_dict[10][1])
        self.assertEqual([], data_dict[11])
        self.assertEqual('T00001', data_dict[13][0])
        self.assertIn('Test template 1', data_dict[13][1])
        self.assertEqual('3,00', data_dict[13][2])
        self.assertEqual('1,00', data_dict[13][3])
        self.assertEqual('0,00', data_dict[13][4])
        self.assertEqual('3,00', data_dict[13][5])
        self.assertEqual([], data_dict[14])
        self.assertEqual('', data_dict[15][0])
        self.assertEqual('', data_dict[15][1])
        self.assertEqual('', data_dict[15][2])
        self.assertEqual('', data_dict[15][3])
        self.assertEqual('3,00', data_dict[15][5])
        self.assertEqual('0,63', data_dict[16][5])
        self.assertEqual('3,63', data_dict[17][5])
        self.assertEqual([], data_dict[18])
        self.assertIn('21%', data_dict[20][0])
        self.assertEqual('3,00', data_dict[20][1])
        self.assertEqual('0,63', data_dict[20][2])
        self.assertEqual([], data_dict[21])
        self.assertIn('Payment mode 01', data_dict[22][1])
        self.assertEqual('3,00', data_dict[26][1])
        self.assertEqual('', data_dict[27][1])

    def test_export_04(self):
        '''File with two rows (equal product, different price)'''
        wiz_export = self.env['wiz.account_invoice_export'].with_context({
            'active_ids': [self.invoice_04.id],
            'active_model': 'account.invoice',
            'active_id': self.invoice_04.id}).create({})
        wiz_export.button_accept()
        self.assertTrue(wiz_export.ffile)
        data_dict = self.get_data_dict(wiz_export)
        self.assertEqual(_(''), data_dict[1][1])
        self.assertEqual('', data_dict[1][1])
        self.assertEqual('11/08/2017', data_dict[2][1])
        self.assertEqual([], data_dict[3])
        self.assertEqual('CUST-123', data_dict[4][1])
        self.assertEqual(_('Customer 01'), data_dict[5][1])
        self.assertEqual(_('Calle Real, 33 18008'), data_dict[6][1])
        self.assertEqual(_('Granada'), data_dict[7][1])
        self.assertEqual('', data_dict[8][1])
        self.assertEqual('', data_dict[9][1])
        self.assertEqual('ES12345678Z', data_dict[10][1])
        self.assertEqual([], data_dict[11])
        self.assertEqual('T00001', data_dict[13][0])
        self.assertIn('Test template 1', data_dict[13][1])
        self.assertEqual('1,00', data_dict[13][2])
        self.assertEqual('1,00', data_dict[13][3])
        self.assertEqual('0,00', data_dict[13][4])
        self.assertEqual('1,00', data_dict[13][5])
        self.assertEqual('T00001', data_dict[14][0])
        self.assertIn('Test template 1', data_dict[14][1])
        self.assertEqual('2,00', data_dict[14][2])
        self.assertEqual('10,00', data_dict[14][3])
        self.assertEqual('0,00', data_dict[14][4])
        self.assertEqual('20,00', data_dict[14][5])
        self.assertEqual([], data_dict[15])
        self.assertEqual('', data_dict[16][0])
        self.assertEqual('', data_dict[16][1])
        self.assertEqual('', data_dict[16][2])
        self.assertEqual('', data_dict[16][3])
        self.assertEqual('21,00', data_dict[16][5])
        self.assertEqual('4,41', data_dict[17][5])
        self.assertEqual('25,41', data_dict[18][5])
        self.assertEqual([], data_dict[19])
        self.assertIn('21%', data_dict[21][0])
        self.assertEqual('21,00', data_dict[21][1])
        self.assertEqual('4,41', data_dict[21][2])
        self.assertEqual([], data_dict[22])
        self.assertIn('Payment mode 01', data_dict[23][1])
        self.assertEqual('3,00', data_dict[27][1])
        self.assertEqual('', data_dict[28][1])

    def test_export_05(self):
        '''File with three rows (two equal product, equal price)'''
        wiz_export = self.env['wiz.account_invoice_export'].with_context({
            'active_ids': [self.invoice_05.id],
            'active_model': 'account.invoice',
            'active_id': self.invoice_05.id}).create({})
        wiz_export.button_accept()
        self.assertTrue(wiz_export.ffile)
        data_dict = self.get_data_dict(wiz_export)
        self.assertEqual(_(''), data_dict[1][1])
        self.assertEqual('', data_dict[1][1])
        self.assertEqual('11/08/2017', data_dict[2][1])
        self.assertEqual([], data_dict[3])
        self.assertEqual('CUST-123', data_dict[4][1])
        self.assertEqual(_('Customer 01'), data_dict[5][1])
        self.assertEqual(_('Calle Real, 33 18008'), data_dict[6][1])
        self.assertEqual(_('Granada'), data_dict[7][1])
        self.assertEqual('', data_dict[8][1])
        self.assertEqual('', data_dict[9][1])
        self.assertEqual('ES12345678Z', data_dict[10][1])
        self.assertEqual([], data_dict[11])
        self.assertEqual('T00001', data_dict[13][0])
        self.assertIn('Test template 1', data_dict[13][1])
        self.assertEqual('5,00', data_dict[13][2])
        self.assertEqual('1,00', data_dict[13][3])
        self.assertEqual('0,00', data_dict[13][4])
        self.assertEqual('5,00', data_dict[13][5])
        self.assertEqual('T00002', data_dict[14][0])
        self.assertIn('Test template 2', data_dict[14][1])
        self.assertEqual('3,00', data_dict[14][2])
        self.assertEqual('10,00', data_dict[14][3])
        self.assertEqual('0,00', data_dict[14][4])
        self.assertEqual('30,00', data_dict[14][5])
        self.assertEqual([], data_dict[15])
        self.assertEqual('', data_dict[16][0])
        self.assertEqual('', data_dict[16][1])
        self.assertEqual('', data_dict[16][2])
        self.assertEqual('', data_dict[16][3])
        self.assertEqual('35,00', data_dict[16][5])
        self.assertEqual('7,35', data_dict[17][5])
        self.assertEqual('42,35', data_dict[18][5])
        self.assertEqual([], data_dict[19])
        self.assertIn('21%', data_dict[21][0])
        self.assertEqual('35,00', data_dict[21][1])
        self.assertEqual('7,35', data_dict[21][2])
        self.assertEqual([], data_dict[22])
        self.assertIn('Payment mode 01', data_dict[23][1])
        self.assertEqual('8,00', data_dict[27][1])
        self.assertEqual('', data_dict[28][1])
