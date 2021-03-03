# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import os

from openerp import _, exceptions
from openerp.tests.common import TransactionCase


class TestImportTemplateSaleAmazon(TransactionCase):

    def setUp(self):
        super(TestImportTemplateSaleAmazon, self).setUp()

    def get_sample(self, fname):
        return os.path.join(os.path.dirname(__file__), fname)

    def get_file_name(self, fname):
        return fname.split('/')[-1:][0]

    def create_payment_mode_test(self):
        payment_mode_type = self.env['payment.mode.type'].create({
            'name': 'Manual bank',
            'code': 'OURSBANK'})
        partner_bank_01 = self.env['res.partner.bank'].create({
            'bank_name': 'My bank',
            'state': 'iban',
            'acc_number': 'FR76 4242 4242 4242 4242 4242 424'})
        account_430 = self.env['account.account'].search([
            ('code', '=', '430000'),
        ], limit=1)
        if not account_430.exists():
            user_type = self.env['account.account.type'].search([
                ('code', '=', 'receivable'),
            ], limit=1)
            if not user_type:
                raise exceptions.Warning('Does not exist any account type.')
            account_430 = self.env['account.account'].create({
                'code': '430000',
                'name': 'Account 430',
                'type': 'receivable',
                'user_type': user_type.id,
                'currency_mode': 'current',
            })
        account_journal = self.env['account.journal'].create({
            'code': 'JJJI',
            'name': 'bank journal',
            'type': 'sale',
            'default_debit_account_id': account_430.id,
            'default_credit_account_id': account_430.id,
            'sequence_id': self.ref(
                'account.sequence_refund_purchase_journal'),
        })
        return self.env['payment.mode'].create({
            'name': 'Payment mode test',
            'bank_id': partner_bank_01.id,
            'type': payment_mode_type.id,
            'journal': account_journal.id,
        })

    def test_import_create_ok(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
        })
        fname = self.get_sample('sample_ok.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_1.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, 0)
        self.assertEquals(sales_1.amount_total, 17.31)
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(57.81 / 2, 2))
        self.assertEquals(sales_2.amount_untaxed, round(57.81 / 2, 2) * 2)
        self.assertEquals(sales_2.amount_tax, 0)
        self.assertEquals(sales_2.amount_total, round(57.81 / 2, 2) * 2)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_write_ok(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
        })
        partner_test = self.env['res.partner'].create({
            'name': 'Partner test',
            'customer': True,
        })
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': partner_test.id,
        })
        fname = self.get_sample('sample_ok.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_1.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, 0)
        self.assertEquals(sales_1.amount_total, 17.31)
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(57.81 / 2, 2))
        self.assertEquals(sales_2.amount_untaxed, round(57.81 / 2, 2) * 2)
        self.assertEquals(sales_2.amount_tax, 0)
        self.assertEquals(sales_2.amount_total, round(57.81 / 2, 2) * 2)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_default_wizard_values_create_ok(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
        })
        fname = self.get_sample('sample_ok.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({})
        sale_amazon.action_import_file()
        default_pricelist = self.env[
            'import.template.sale_amazon']._default_pricelist_id()
        default_carrier = self.env[
            'import.template.sale_amazon']._default_carrier_id()
        default_payment_mode = self.env[
            'import.template.sale_amazon']._default_payment_mode_id()
        self.assertEquals(sale_amazon.pricelist_id.id, default_pricelist.id)
        self.assertEquals(sale_amazon.carrier_id.id, default_carrier.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, default_payment_mode.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, default_pricelist.id)
        self.assertEquals(sale_amazon.carrier_id.id, default_carrier.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, default_payment_mode.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id.name, default_pricelist.name)
        self.assertEquals(sales_1.carrier_id.name, default_carrier.name)
        self.assertEquals(
            sales_1.payment_mode_id.name, default_payment_mode.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, 0)
        self.assertEquals(sales_1.amount_total, 17.31)
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, default_pricelist.name)
        self.assertEquals(sales_2.carrier_id.name, default_carrier.name)
        self.assertEquals(
            sales_2.payment_mode_id.name, default_payment_mode.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(57.81 / 2, 2))
        self.assertEquals(sales_2.amount_untaxed, round(57.81 / 2, 2) * 2)
        self.assertEquals(sales_2.amount_tax, 0)
        self.assertEquals(sales_2.amount_total, round(57.81 / 2, 2) * 2)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_default_wizard_values_write_ok(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
        })
        partner_test = self.env['res.partner'].create({
            'name': 'Partner test',
            'customer': True,
        })
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': partner_test.id,
        })
        fname = self.get_sample('sample_ok.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({})
        sale_amazon.action_import_file()
        default_pricelist = self.env[
            'import.template.sale_amazon']._default_pricelist_id()
        default_carrier = self.env[
            'import.template.sale_amazon']._default_carrier_id()
        default_payment_mode = self.env[
            'import.template.sale_amazon']._default_payment_mode_id()
        self.assertEquals(sale_amazon.pricelist_id.id, default_pricelist.id)
        self.assertEquals(sale_amazon.carrier_id.id, default_carrier.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, default_payment_mode.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, default_pricelist.id)
        self.assertEquals(sale_amazon.carrier_id.id, default_carrier.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, default_payment_mode.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id.name, default_pricelist.name)
        self.assertEquals(sales_1.carrier_id.name, default_carrier.name)
        self.assertEquals(
            sales_1.payment_mode_id.name, default_payment_mode.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, 0)
        self.assertEquals(sales_1.amount_total, 17.31)
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, default_pricelist.name)
        self.assertEquals(sales_2.carrier_id.name, default_carrier.name)
        self.assertEquals(
            sales_2.payment_mode_id.name, default_payment_mode.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(57.81 / 2, 2))
        self.assertEquals(sales_2.amount_untaxed, round(57.81 / 2, 2) * 2)
        self.assertEquals(sales_2.amount_tax, 0)
        self.assertEquals(sales_2.amount_total, round(57.81 / 2, 2) * 2)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_product_tax_create_ok(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        tax_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.ref('base.main_company'),
        })
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        fname = self.get_sample('sample_ok.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_1.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, round(17.31 * 0.21, 2))
        self.assertEquals(sales_1.amount_total, round(17.31 * 1.21, 2))
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(57.81 / 2, 2))
        self.assertEquals(sales_2.amount_untaxed, round(57.81 / 2, 2) * 2)
        self.assertEquals(sales_2.amount_tax, round(57.81 / 2 * 2 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.81 / 2 * 1.21, 2) * 2)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_product_tax_write_ok(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        tax_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.ref('base.main_company'),
        })
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        partner_test = self.env['res.partner'].create({
            'name': 'Partner test',
            'customer': True,
        })
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': partner_test.id,
        })
        fname = self.get_sample('sample_ok.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_1.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, round(17.31 * 0.21, 2))
        self.assertEquals(sales_1.amount_total, round(17.31 * 1.21, 2))
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(57.81 / 2, 2))
        self.assertEquals(sales_2.amount_untaxed, round(57.81 / 2, 2) * 2)
        self.assertEquals(sales_2.amount_tax, round(57.81 / 2 * 2 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.81 / 2 * 1.21, 2) * 2)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_order_id_empty_create_error(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        tax_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.ref('base.main_company'),
        })
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        fname = self.get_sample('sample_order_id_empty_error.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Column \'order_id\' cannot be empty.'),
            wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: ')])
        self.assertEquals(len(sales_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Column \'order_id\' cannot be empty.'),
            wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: ')])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(57.81 / 2, 2))
        self.assertEquals(sales_2.amount_untaxed, round(57.81 / 2, 2) * 2)
        self.assertEquals(sales_2.amount_tax, round(57.81 / 2 * 2 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.81 / 2 * 1.21, 2) * 2)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_order_id_empty_write_error(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        tax_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.ref('base.main_company'),
        })
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        partner_test = self.env['res.partner'].create({
            'name': 'Partner test',
            'customer': True,
        })
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: ',
            'partner_id': partner_test.id,
        })
        fname = self.get_sample('sample_order_id_empty_error.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Column \'order_id\' cannot be empty.'),
            wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: ')])
        self.assertEquals(len(sales_1), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Column \'order_id\' cannot be empty.'),
            wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: ')])
        self.assertEquals(len(sales_1), 1)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(57.81 / 2, 2))
        self.assertEquals(sales_2.amount_untaxed, round(57.81 / 2, 2) * 2)
        self.assertEquals(sales_2.amount_tax, round(57.81 / 2 * 2 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.81 / 2 * 1.21, 2) * 2)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_partner_id_empty_create_error(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        tax_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.ref('base.main_company'),
        })
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        fname = self.get_sample('sample_partner_id_empty_error.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Partner name  not found.'), wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Partner name  not found.'), wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'None')])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(57.81 / 2, 2))
        self.assertEquals(sales_2.amount_untaxed, round(57.81 / 2, 2) * 2)
        self.assertEquals(sales_2.amount_tax, round(57.81 / 2 * 2 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.81 / 2 * 1.21, 2) * 2)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_partner_id_empty_write_error(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        tax_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.ref('base.main_company'),
        })
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        partner_test = self.env['res.partner'].create({
            'name': 'Partner test',
            'customer': True,
        })
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': partner_test.id,
        })
        fname = self.get_sample('sample_partner_id_empty_error.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Partner name  not found.'), wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'None')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Partner name  not found.'), wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'None')])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Partner test')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(57.81 / 2, 2))
        self.assertEquals(sales_2.amount_untaxed, round(57.81 / 2, 2) * 2)
        self.assertEquals(sales_2.amount_tax, round(57.81 / 2 * 2 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.81 / 2 * 1.21, 2) * 2)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_default_code_empty_create_error(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        tax_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.ref('base.main_company'),
        })
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        fname = self.get_sample('sample_default_code_empty_error.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '2: Default code None not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Column \'product_id\' cannot be empty.'),
            wizard.line_ids[1].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '2: Default code None not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Column \'product_id\' cannot be empty.'),
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'None')])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(57.81 / 2, 2))
        self.assertEquals(sales_2.amount_untaxed, round(57.81 / 2, 2) * 2)
        self.assertEquals(sales_2.amount_tax, round(57.81 / 2 * 2 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.81 / 2 * 1.21, 2) * 2)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_default_code_empty_write_error(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        tax_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.ref('base.main_company'),
        })
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        partner_test = self.env['res.partner'].create({
            'name': 'Partner test',
            'customer': True,
        })
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': partner_test.id,
        })
        fname = self.get_sample('sample_default_code_empty_error.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '2: Default code None not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Column \'product_id\' cannot be empty.'),
            wizard.line_ids[1].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(len(sales_1.order_line), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '2: Default code None not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Column \'product_id\' cannot be empty.'),
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(len(sales_1.order_line), 0)
        self.assertEquals(sales_1.partner_id.name, 'Partner test')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(57.81 / 2, 2))
        self.assertEquals(sales_2.amount_untaxed, round(57.81 / 2, 2) * 2)
        self.assertEquals(sales_2.amount_tax, round(57.81 / 2 * 2 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.81 / 2 * 1.21, 2) * 2)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_duply_product_create_error(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        tax_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.ref('base.main_company'),
        })
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        self.env['product.product'].create({
            'name': 'Product test duply',
            'default_code': '92385',
            'list_price': 33,
            'type': 'product',
        })
        fname = self.get_sample('sample_ok.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '2: More than one product found for 92385.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '3: More than one product found for 92385.'),
            wizard.line_ids[1].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '2: More than one product found for 92385.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '3: More than one product found for 92385.'),
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)

    def test_import_duply_product_write_error(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        tax_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.ref('base.main_company'),
        })
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        self.env['product.product'].create({
            'name': 'Product test duply',
            'default_code': '92385',
            'list_price': 33,
            'type': 'product',
        })
        partner_test = self.env['res.partner'].create({
            'name': 'Partner test',
            'customer': True,
        })
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': partner_test.id,
        })
        fname = self.get_sample('sample_ok.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '2: More than one product found for 92385.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '3: More than one product found for 92385.'),
            wizard.line_ids[1].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(len(sales_1.order_line), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '2: More than one product found for 92385.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '3: More than one product found for 92385.'),
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(len(sales_1.order_line), 0)
        self.assertEquals(sales_1.partner_id.name, 'Partner test')
        self.assertNotEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertNotEquals(sales_1.partner_id.phone, '626795384')
        self.assertNotEquals(sales_1.partner_id.vat, 'ES01234567L')
        self.assertNotEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertNotEquals(sales_1.partner_id.street2, 'Casa')
        self.assertNotEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertNotEquals(sales_1.partner_id.zip, '08330')
        self.assertNotEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertNotEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertNotEquals(sales_1.pricelist_id.name, pricelist_test.name)
        self.assertNotEquals(sales_1.carrier_id.name, carrier_test.name)
        self.assertNotEquals(
            sales_1.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 0)
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)

    def test_import_duply_origin_error(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        tax_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.ref('base.main_company'),
        })
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        partner_test = self.env['res.partner'].create({
            'name': 'Partner test',
            'customer': True,
        })
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': partner_test.id,
        })
        partner_test2 = self.env['res.partner'].create({
            'name': 'Partner test 2',
            'customer': True,
        })
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': partner_test2.id,
        })
        fname = self.get_sample('sample_ok.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 2)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: More than one sale order with origin \'Amazon sale number: '
            '406-9428643-3124325\' has been found. The order details could '
            'not be imported.'),
            wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 2)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)

    def test_import_order_with_serveral_lines_create_ok(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        tax_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.ref('base.main_company'),
        })
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        self.env['product.product'].create({
            'name': 'Product test 2',
            'default_code': '50944',
            'list_price': 9,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        fname = self.get_sample('order_with_serveral_lines_ok.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'jt81lk8h6cb5n8p@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_1.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 2)
        self.assertEquals(
            sales_1.order_line[0].product_id.name, 'Product test')
        self.assertEquals(sales_1.order_line[0].product_uom_qty, 1)
        self.assertEquals(sales_1.order_line[0].price_unit, 17.31)
        self.assertEquals(
            sales_1.order_line[1].product_id.name, 'Product test 2')
        self.assertEquals(sales_1.order_line[1].product_uom_qty, 3)
        self.assertEquals(
            sales_1.order_line[1].price_unit, round(57.81 / 3, 2))
        self.assertEquals(sales_1.amount_untaxed, round(17.31 + 57.81, 2))
        self.assertEquals(
            sales_1.amount_tax, round(17.31 * 0.21 + 57.81 * 0.21, 2))
        self.assertEquals(
            sales_1.amount_total, round(17.31 * 1.21 + 57.81 * 1.21, 2))
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(17.31 / 2, 2))
        self.assertEquals(sales_2.amount_untaxed, round(17.31 / 2, 2) * 2)
        self.assertEquals(
            sales_2.amount_tax, round(sales_2.amount_untaxed * 0.21, 2))
        self.assertEquals(
            sales_2.amount_total, sales_2.amount_untaxed + sales_2.amount_tax)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_order_with_serveral_lines_write_draft_ok(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        tax_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.ref('base.main_company'),
        })
        product_test_1 = self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        self.env['product.product'].create({
            'name': 'Product test 2',
            'default_code': '50944',
            'list_price': 9,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        product_test_3 = self.env['product.product'].create({
            'name': 'Product test 3',
            'default_code': 'xxxxx',
            'list_price': 100,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        partner_test = self.env['res.partner'].create({
            'name': 'Partner test',
            'customer': True,
        })
        order = self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': partner_test.id,
        })
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': product_test_1.id,
            'product_uom_qty': 1,
            'product_uom': self.ref('product.product_uom_unit'),
        })
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': product_test_3.id,
            'product_uom_qty': 1,
            'product_uom': self.ref('product.product_uom_unit'),
        })
        fname = self.get_sample('order_with_serveral_lines_ok.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(len(sales_1.order_line), 2)
        self.assertEquals(
            sales_1.order_line[0].product_id.name, 'Product test')
        self.assertEquals(sales_1.order_line[0].product_uom_qty, 1)
        self.assertEquals(sales_1.order_line[0].price_unit, 10)
        self.assertEquals(
            sales_1.order_line[1].product_id.name, 'Product test 3')
        self.assertEquals(sales_1.order_line[1].product_uom_qty, 1)
        self.assertEquals(sales_1.order_line[1].price_unit, 100)
        self.assertEquals(sales_1.amount_untaxed, 10 + 100)
        self.assertEquals(sales_1.amount_tax, round(10 * 0.21 + 100 * 0.21, 2))
        self.assertEquals(
            sales_1.amount_total, round(10 * 1.21 + 100 * 1.21, 2))
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'jt81lk8h6cb5n8p@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_1.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 2)
        self.assertEquals(
            sales_1.order_line[0].product_id.name, 'Product test')
        self.assertEquals(sales_1.order_line[0].product_uom_qty, 1)
        self.assertEquals(sales_1.order_line[0].price_unit, 17.31)
        self.assertEquals(
            sales_1.order_line[1].product_id.name, 'Product test 2')
        self.assertEquals(sales_1.order_line[1].product_uom_qty, 3)
        self.assertEquals(
            sales_1.order_line[1].price_unit, round(57.81 / 3, 2))
        self.assertEquals(
            sales_1.amount_untaxed, round((17.31 + 57.81) / 3, 2) * 3)
        self.assertEquals(
            sales_1.amount_tax,
            round((17.31 * 0.21 + 57.81 * 0.21) * 3 / 3, 2))
        self.assertEquals(
            sales_1.amount_total,
            round((17.31 * 1.21 + 57.81 * 1.21) * 3 / 3, 2))
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(17.31 / 2, 2))
        self.assertEquals(sales_2.amount_untaxed, round(17.31 / 2, 2) * 2)
        self.assertEquals(
            sales_2.amount_tax, round(sales_2.amount_untaxed * 0.21, 2))
        self.assertEquals(
            sales_2.amount_total, sales_2.amount_untaxed + sales_2.amount_tax)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_order_with_serveral_lines_write_confirm_error(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        tax_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.ref('base.main_company'),
        })
        product_test_1 = self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        self.env['product.product'].create({
            'name': 'Product test 2',
            'default_code': '50944',
            'list_price': 9,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        product_test_3 = self.env['product.product'].create({
            'name': 'Product test 3',
            'default_code': 'xxxxx',
            'list_price': 100,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        partner_test = self.env['res.partner'].create({
            'name': 'Partner test',
            'customer': True,
        })
        order = self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': partner_test.id,
        })
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': product_test_1.id,
            'product_uom_qty': 1,
            'product_uom': self.ref('product.product_uom_unit'),
        })
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': product_test_3.id,
            'product_uom_qty': 1,
            'product_uom': self.ref('product.product_uom_unit'),
        })
        order.signal_workflow('order_confirm')
        fname = self.get_sample('order_with_serveral_lines_ok.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(len(sales_1.order_line), 2)
        self.assertNotEqual(sales_1.state, 'draft')
        self.assertEquals(
            sales_1.order_line[0].product_id.name, 'Product test')
        self.assertEquals(sales_1.order_line[0].product_uom_qty, 1)
        self.assertEquals(sales_1.order_line[0].price_unit, 10)
        self.assertEquals(
            sales_1.order_line[1].product_id.name, 'Product test 3')
        self.assertEquals(sales_1.order_line[1].product_uom_qty, 1)
        self.assertEquals(sales_1.order_line[1].price_unit, 100)
        self.assertEquals(sales_1.amount_untaxed, 10 + 100)
        self.assertEquals(sales_1.amount_tax, round(10 * 0.21 + 100 * 0.21, 2))
        self.assertEquals(
            sales_1.amount_total, round(10 * 1.21 + 100 * 1.21, 2))
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2, 3: The order with origin \'Amazon sale number: '
            '406-9428643-3124325\' cannot be modified because it is not in a '
            'draft state.'), wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Partner test')
        self.assertEquals(sales_1.partner_id.email, False)
        self.assertEquals(sales_1.partner_id.phone, False)
        self.assertEquals(sales_1.partner_id.vat, False)
        self.assertEquals(sales_1.partner_id.street, False)
        self.assertEquals(sales_1.partner_id.street2, False)
        self.assertEquals(sales_1.partner_id.city, False)
        self.assertEquals(sales_1.partner_id.zip, False)
        self.assertEquals(sales_1.partner_id.state_id.name, False)
        self.assertEquals(sales_1.partner_id.country_id.code, False)
        self.assertEquals(sales_1.pricelist_id.name, 'Public Pricelist')
        self.assertEquals(sales_1.payment_mode_id.name, False)
        self.assertEquals(len(sales_1.order_line), 2)
        self.assertEquals(
            sales_1.order_line[0].product_id.name, 'Product test')
        self.assertEquals(sales_1.order_line[0].product_uom_qty, 1)
        self.assertEquals(sales_1.order_line[0].price_unit, 10)
        self.assertEquals(
            sales_1.order_line[1].product_id.name, 'Product test 3')
        self.assertEquals(sales_1.order_line[1].product_uom_qty, 1)
        self.assertEquals(sales_1.order_line[1].price_unit, 100)
        self.assertEquals(sales_1.amount_untaxed, 10 + 100)
        self.assertEquals(
            sales_1.amount_tax, round(10 * 0.21 + 100 * 0.21, 2))
        self.assertEquals(
            sales_1.amount_total, round(10 * 1.21 + 100 * 1.21, 2))
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(17.31 / 2, 2))
        self.assertEquals(sales_2.amount_untaxed, round(17.31 / 2, 2) * 2)
        self.assertEquals(
            sales_2.amount_tax, round(sales_2.amount_untaxed * 0.21, 2))
        self.assertEquals(
            sales_2.amount_total, sales_2.amount_untaxed + sales_2.amount_tax)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_order_with_serveral_lines_duply_product_error(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        tax_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.ref('base.main_company'),
        })
        product_test_1 = self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        self.env['product.product'].create({
            'name': 'Product test 2',
            'default_code': '50944',
            'list_price': 9,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        product_test_3 = self.env['product.product'].create({
            'name': 'Product test 3',
            'default_code': 'xxxxx',
            'list_price': 100,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        partner_test = self.env['res.partner'].create({
            'name': 'Partner test',
            'customer': True,
        })
        order = self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': partner_test.id,
        })
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': product_test_1.id,
            'product_uom_qty': 1,
            'product_uom': self.ref('product.product_uom_unit'),
        })
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': product_test_3.id,
            'product_uom_qty': 1,
            'product_uom': self.ref('product.product_uom_unit'),
        })
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': partner_test.id,
        })
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': product_test_1.id,
            'product_uom_qty': 10,
            'product_uom': self.ref('product.product_uom_unit'),
        })
        fname = self.get_sample('order_with_serveral_lines_ok.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 2)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 2)
        for sale in sales_1:
            self.assertNotEquals(sale.partner_id.name, 'Esther')
            self.assertNotEquals(
                sale.partner_id.email, 'jt81lk8h6cb5n8p@marketplace.amazon.es')
            self.assertNotEquals(sale.partner_id.phone, '626795384')
            self.assertNotEquals(sale.partner_id.vat, 'ES01234567L')
            self.assertNotEquals(sale.partner_id.street, u'Calle Cañada 10')
            self.assertNotEquals(sale.partner_id.street2, 'Casa')
            self.assertNotEquals(sale.partner_id.city, 'Pamplona')
            self.assertNotEquals(sale.partner_id.zip, '08330')
            self.assertNotEquals(sale.partner_id.state_id.name, 'Texas')
            self.assertNotEquals(sale.partner_id.country_id.code, 'US')
            self.assertNotEquals(sale.pricelist_id.name, pricelist_test.name)
            self.assertNotEquals(sale.carrier_id.name, carrier_test.name)
            self.assertNotEquals(
                sale.payment_mode_id.name, payment_mode_test.name)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(17.31 / 2, 2))
        self.assertEquals(sales_2.amount_untaxed, round(17.31 / 2, 2) * 2)
        self.assertEquals(
            sales_2.amount_tax, round(sales_2.amount_untaxed * 0.21, 2))
        self.assertEquals(
            sales_2.amount_total, sales_2.amount_untaxed + sales_2.amount_tax)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_new_fields_ok(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        tax_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.ref('base.main_company'),
        })
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        self.env['product.product'].create({
            'name': 'Product test 2',
            'default_code': '50944',
            'list_price': 9,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        fname = self.get_sample('sample_new_fields_ok.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_1.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.delay, 10)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, round(17.31 * 0.21, 2))
        self.assertEquals(sales_1.amount_total, round(17.31 * 1.21, 2))
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.delay, 7)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(57.81 / 2, 2))
        self.assertEquals(sales_2.amount_untaxed, round(57.81 / 2, 2) * 2)
        self.assertEquals(sales_2.amount_tax, round(57.81 / 2 * 2 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.81 / 2 * 1.21, 2) * 2)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_new_fields_error(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        tax_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.ref('base.main_company'),
        })
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        self.env['product.product'].create({
            'name': 'Product test 2',
            'default_code': '50944',
            'list_price': 9,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        fname = self.get_sample('sample_new_fields_error.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '2: The \'company_id\' column is a relational field and there is '
            'no defined function to convert it.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The \'company_id\' column is a relational field and there is '
            'no defined function to convert it.'), wizard.line_ids[1].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '2: The \'company_id\' column is a relational field and there is '
            'no defined function to convert it.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The \'company_id\' column is a relational field and there is '
            'no defined function to convert it.'), wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)

    def test_import_create_disordered_columns_ok(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
        })
        fname = self.get_sample('sample_disordered_columns_ok.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_1.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.order_line.delay, 10)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, 0)
        self.assertEquals(sales_1.amount_total, 17.31)
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(57.81 / 2, 2))
        self.assertEquals(sales_2.order_line.delay, 7)
        self.assertEquals(sales_2.amount_untaxed, round(57.81 / 2, 2) * 2)
        self.assertEquals(sales_2.amount_tax, 0)
        self.assertEquals(sales_2.amount_total, round(57.81 / 2, 2) * 2)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_write_disordered_columns_ok(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        tax_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.ref('base.main_company'),
        })
        product_test_1 = self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        self.env['product.product'].create({
            'name': 'Product test 2',
            'default_code': '50944',
            'list_price': 9,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        product_test_3 = self.env['product.product'].create({
            'name': 'Product test 3',
            'default_code': 'xxxxx',
            'list_price': 100,
            'type': 'product',
            'taxes_id': [(6, 0, [tax_21.id])]
        })
        partner_test = self.env['res.partner'].create({
            'name': 'Partner test',
            'customer': True,
        })
        order = self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': partner_test.id,
        })
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': product_test_1.id,
            'product_uom_qty': 1,
            'product_uom': self.ref('product.product_uom_unit'),
        })
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': product_test_3.id,
            'product_uom_qty': 1,
            'product_uom': self.ref('product.product_uom_unit'),
        })
        fname = self.get_sample('sample_disordered_columns_ok.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(len(sales_1.order_line), 2)
        self.assertEquals(
            sales_1.order_line[0].product_id.name, 'Product test')
        self.assertEquals(sales_1.order_line[0].product_uom_qty, 1)
        self.assertEquals(sales_1.order_line[0].price_unit, 10)
        self.assertEquals(sales_1.order_line[0].delay, 0)
        self.assertEquals(
            sales_1.order_line[1].product_id.name, 'Product test 3')
        self.assertEquals(sales_1.order_line[1].product_uom_qty, 1)
        self.assertEquals(sales_1.order_line[1].price_unit, 100)
        self.assertEquals(sales_1.order_line[1].delay, 0)
        self.assertEquals(sales_1.amount_untaxed, 10 + 100)
        self.assertEquals(sales_1.amount_tax, round(10 * 0.21 + 100 * 0.21, 2))
        self.assertEquals(
            sales_1.amount_total, round(10 * 1.21 + 100 * 1.21, 2))
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_1.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.order_line.delay, 10)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, round(17.31 * 0.21, 2))
        self.assertEquals(sales_1.amount_total, round(17.31 * 1.21, 2))
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(57.81 / 2, 2))
        self.assertEquals(sales_2.order_line.delay, 7)
        self.assertEquals(sales_2.amount_untaxed, round(57.81 / 2, 2) * 2)
        self.assertEquals(sales_2.amount_tax, round(57.81 / 2 * 2 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.81 / 2 * 1.21, 2) * 2)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_with_shipping_price_create_ok(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
        })
        shipping_product_test = self.env['product.product'].create({
            'name': 'Shipping costs',
            'type': 'service',
            'default_code': 'SHIPPTEST',
            'standard_price': 3,
            'list_price': 5,
        })
        fname = self.get_sample('sample_with_shipping_price_ok.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
                'shipping_product_id': shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_1.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, 0)
        self.assertEquals(sales_1.amount_total, 17.31)
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 2)
        self.assertEquals(
            sales_2.order_line[0].product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line[0].product_uom_qty, 2)
        self.assertEquals(
            sales_2.order_line[0].price_unit, round(57.81 / 2, 2))
        self.assertEquals(
            sales_2.order_line[1].product_id.name, shipping_product_test.name)
        self.assertEquals(sales_2.order_line[1].product_uom_qty, 1)
        self.assertEquals(sales_2.order_line[1].price_unit, 4.24)
        self.assertEquals(
            sales_2.amount_untaxed, round(57.81 / 2, 2) * 2 + 4.24)
        self.assertEquals(sales_2.amount_tax, 0)
        self.assertEquals(sales_2.amount_total, round(57.81 / 2, 2) * 2 + 4.24)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_with_shipping_price_write_ok(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
        })
        shipping_product_test = self.env['product.product'].create({
            'name': 'Shipping costs',
            'type': 'service',
            'default_code': 'SHIPPTEST',
            'standard_price': 3,
            'list_price': 5,
        })
        partner_test = self.env['res.partner'].create({
            'name': 'Partner test',
            'customer': True,
        })
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': partner_test.id,
        })
        fname = self.get_sample('sample_with_shipping_price_ok.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
                'shipping_product_id': shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_1.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, 0)
        self.assertEquals(sales_1.amount_total, 17.31)
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 2)
        self.assertEquals(
            sales_2.order_line[0].product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line[0].product_uom_qty, 2)
        self.assertEquals(
            sales_2.order_line[0].price_unit, round(57.81 / 2, 2))
        self.assertEquals(
            sales_2.order_line[1].product_id.name, shipping_product_test.name)
        self.assertEquals(sales_2.order_line[1].product_uom_qty, 1)
        self.assertEquals(sales_2.order_line[1].price_unit, 4.24)
        self.assertEquals(
            sales_2.amount_untaxed, round(57.81 / 2, 2) * 2 + 4.24)
        self.assertEquals(sales_2.amount_tax, 0)
        self.assertEquals(sales_2.amount_total, round(57.81 / 2, 2) * 2 + 4.24)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_new_state_id_without_country_create_ok(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
        })
        fname = self.get_sample(
            'sample_new_state_id_without_country_create_ok.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Country code \'None\' not found; \'No country\' is assigned.'),
            wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        no_country = self.env['res.country'].search([
            ('name', '=', _('No country')),
        ])
        self.assertEquals(len(no_country), 0)
        state = self.env['res.country.state'].search([
            ('name', '=', 'Granada'),
            ('country_id', '=', no_country.id),
        ])
        self.assertEquals(len(state), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Country code \'None\' not found; \'No country\' is assigned.'),
            wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Granada')
        self.assertEquals(sales_1.partner_id.country_id.code, '00')
        self.assertEquals(sales_1.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_1.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, 0)
        self.assertEquals(sales_1.amount_total, 17.31)
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(57.81 / 2, 2))
        self.assertEquals(sales_2.amount_untaxed, round(57.81 / 2, 2) * 2)
        self.assertEquals(sales_2.amount_tax, 0)
        self.assertEquals(sales_2.amount_total, round(57.81 / 2, 2) * 2)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_new_state_id_without_country_write_ok(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
        })
        partner_test = self.env['res.partner'].create({
            'name': 'Partner test',
            'customer': True,
        })
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': partner_test.id,
        })
        fname = self.get_sample(
            'sample_new_state_id_without_country_create_ok.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Country code \'None\' not found; \'No country\' is assigned.'),
            wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        no_country = self.env['res.country'].search([
            ('name', '=', _('No country')),
        ])
        self.assertEquals(len(no_country), 0)
        state = self.env['res.country.state'].search([
            ('name', '=', 'Granada'),
            ('country_id', '=', no_country.id),
        ])
        self.assertEquals(len(state), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Country code \'None\' not found; \'No country\' is assigned.'),
            wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Granada')
        self.assertEquals(sales_1.partner_id.country_id.code, '00')
        self.assertEquals(sales_1.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_1.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, 0)
        self.assertEquals(sales_1.amount_total, 17.31)
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(57.81 / 2, 2))
        self.assertEquals(sales_2.amount_untaxed, round(57.81 / 2, 2) * 2)
        self.assertEquals(sales_2.amount_tax, 0)
        self.assertEquals(sales_2.amount_total, round(57.81 / 2, 2) * 2)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_state_id_without_country_create_ok(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
        })
        fname = self.get_sample('sample_state_id_without_country.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Country code \'None\' not found; \'No country\' is assigned.'),
            wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Country code \'None\' not found; \'No country\' is assigned.'),
            wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, '00')
        self.assertEquals(sales_1.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_1.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, 0)
        self.assertEquals(sales_1.amount_total, 17.31)
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(57.81 / 2, 2))
        self.assertEquals(sales_2.amount_untaxed, round(57.81 / 2, 2) * 2)
        self.assertEquals(sales_2.amount_tax, 0)
        self.assertEquals(sales_2.amount_total, round(57.81 / 2, 2) * 2)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_state_id_without_country_write_ok(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
        })
        partner_test = self.env['res.partner'].create({
            'name': 'Partner test',
            'customer': True,
        })
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': partner_test.id,
        })
        fname = self.get_sample('sample_state_id_without_country.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Country code \'None\' not found; \'No country\' is assigned.'),
            wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Country code \'None\' not found; \'No country\' is assigned.'),
            wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, '00')
        self.assertEquals(sales_1.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_1.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, 0)
        self.assertEquals(sales_1.amount_total, 17.31)
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(57.81 / 2, 2))
        self.assertEquals(sales_2.amount_untaxed, round(57.81 / 2, 2) * 2)
        self.assertEquals(sales_2.amount_tax, 0)
        self.assertEquals(sales_2.amount_total, round(57.81 / 2, 2) * 2)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_empty_state_id_empty_country_id_create_ok(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
        })
        fname = self.get_sample('sample_empty_state_id_empty_country_id.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Country code \'None\' not found; \'No country\' is assigned.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '2: State name \'None\' not found; not assigned.'),
            wizard.line_ids[1].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Country code \'None\' not found; \'No country\' is assigned.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '2: State name \'None\' not found; not assigned.'),
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertFalse(sales_1.partner_id.state_id.exists())
        self.assertEquals(sales_1.partner_id.country_id.code, '00')
        self.assertEquals(sales_1.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_1.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, 0)
        self.assertEquals(sales_1.amount_total, 17.31)
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(57.81 / 2, 2))
        self.assertEquals(sales_2.amount_untaxed, round(57.81 / 2, 2) * 2)
        self.assertEquals(sales_2.amount_tax, 0)
        self.assertEquals(sales_2.amount_total, round(57.81 / 2, 2) * 2)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_empty_state_id_empty_country_id_write_ok(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
        })
        partner_test = self.env['res.partner'].create({
            'name': 'Partner test',
            'customer': True,
        })
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': partner_test.id,
        })
        fname = self.get_sample('sample_empty_state_id_empty_country_id.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Country code \'None\' not found; \'No country\' is assigned.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '2: State name \'None\' not found; not assigned.'),
            wizard.line_ids[1].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Country code \'None\' not found; \'No country\' is assigned.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '2: State name \'None\' not found; not assigned.'),
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertFalse(sales_1.partner_id.state_id.exists())
        self.assertEquals(sales_1.partner_id.country_id.code, '00')
        self.assertEquals(sales_1.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_1.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, 0)
        self.assertEquals(sales_1.amount_total, 17.31)
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(57.81 / 2, 2))
        self.assertEquals(sales_2.amount_untaxed, round(57.81 / 2, 2) * 2)
        self.assertEquals(sales_2.amount_tax, 0)
        self.assertEquals(sales_2.amount_total, round(57.81 / 2, 2) * 2)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_empty_no_required_fields_create_ok(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
        })
        fname = self.get_sample('sample_empty_no_required_fields.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 5)
        self.assertEquals(wizard.total_warn, 5)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Email data not found; not assigned'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Phone data not found; not assigned'), wizard.line_ids[1].name)
        self.assertIn(_(
            '2: Street data not found; not assigned'), wizard.line_ids[2].name)
        self.assertIn(_(
            '2: City data not found; not assigned'), wizard.line_ids[3].name)
        self.assertIn(_(
            '2: Zip data not found; not assigned'), wizard.line_ids[4].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 5)
        self.assertEquals(wizard.total_warn, 5)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Email data not found; not assigned'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Phone data not found; not assigned'), wizard.line_ids[1].name)
        self.assertIn(_(
            '2: Street data not found; not assigned'), wizard.line_ids[2].name)
        self.assertIn(_(
            '2: City data not found; not assigned'), wizard.line_ids[3].name)
        self.assertIn(_(
            '2: Zip data not found; not assigned'), wizard.line_ids[4].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(sales_1.partner_id.email, '')
        self.assertEquals(sales_1.partner_id.phone, '')
        self.assertEquals(sales_1.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_1.partner_id.street, '')
        self.assertEquals(sales_1.partner_id.street2, '')
        self.assertEquals(sales_1.partner_id.city, '')
        self.assertEquals(sales_1.partner_id.zip, '')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_1.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, 0)
        self.assertEquals(sales_1.amount_total, 17.31)
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(57.81 / 2, 2))
        self.assertEquals(sales_2.amount_untaxed, round(57.81 / 2, 2) * 2)
        self.assertEquals(sales_2.amount_tax, 0)
        self.assertEquals(sales_2.amount_total, round(57.81 / 2, 2) * 2)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_empty_no_required_fields_street_write_ok(self):
        partner_carrier = self.env['res.partner'].create({
            'name': 'Carrier partner',
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
        })
        pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'type': 'sale',
        })
        version_pricelist_test = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist_test.id,
            'name': 'Version test',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_pricelist_test.id,
            'name': 'Item pricelist test',
            'base': 1,
            'price_surcharge': 0.99,
        })
        carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'partner_id': partner_carrier.id,
            'product_id': product_carrier.id,
        })
        payment_mode_test = self.create_payment_mode_test()
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
        })
        partner_test = self.env['res.partner'].create({
            'name': 'Partner test',
            'customer': True,
        })
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': partner_test.id,
        })
        fname = self.get_sample('sample_empty_no_required_fields.txt')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_amazon.template_sale_amazon').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_amazon = self.env['import.template.sale_amazon'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': pricelist_test.id,
                'carrier_id': carrier_test.id,
                'payment_mode_id': payment_mode_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 5)
        self.assertEquals(wizard.total_warn, 5)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Email data not found; not assigned'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Phone data not found; not assigned'), wizard.line_ids[1].name)
        self.assertIn(_(
            '2: Street data not found; not assigned'), wizard.line_ids[2].name)
        self.assertIn(_(
            '2: City data not found; not assigned'), wizard.line_ids[3].name)
        self.assertIn(_(
            '2: Zip data not found; not assigned'), wizard.line_ids[4].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, carrier_test.id)
        self.assertEquals(sale_amazon.payment_mode_id.id, payment_mode_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 5)
        self.assertEquals(wizard.total_warn, 5)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Email data not found; not assigned'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Phone data not found; not assigned'), wizard.line_ids[1].name)
        self.assertIn(_(
            '2: Street data not found; not assigned'), wizard.line_ids[2].name)
        self.assertIn(_(
            '2: City data not found; not assigned'), wizard.line_ids[3].name)
        self.assertIn(_(
            '2: Zip data not found; not assigned'), wizard.line_ids[4].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther')])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325')])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(sales_1.partner_id.email, '')
        self.assertEquals(sales_1.partner_id.phone, '')
        self.assertEquals(sales_1.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_1.partner_id.street, '')
        self.assertEquals(sales_1.partner_id.street2, '')
        self.assertEquals(sales_1.partner_id.city, '')
        self.assertEquals(sales_1.partner_id.zip, '')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_1.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, 0)
        self.assertEquals(sales_1.amount_total, 17.31)
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez')])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320')])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, 'ES01234567L')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, carrier_test.name)
        self.assertEquals(sales_2.payment_mode_id.name, payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, round(57.81 / 2, 2))
        self.assertEquals(sales_2.amount_untaxed, round(57.81 / 2, 2) * 2)
        self.assertEquals(sales_2.amount_tax, 0)
        self.assertEquals(sales_2.amount_total, round(57.81 / 2, 2) * 2)
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')
