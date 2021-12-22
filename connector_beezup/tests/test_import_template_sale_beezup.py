###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import logging
import os

from odoo import _
from odoo.tests.common import TransactionCase

_log = logging.getLogger(__name__)


class TestImportTemplateSaleBeezup(TransactionCase):

    def setUp(self):
        super(TestImportTemplateSaleBeezup, self).setUp()
        company = self.env.ref('base.main_company')
        self.tax_21 = self.env['account.tax'].create({
            'company_id': company.id,
            'name': 'Tax test 21%',
            'type_tax_use': 'sale',
            'amount_type': 'percent',
            'amount': 21,
        })
        account_110401 = self.env['account.account'].create({
            'code': '110401',
            'user_type_id': self.ref('account.data_account_type_liquidity'),
            'name': 'Cash account',
        })
        self.cash_journal_test = self.env['account.journal'].create({
            'code': 'CASH',
            'name': 'Cash journal test',
            'type': 'cash',
            'default_debit_account_id': account_110401.id,
            'default_credit_account_id': account_110401.id,
        })
        self.fiscal_position_es = self.env['account.fiscal.position'].create({
            'name': 'Fiscal position es',
            'country_id': self.env.ref('base.es').id
        })
        self.fiscal_position_fr = self.env['account.fiscal.position'].create({
            'name': 'Fiscal position fr',
            'country_id': self.env.ref('base.fr').id
        })
        self.tax_10 = self.env['account.tax'].create({
            'company_id': company.id,
            'name': 'Tax test 10%',
            'type_tax_use': 'sale',
            'amount_type': 'percent',
            'amount': 10,
        })
        self.tax_7 = self.env['account.tax'].create({
            'company_id': company.id,
            'name': 'Tax test 7%',
            'type_tax_use': 'sale',
            'amount_type': 'percent',
            'amount': 7,
        })
        self.env['account.fiscal.position.tax'].create({
            'position_id': self.fiscal_position_fr.id,
            'tax_src_id': self.tax_21.id,
            'tax_dest_id': self.tax_10.id,
        })
        tax_15 = self.env['account.tax'].search([
            ('amount_type', '=', 'percent'),
            ('amount', '=', 15),
            ('type_tax_use', '=', 'sale'),
        ])
        self.env['account.fiscal.position.tax'].create({
            'position_id': self.fiscal_position_fr.id,
            'tax_src_id': tax_15.id,
            'tax_dest_id': self.tax_10.id,
        })
        partner_account = self.env['account.account'].create({
            'code': 'xxx',
            'user_type_id': self.ref('account.data_account_type_receivable'),
            'name': 'Partner account',
            'reconcile': True,
        })
        self.account_700 = self.env['account.account'].create({
            'code': '700000',
            'name': '700000',
            'user_type_id': self.ref('account.data_account_type_revenue'),
        })
        product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
            'property_account_income_id': self.account_700.id,

            'type': 'service',
            'taxes_id': [(6, 0, [self.tax_21.id])],
        })
        self.carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'delivery_type': 'fixed',
            'product_id': product_carrier.id,
            'fixed_price': 99.99,
        })
        self.partner_test1 = self.env['res.partner'].create({
            'name': 'Partner test 1',
            'customer': True,
            'property_account_receivable_id': partner_account.id,
            'property_account_position_id': self.fiscal_position_es.id,
        })
        self.partner_test2 = self.env['res.partner'].create({
            'name': 'Partner test 2',
            'customer': True,
            'property_account_receivable_id': partner_account.id,
            'property_account_position_id': self.fiscal_position_es.id,
        })
        self.partner_parent_test = self.env['res.partner'].create({
            'name': 'Partner parent test',
            'customer': True,
            'vat': '12345678A',
            'property_account_receivable_id': partner_account.id,
            'property_account_position_id': self.fiscal_position_es.id,
        })
        self.payment_mode_test = self.env['account.payment.mode'].create({
            'name': 'Payment mode customer',
            'payment_method_id': self.env.ref(
                'account.account_payment_method_manual_in').id,
            'payment_type': 'inbound',
            'bank_account_link': 'variable',
        })
        self.product1 = self.env['product.product'].create({
            'name': 'Product test 1',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
            'property_account_income_id': self.account_700.id,
            'invoice_policy': 'delivery',
            'taxes_id': [(6, 0, [self.tax_21.id])],
        })
        self.product2 = self.env['product.product'].create({
            'name': 'Product test 2',
            'default_code': '91277',
            'list_price': 100,
            'type': 'product',
            'property_account_income_id': self.account_700.id,
            'invoice_policy': 'delivery',
            'taxes_id': [(6, 0, [self.tax_21.id])],
        })
        self.product3 = self.env['product.product'].create({
            'name': 'Product test 3',
            'default_code': '52469',
            'list_price': 100,
            'type': 'product',
            'property_account_income_id': self.account_700.id,
            'invoice_policy': 'delivery',
            'taxes_id': [(6, 0, [self.tax_21.id])],
        })
        self.product4 = self.env['product.product'].create({
            'name': 'Product test 4',
            'default_code': '52470',
            'list_price': 100,
            'type': 'product',
            'property_account_income_id': self.account_700.id,
            'invoice_policy': 'delivery',
            'taxes_id': [(6, 0, [self.tax_21.id])],
        })
        self.product5 = self.env['product.product'].create({
            'name': 'Product test 5',
            'default_code': '52258',
            'list_price': 100,
            'type': 'product',
            'property_account_income_id': self.account_700.id,
            'invoice_policy': 'delivery',
            'taxes_id': [(6, 0, [self.tax_21.id])],
        })
        self.shipping_product_test = self.env['product.product'].create({
            'name': 'Shipping costs',
            'type': 'service',
            'default_code': 'SHIPPTEST',
            'standard_price': 3,
            'list_price': 5,
            'property_account_income_id': self.account_700.id,
            'invoice_policy': 'delivery',
            'taxes_id': [(6, 0, [self.tax_21.id])],
        })
        self.product_inv_policy_order = self.env['product.product'].create({
            'name': 'Product test invoice policy order',
            'default_code': '44444',
            'list_price': 10,
            'type': 'product',
            'property_account_income_id': self.account_700.id,
            'invoice_policy': 'order',
            'taxes_id': [(6, 0, [self.tax_21.id])],
        })
        self.pricelist_test = self.env['product.pricelist'].create({
            'name': 'Test pricelis',
            'item_ids': [
                (0, 0, {
                    'applied_on': '3_global',
                    'base': 'list_price',
                    'price_surcharge': 0.99,
                }),
            ],
        })
        company.beezup_pricelist_id = self.pricelist_test.id

    def create_fiscal_position_no_country(self):
        fposition_nocountry = self.env['account.fiscal.position'].create({
            'name': 'Fiscal position no country',
            'country_id': self.env.ref('import_template.no_country').id
        })
        self.env['account.fiscal.position.tax'].create({
            'position_id': fposition_nocountry.id,
            'tax_src_id': self.tax_21.id,
            'tax_dest_id': self.tax_7.id,
        })
        return fposition_nocountry

    def get_file(self, fname):
        return os.path.join(os.path.dirname(__file__), fname)

    def get_file_name(self, fname):
        return fname.split('/')[-1:][0]

    def check_manual_confirm_and_transfer(self, sale):
        num_lines = len(sale.order_line)
        self.assertEquals(sale.state, 'draft')
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        self.assertEquals(len(sale.order_line), num_lines)
        picking_out = sale.picking_ids
        picking_out.action_confirm()
        picking_out.action_assign()
        for move in picking_out.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_out.action_done()
        self.assertEquals(picking_out.state, 'done')
        self.assertEquals(len(sale.order_line), num_lines)

    def test_import_create_ok(self):
        fname = self.get_file('sample_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertFalse(sales_1.partner_id.parent_id)
        self.assertEquals(sales_1.partner_invoice_id, sales_1.partner_id)
        self.assertEquals(sales_1.partner_shipping_id, sales_1.partner_id)
        self.assertEquals(sales_1.partner_id.email, 'ray@test.com')
        self.assertEquals(sales_1.partner_id.phone, '911000111')
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '45631')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_fr)
        self.assertEquals(
            sales_1.fiscal_position_id,
            self.fiscal_position_fr)
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.10, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_10)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.10, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.10, 2))
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(
            sales_1.picking_ids[0].partner_id, sales_1.partner_id)
        self.assertEquals(
            sales_1.picking_ids[1].partner_id, sales_1.partner_id)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(sales_1.invoice_ids.partner_id, sales_1.partner_id)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id, self.cash_journal_test)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.fiscal_position_id, self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_write_ok(self):
        self.env['sale.order'].create({
            'origin': 'Beezup sale number: 407-3315028-8261943',
            'partner_id': self.partner_test1.id,
        })
        fname = self.get_file('sample_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertFalse(sales_1.partner_id.parent_id)
        self.assertEquals(sales_1.partner_invoice_id, sales_1.partner_id)
        self.assertEquals(sales_1.partner_shipping_id, sales_1.partner_id)
        self.assertEquals(sales_1.partner_id.email, 'ray@test.com')
        self.assertEquals(sales_1.partner_id.phone, '911000111')
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '45631')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_fr)
        self.assertEquals(
            sales_1.fiscal_position_id,
            self.fiscal_position_fr)
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        price_unit = round(23.95 / 1.10, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_10)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.10, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.10, 2))
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(
            sales_1.picking_ids[0].partner_id, sales_1.partner_id)
        self.assertEquals(
            sales_1.picking_ids[1].partner_id, sales_1.partner_id)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(sales_1.invoice_ids.partner_id, sales_1.partner_id)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id, self.cash_journal_test)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.fiscal_position_id, self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_create_ok_force_partner(self):
        fname = self.get_file('sample_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
                'force_partner': True,
                'parent_partner_id': self.partner_parent_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertEquals(
            sales_1.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_1.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_1.partner_shipping_id, sales_1.partner_id)
        self.assertEquals(sales_1.partner_id.email, 'ray@test.com')
        self.assertEquals(sales_1.partner_id.phone, '911000111')
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '45631')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.partner_parent_test.property_account_position_id)
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.21, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(
            sales_1.picking_ids[0].partner_id, sales_1.partner_id)
        self.assertEquals(
            sales_1.picking_ids[1].partner_id, sales_1.partner_id)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.partner_id, self.partner_parent_test)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id, self.cash_journal_test)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertEquals(
            sales_2.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.partner_parent_test.property_account_position_id)
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_write_ok_force_partner(self):
        self.env['sale.order'].create({
            'origin': 'Beezup sale number: 407-3315028-8261943',
            'partner_id': self.partner_test1.id,
        })
        fname = self.get_file('sample_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
                'force_partner': True,
                'parent_partner_id': self.partner_parent_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertEquals(
            sales_1.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_1.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_1.partner_shipping_id, sales_1.partner_id)
        self.assertEquals(sales_1.partner_id.email, 'ray@test.com')
        self.assertEquals(sales_1.partner_id.phone, '911000111')
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '45631')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.partner_parent_test.property_account_position_id)
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.21, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(
            sales_1.picking_ids[0].partner_id, sales_1.partner_id)
        self.assertEquals(
            sales_1.picking_ids[1].partner_id, sales_1.partner_id)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.partner_id, self.partner_parent_test)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id, self.cash_journal_test)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertEquals(
            sales_2.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.partner_parent_test.property_account_position_id)
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_default_wizard_values_create_ok(self):
        def _check_default_vals():
            self.default_pricelist = self.env[
                'import.template.sale_beezup']._default_pricelist_id()
            self.assertTrue(sale_beezup.pricelist_id)
            self.assertEquals(sale_beezup.pricelist_id, self.default_pricelist)
            self.default_carrier = self.env[
                'import.template.sale_beezup']._default_carrier_id()
            self.assertTrue(sale_beezup.carrier_id)
            self.assertEquals(sale_beezup.carrier_id, self.default_carrier)
            self.default_payment_mode = self.env[
                'import.template.sale_beezup']._default_payment_mode_id()
            self.assertTrue(sale_beezup.payment_mode_id)
            self.assertEquals(
                sale_beezup.payment_mode_id, self.default_payment_mode)
            default_shipping_product = self.env[
                'import.template.sale_beezup']._default_shipping_product_id()
            self.assertTrue(sale_beezup.shipping_product_id)
            self.assertEquals(
                sale_beezup.shipping_product_id, default_shipping_product)
            default_journal_payment = self.env[
                'import.template.sale_beezup']._default_journal_payment_id()
            self.assertTrue(sale_beezup.journal_payment_id)
            self.assertEquals(
                sale_beezup.journal_payment_id, default_journal_payment)
            default_journal_sale = self.env[
                'import.template.sale_beezup']._default_journal_sale_id()
            self.assertTrue(sale_beezup.journal_sale_id)
            self.assertEquals(
                sale_beezup.journal_sale_id, default_journal_sale)
            default_partner_account = self.env[
                'import.template.sale_beezup']._default_partner_account_id()
            self.assertTrue(sale_beezup.partner_account_id)
            self.assertEquals(
                sale_beezup.partner_account_id, default_partner_account)

        fname = self.get_file('sample_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({})
        sale_beezup.action_import_file()
        _check_default_vals()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        _check_default_vals()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertFalse(sales_1.partner_id.parent_id)
        self.assertEquals(sales_1.partner_invoice_id, sales_1.partner_id)
        self.assertEquals(sales_1.partner_shipping_id, sales_1.partner_id)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertEquals(sales_1.partner_id.email, 'ray@test.com')
        self.assertEquals(sales_1.partner_id.phone, '911000111')
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '45631')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_fr)
        self.assertEquals(
            sales_1.pricelist_id, self.default_pricelist)
        self.assertEquals(sales_1.carrier_id, self.default_carrier)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.default_payment_mode.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.10, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_10)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.10, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.10, 2))
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(
            sales_1.picking_ids[0].partner_id, sales_1.partner_id)
        self.assertEquals(
            sales_1.picking_ids[1].partner_id, sales_1.partner_id)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(sales_1.invoice_ids.partner_id, sales_1.partner_id)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        default_journal_payment = self.env[
            'import.template.sale_beezup']._default_journal_payment_id()
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id,
            default_journal_payment)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.default_pricelist)
        self.assertEquals(sales_2.carrier_id, self.default_carrier)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.default_payment_mode.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_default_wizard_values_write_ok(self):
        def _check_default_vals():
            self.default_pricelist = self.env[
                'import.template.sale_beezup']._default_pricelist_id()
            self.assertTrue(sale_beezup.pricelist_id)
            self.assertEquals(sale_beezup.pricelist_id, self.default_pricelist)
            self.default_carrier = self.env[
                'import.template.sale_beezup']._default_carrier_id()
            self.assertTrue(sale_beezup.carrier_id)
            self.assertEquals(sale_beezup.carrier_id, self.default_carrier)
            self.default_payment_mode = self.env[
                'import.template.sale_beezup']._default_payment_mode_id()
            self.assertTrue(sale_beezup.payment_mode_id)
            self.assertEquals(
                sale_beezup.payment_mode_id, self.default_payment_mode)
            default_shipping_product = self.env[
                'import.template.sale_beezup']._default_shipping_product_id()
            self.assertTrue(sale_beezup.shipping_product_id)
            self.assertEquals(
                sale_beezup.shipping_product_id, default_shipping_product)
            default_journal_payment = self.env[
                'import.template.sale_beezup']._default_journal_payment_id()
            self.assertTrue(sale_beezup.journal_payment_id)
            self.assertEquals(
                sale_beezup.journal_payment_id, default_journal_payment)
            default_journal_sale = self.env[
                'import.template.sale_beezup']._default_journal_sale_id()
            self.assertTrue(sale_beezup.journal_sale_id)
            self.assertEquals(
                sale_beezup.journal_sale_id, default_journal_sale)
            default_partner_account = self.env[
                'import.template.sale_beezup']._default_partner_account_id()
            self.assertTrue(sale_beezup.partner_account_id)
            self.assertEquals(
                sale_beezup.partner_account_id, default_partner_account)

        self.env['sale.order'].create({
            'origin': 'Beezup sale number: 407-3315028-8261943',
            'partner_id': self.partner_test1.id,
        })
        fname = self.get_file('sample_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({})
        sale_beezup.action_import_file()
        _check_default_vals()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        _check_default_vals()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertFalse(sales_1.partner_id.parent_id)
        self.assertEquals(sales_1.partner_invoice_id, sales_1.partner_id)
        self.assertEquals(sales_1.partner_shipping_id, sales_1.partner_id)
        self.assertEquals(sales_1.partner_id.email, 'ray@test.com')
        self.assertEquals(sales_1.partner_id.phone, '911000111')
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '45631')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_fr)
        self.assertEquals(
            sales_1.pricelist_id, self.default_pricelist)
        self.assertEquals(sales_1.carrier_id, self.default_carrier)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.default_payment_mode.name)
        self.assertEquals(len(sales_1.order_line), 1)
        price_unit = round(23.95 / 1.10, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_10)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.10, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.10, 2))
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(
            sales_1.picking_ids[0].partner_id, sales_1.partner_id)
        self.assertEquals(
            sales_1.picking_ids[1].partner_id, sales_1.partner_id)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(sales_1.invoice_ids.partner_id, sales_1.partner_id)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        default_journal_payment = self.env[
            'import.template.sale_beezup']._default_journal_payment_id()
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id,
            default_journal_payment)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.default_pricelist)
        self.assertEquals(sales_2.carrier_id, self.default_carrier)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.default_payment_mode.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_default_wizard_values_create_ok_force_partner(self):
        def _check_default_vals():
            self.default_pricelist = self.env[
                'import.template.sale_beezup']._default_pricelist_id()
            self.assertTrue(sale_beezup.pricelist_id)
            self.assertEquals(sale_beezup.pricelist_id, self.default_pricelist)
            self.default_carrier = self.env[
                'import.template.sale_beezup']._default_carrier_id()
            self.assertTrue(sale_beezup.carrier_id)
            self.assertEquals(sale_beezup.carrier_id, self.default_carrier)
            self.default_payment_mode = self.env[
                'import.template.sale_beezup']._default_payment_mode_id()
            self.assertTrue(sale_beezup.payment_mode_id)
            self.assertEquals(
                sale_beezup.payment_mode_id, self.default_payment_mode)
            default_shipping_product = self.env[
                'import.template.sale_beezup']._default_shipping_product_id()
            self.assertTrue(sale_beezup.shipping_product_id)
            self.assertEquals(
                sale_beezup.shipping_product_id, default_shipping_product)
            default_journal_payment = self.env[
                'import.template.sale_beezup']._default_journal_payment_id()
            self.assertTrue(sale_beezup.journal_payment_id)
            self.assertEquals(
                sale_beezup.journal_payment_id, default_journal_payment)
            default_journal_sale = self.env[
                'import.template.sale_beezup']._default_journal_sale_id()
            self.assertTrue(sale_beezup.journal_sale_id)
            self.assertEquals(
                sale_beezup.journal_sale_id, default_journal_sale)
            default_partner_account = self.env[
                'import.template.sale_beezup']._default_partner_account_id()
            self.assertTrue(sale_beezup.partner_account_id)
            self.assertEquals(
                sale_beezup.partner_account_id, default_partner_account)

        fname = self.get_file('sample_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'force_partner': True,
                'parent_partner_id': self.partner_parent_test.id,
            })
        sale_beezup.action_import_file()
        _check_default_vals()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        _check_default_vals()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertEquals(
            sales_1.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_1.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_1.partner_shipping_id, sales_1.partner_id)
        self.assertEquals(sales_1.partner_id.email, 'ray@test.com')
        self.assertEquals(sales_1.partner_id.phone, '911000111')
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '45631')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.partner_parent_test.property_account_position_id)
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(
            sales_1.pricelist_id, self.default_pricelist)
        self.assertEquals(sales_1.carrier_id, self.default_carrier)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.default_payment_mode.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.21, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(
            sales_1.picking_ids[0].partner_id, sales_1.partner_id)
        self.assertEquals(
            sales_1.picking_ids[1].partner_id, sales_1.partner_id)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.partner_id, self.partner_parent_test)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        default_journal_payment = self.env[
            'import.template.sale_beezup']._default_journal_payment_id()
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id,
            default_journal_payment)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertEquals(
            sales_2.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.partner_parent_test.property_account_position_id)
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.default_pricelist)
        self.assertEquals(sales_2.carrier_id, self.default_carrier)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.default_payment_mode.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_default_wizard_values_write_ok_force_partner(self):
        def _check_default_vals():
            self.default_pricelist = self.env[
                'import.template.sale_beezup']._default_pricelist_id()
            self.assertTrue(sale_beezup.pricelist_id)
            self.assertEquals(sale_beezup.pricelist_id, self.default_pricelist)
            self.default_carrier = self.env[
                'import.template.sale_beezup']._default_carrier_id()
            self.assertTrue(sale_beezup.carrier_id)
            self.assertEquals(sale_beezup.carrier_id, self.default_carrier)
            self.default_payment_mode = self.env[
                'import.template.sale_beezup']._default_payment_mode_id()
            self.assertTrue(sale_beezup.payment_mode_id)
            self.assertEquals(
                sale_beezup.payment_mode_id, self.default_payment_mode)
            default_shipping_product = self.env[
                'import.template.sale_beezup']._default_shipping_product_id()
            self.assertTrue(sale_beezup.shipping_product_id)
            self.assertEquals(
                sale_beezup.shipping_product_id, default_shipping_product)
            default_journal_payment = self.env[
                'import.template.sale_beezup']._default_journal_payment_id()
            self.assertTrue(sale_beezup.journal_payment_id)
            self.assertEquals(
                sale_beezup.journal_payment_id, default_journal_payment)
            default_journal_sale = self.env[
                'import.template.sale_beezup']._default_journal_sale_id()
            self.assertTrue(sale_beezup.journal_sale_id)
            self.assertEquals(
                sale_beezup.journal_sale_id, default_journal_sale)
            default_partner_account = self.env[
                'import.template.sale_beezup']._default_partner_account_id()
            self.assertTrue(sale_beezup.partner_account_id)
            self.assertEquals(
                sale_beezup.partner_account_id, default_partner_account)

        self.env['sale.order'].create({
            'origin': 'Beezup sale number: 407-3315028-8261943',
            'partner_id': self.partner_test1.id,
        })
        fname = self.get_file('sample_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'force_partner': True,
                'parent_partner_id': self.partner_parent_test.id,
            })
        sale_beezup.action_import_file()
        _check_default_vals()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        _check_default_vals()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertEquals(
            sales_1.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_1.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_1.partner_shipping_id, sales_1.partner_id)
        self.assertEquals(sales_1.partner_id.email, 'ray@test.com')
        self.assertEquals(sales_1.partner_id.phone, '911000111')
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '45631')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.partner_parent_test.property_account_position_id)
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(
            sales_1.pricelist_id, self.default_pricelist)
        self.assertEquals(sales_1.carrier_id, self.default_carrier)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.default_payment_mode.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.21, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(
            sales_1.picking_ids[0].partner_id, sales_1.partner_id)
        self.assertEquals(
            sales_1.picking_ids[1].partner_id, sales_1.partner_id)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.partner_id, self.partner_parent_test)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        default_journal_payment = self.env[
            'import.template.sale_beezup']._default_journal_payment_id()
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id,
            default_journal_payment)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertEquals(
            sales_2.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.partner_parent_test.property_account_position_id)
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.default_pricelist)
        self.assertEquals(sales_2.carrier_id, self.default_carrier)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.default_payment_mode.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_order_id_empty_create_error(self):
        fname = self.get_file('sample_order_id_empty_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Column \'order_id\' cannot be empty.'),
            wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: ')])
        self.assertEquals(len(sales_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: '),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Column \'order_id\' cannot be empty.'),
            wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: '),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_order_id_empty_write_error(self):
        self.env['sale.order'].create({
            'origin': 'Beezup sale number: ',
            'partner_id': self.partner_test1.id,
        })
        fname = self.get_file('sample_order_id_empty_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Column \'order_id\' cannot be empty.'),
            wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: ')])
        self.assertEquals(len(sales_1), 1)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: '),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Partner test 1')
        self.assertFalse(sales_1.partner_id.email)
        self.assertFalse(sales_1.partner_id.phone)
        self.assertFalse(sales_1.partner_id.mobile)
        self.assertFalse(sales_1.partner_id.vat)
        self.assertFalse(sales_1.partner_id.street)
        self.assertFalse(sales_1.partner_id.street2)
        self.assertFalse(sales_1.partner_id.city)
        self.assertFalse(sales_1.partner_id.zip)
        self.assertFalse(sales_1.partner_id.state_id)
        self.assertFalse(sales_1.partner_id.country_id)
        self.assertEquals(len(sales_1.order_line), 0)
        self.assertEquals(sales_1.state, 'draft')
        self.assertEquals(len(sales_1.picking_ids), 0)
        self.assertEquals(len(sales_1.invoice_ids), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_order_id_empty_create_error_force_partner(self):
        fname = self.get_file('sample_order_id_empty_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
                'force_partner': True,
                'parent_partner_id': self.partner_parent_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Column \'order_id\' cannot be empty.'),
            wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: ')])
        self.assertEquals(len(sales_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: '),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Column \'order_id\' cannot be empty.'),
            wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: '),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertEquals(
            sales_2.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.partner_parent_test.property_account_position_id)
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_order_id_empty_write_error_force_partner(self):
        self.env['sale.order'].create({
            'origin': 'Beezup sale number: ',
            'partner_id': self.partner_test1.id,
        })
        fname = self.get_file('sample_order_id_empty_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
                'force_partner': True,
                'parent_partner_id': self.partner_parent_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Column \'order_id\' cannot be empty.'),
            wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: ')])
        self.assertEquals(len(sales_1), 1)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: '),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Partner test 1')
        self.assertFalse(sales_1.partner_id.email)
        self.assertFalse(sales_1.partner_id.phone)
        self.assertFalse(sales_1.partner_id.mobile)
        self.assertFalse(sales_1.partner_id.vat)
        self.assertFalse(sales_1.partner_id.street)
        self.assertFalse(sales_1.partner_id.street2)
        self.assertFalse(sales_1.partner_id.city)
        self.assertFalse(sales_1.partner_id.zip)
        self.assertFalse(sales_1.partner_id.state_id)
        self.assertFalse(sales_1.partner_id.country_id)
        self.assertEquals(len(sales_1.order_line), 0)
        self.assertEquals(sales_1.state, 'draft')
        self.assertEquals(len(sales_1.picking_ids), 0)
        self.assertEquals(len(sales_1.invoice_ids), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertEquals(
            sales_2.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.partner_parent_test.property_account_position_id)
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_partner_id_empty_create_error(self):
        fname = self.get_file('sample_partner_id_empty_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Partner empty not found.'), wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', ''),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Partner empty not found.'), wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', ''),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_partner_id_empty_write_error(self):
        self.env['sale.order'].create({
            'origin': 'Beezup sale number: 407-3315028-8261943',
            'partner_id': self.partner_test1.id,
        })
        fname = self.get_file('sample_partner_id_empty_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Partner empty not found.'), wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943')])
        self.assertEquals(len(sales_1), 1)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Partner empty not found.'), wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Partner test 1')
        self.assertFalse(sales_1.partner_id.email)
        self.assertFalse(sales_1.partner_id.phone)
        self.assertFalse(sales_1.partner_id.mobile)
        self.assertFalse(sales_1.partner_id.vat)
        self.assertFalse(sales_1.partner_id.street)
        self.assertFalse(sales_1.partner_id.street2)
        self.assertFalse(sales_1.partner_id.city)
        self.assertFalse(sales_1.partner_id.zip)
        self.assertFalse(sales_1.partner_id.state_id)
        self.assertFalse(sales_1.partner_id.country_id)
        self.assertFalse(len(sales_1.order_line), 0)
        self.assertEquals(sales_1.state, 'draft')
        self.assertEquals(len(sales_1.picking_ids), 0)
        self.assertEquals(len(sales_1.invoice_ids), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_partner_id_empty_create_error_force_partner(self):
        fname = self.get_file('sample_partner_id_empty_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
                'force_partner': True,
                'parent_partner_id': self.partner_parent_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Partner empty not found.'), wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', ''),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Partner empty not found.'), wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', ''),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertEquals(
            sales_2.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.partner_parent_test.property_account_position_id)
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_partner_id_empty_write_error_force_partner(self):
        self.env['sale.order'].create({
            'origin': 'Beezup sale number: 407-3315028-8261943',
            'partner_id': self.partner_test1.id,
        })
        fname = self.get_file('sample_partner_id_empty_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
                'force_partner': True,
                'parent_partner_id': self.partner_parent_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Partner empty not found.'), wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943')])
        self.assertEquals(len(sales_1), 1)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Partner empty not found.'), wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Partner test 1')
        self.assertFalse(sales_1.partner_id.email)
        self.assertFalse(sales_1.partner_id.phone)
        self.assertFalse(sales_1.partner_id.mobile)
        self.assertFalse(sales_1.partner_id.vat)
        self.assertFalse(sales_1.partner_id.street)
        self.assertFalse(sales_1.partner_id.street2)
        self.assertFalse(sales_1.partner_id.city)
        self.assertFalse(sales_1.partner_id.zip)
        self.assertFalse(sales_1.partner_id.state_id)
        self.assertFalse(sales_1.partner_id.country_id)
        self.assertFalse(len(sales_1.order_line), 0)
        self.assertEquals(sales_1.state, 'draft')
        self.assertEquals(len(sales_1.picking_ids), 0)
        self.assertEquals(len(sales_1.invoice_ids), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertEquals(
            sales_2.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.partner_parent_test.property_account_position_id)
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_default_code_empty_create_error(self):
        fname = self.get_file('sample_default_code_empty_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Default code empty not found.'), wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Default code empty not found.'), wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_default_code_empty_write_error(self):
        self.env['sale.order'].create({
            'origin': 'Beezup sale number: 407-3315028-8261943',
            'partner_id': self.partner_test1.id,
        })
        fname = self.get_file('sample_default_code_empty_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Default code empty not found.'), wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943')])
        self.assertEquals(len(sales_1), 1)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Default code empty not found.'), wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Partner test 1')
        self.assertFalse(sales_1.partner_id.email)
        self.assertFalse(sales_1.partner_id.phone)
        self.assertFalse(sales_1.partner_id.mobile)
        self.assertFalse(sales_1.partner_id.vat)
        self.assertFalse(sales_1.partner_id.street)
        self.assertFalse(sales_1.partner_id.street2)
        self.assertFalse(sales_1.partner_id.city)
        self.assertFalse(sales_1.partner_id.zip)
        self.assertFalse(sales_1.partner_id.state_id)
        self.assertFalse(sales_1.partner_id.country_id)
        self.assertFalse(len(sales_1.order_line), 0)
        self.assertEquals(sales_1.state, 'draft')
        self.assertEquals(len(sales_1.picking_ids), 0)
        self.assertEquals(len(sales_1.invoice_ids), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_default_code_empty_create_error_force_partner(self):
        fname = self.get_file('sample_default_code_empty_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
                'force_partner': True,
                'parent_partner_id': self.partner_parent_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Default code empty not found.'), wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Default code empty not found.'), wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertEquals(
            sales_2.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.partner_parent_test.property_account_position_id)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_default_code_empty_write_error_force_partner(self):
        self.env['sale.order'].create({
            'origin': 'Beezup sale number: 407-3315028-8261943',
            'partner_id': self.partner_test1.id,
        })
        fname = self.get_file('sample_default_code_empty_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
                'force_partner': True,
                'parent_partner_id': self.partner_parent_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Default code empty not found.'), wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943')])
        self.assertEquals(len(sales_1), 1)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Default code empty not found.'), wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Partner test 1')
        self.assertFalse(sales_1.partner_id.email)
        self.assertFalse(sales_1.partner_id.phone)
        self.assertFalse(sales_1.partner_id.mobile)
        self.assertFalse(sales_1.partner_id.vat)
        self.assertFalse(sales_1.partner_id.street)
        self.assertFalse(sales_1.partner_id.street2)
        self.assertFalse(sales_1.partner_id.city)
        self.assertFalse(sales_1.partner_id.zip)
        self.assertFalse(sales_1.partner_id.state_id)
        self.assertFalse(sales_1.partner_id.country_id)
        self.assertFalse(len(sales_1.order_line), 0)
        self.assertEquals(sales_1.state, 'draft')
        self.assertEquals(len(sales_1.picking_ids), 0)
        self.assertEquals(len(sales_1.invoice_ids), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertEquals(
            sales_2.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.partner_parent_test.property_account_position_id)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_duply_product_create_error(self):
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
            'taxes_id': [(6, 0, [self.tax_21.id])]
        })
        self.env['product.product'].create({
            'name': 'Product test duply',
            'default_code': '92385',
            'list_price': 33,
            'type': 'product',
        })
        fname = self.get_file('sample_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: More than one product found for 92385.'),
            wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: More than one product found for 92385.'),
            wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_duply_product_write_error(self):
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
            'taxes_id': [(6, 0, [self.tax_21.id])]
        })
        self.env['product.product'].create({
            'name': 'Product test duply',
            'default_code': '92385',
            'list_price': 33,
            'type': 'product',
        })
        self.env['sale.order'].create({
            'origin': 'Beezup sale number: 407-3315028-8261943',
            'partner_id': self.partner_test1.id,
        })
        fname = self.get_file('sample_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: More than one product found for 92385.'),
            wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943')])
        self.assertEquals(len(sales_1), 1)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: More than one product found for 92385.'),
            wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Partner test 1')
        self.assertFalse(sales_1.partner_id.email)
        self.assertFalse(sales_1.partner_id.phone)
        self.assertFalse(sales_1.partner_id.mobile)
        self.assertFalse(sales_1.partner_id.vat)
        self.assertFalse(sales_1.partner_id.street)
        self.assertFalse(sales_1.partner_id.street2)
        self.assertFalse(sales_1.partner_id.city)
        self.assertFalse(sales_1.partner_id.zip)
        self.assertFalse(sales_1.partner_id.state_id)
        self.assertFalse(sales_1.partner_id.country_id)
        self.assertFalse(len(sales_1.order_line), 0)
        self.assertEquals(sales_1.state, 'draft')
        self.assertEquals(len(sales_1.picking_ids), 0)
        self.assertEquals(len(sales_1.invoice_ids), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_duply_product_create_error_force_partner(self):
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
            'taxes_id': [(6, 0, [self.tax_21.id])]
        })
        self.env['product.product'].create({
            'name': 'Product test duply',
            'default_code': '92385',
            'list_price': 33,
            'type': 'product',
        })
        fname = self.get_file('sample_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
                'force_partner': True,
                'parent_partner_id': self.partner_parent_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: More than one product found for 92385.'),
            wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: More than one product found for 92385.'),
            wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertEquals(
            sales_2.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.partner_parent_test.property_account_position_id)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_duply_product_write_error_force_partner(self):
        self.env['product.product'].create({
            'name': 'Product test',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
            'taxes_id': [(6, 0, [self.tax_21.id])]
        })
        self.env['product.product'].create({
            'name': 'Product test duply',
            'default_code': '92385',
            'list_price': 33,
            'type': 'product',
        })
        self.env['sale.order'].create({
            'origin': 'Beezup sale number: 407-3315028-8261943',
            'partner_id': self.partner_test1.id,
        })
        fname = self.get_file('sample_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
                'force_partner': True,
                'parent_partner_id': self.partner_parent_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: More than one product found for 92385.'),
            wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943')])
        self.assertEquals(len(sales_1), 1)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: More than one product found for 92385.'),
            wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Partner test 1')
        self.assertFalse(sales_1.partner_id.email)
        self.assertFalse(sales_1.partner_id.phone)
        self.assertFalse(sales_1.partner_id.mobile)
        self.assertFalse(sales_1.partner_id.vat)
        self.assertFalse(sales_1.partner_id.street)
        self.assertFalse(sales_1.partner_id.street2)
        self.assertFalse(sales_1.partner_id.city)
        self.assertFalse(sales_1.partner_id.zip)
        self.assertFalse(sales_1.partner_id.state_id)
        self.assertFalse(sales_1.partner_id.country_id)
        self.assertFalse(len(sales_1.order_line), 0)
        self.assertEquals(sales_1.state, 'draft')
        self.assertEquals(len(sales_1.picking_ids), 0)
        self.assertEquals(len(sales_1.invoice_ids), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertEquals(
            sales_2.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.partner_parent_test.property_account_position_id)
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_duply_origin_error(self):
        self.env['sale.order'].create({
            'origin': 'Beezup sale number: 407-3315028-8261943',
            'partner_id': self.partner_test1.id,
        })
        partner_test2 = self.env['res.partner'].create({
            'name': 'Partner test 2',
            'customer': True,
        })
        self.env['sale.order'].create({
            'origin': 'Beezup sale number: 407-3315028-8261943',
            'partner_id': partner_test2.id,
        })
        fname = self.get_file('sample_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943')])
        self.assertEquals(len(sales_1), 2)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: More than one sale order with origin \'Beezup sale number: '
            '407-3315028-8261943\' has been found. The order details could '
            'not be imported.'),
            wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ], order='id desc')
        self.assertEquals(len(sales_1), 2)
        self.assertEquals(sales_1[0].partner_id.name, 'Partner test 2')
        self.assertEquals(sales_1[1].partner_id.name, 'Partner test 1')
        self.assertFalse(sales_1[0].partner_id.email)
        self.assertFalse(sales_1[0].partner_id.phone)
        self.assertFalse(sales_1[0].partner_id.mobile)
        self.assertFalse(sales_1[0].partner_id.vat)
        self.assertFalse(sales_1[0].partner_id.street)
        self.assertFalse(sales_1[0].partner_id.street2)
        self.assertFalse(sales_1[0].partner_id.city)
        self.assertFalse(sales_1[0].partner_id.zip)
        self.assertFalse(sales_1[0].partner_id.state_id)
        self.assertFalse(sales_1[0].partner_id.country_id)
        self.assertFalse(len(sales_1[0].order_line), 0)
        self.assertEquals(sales_1[0].state, 'draft')
        self.assertEquals(len(sales_1[0].picking_ids), 0)
        self.assertEquals(len(sales_1[0].invoice_ids), 0)
        self.assertFalse(sales_1[1].partner_id.email)
        self.assertFalse(sales_1[1].partner_id.phone)
        self.assertFalse(sales_1[1].partner_id.mobile)
        self.assertFalse(sales_1[1].partner_id.vat)
        self.assertFalse(sales_1[1].partner_id.street)
        self.assertFalse(sales_1[1].partner_id.street2)
        self.assertFalse(sales_1[1].partner_id.city)
        self.assertFalse(sales_1[1].partner_id.zip)
        self.assertFalse(sales_1[1].partner_id.state_id)
        self.assertFalse(sales_1[1].partner_id.country_id)
        self.assertFalse(len(sales_1[1].order_line), 0)
        self.assertEquals(sales_1[1].state, 'draft')
        self.assertEquals(len(sales_1[1].picking_ids), 0)
        self.assertEquals(len(sales_1[1].invoice_ids), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_create_order_totalprice_not_match(self):
        fname = self.get_file('order_totalprice_not_match.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: The amount total in order with origin \'Beezup sale number: '
            '407-3315028-8261943\' does not match with Odoo calcules:\nTotal '
            'amount in file: 99999.0\nTotal amount in Odoo: 23.95.'),
            wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertFalse(sales_1.partner_id.parent_id)
        self.assertEquals(sales_1.partner_invoice_id, sales_1.partner_id)
        self.assertEquals(sales_1.partner_shipping_id, sales_1.partner_id)
        self.assertEquals(sales_1.partner_id.email, 'ray@test.com')
        self.assertEquals(sales_1.partner_id.phone, '911000111')
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '45631')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_fr)
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.10, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_10)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.10, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.10, 2))
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(
            sales_1.picking_ids[0].partner_id, sales_1.partner_id)
        self.assertEquals(
            sales_1.picking_ids[1].partner_id, sales_1.partner_id)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(sales_1.invoice_ids.partner_id, sales_1.partner_id)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id, self.cash_journal_test)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_write_order_totalprice_not_match(self):
        self.env['sale.order'].create({
            'origin': 'Beezup sale number: 407-3315028-8261943',
            'partner_id': self.partner_test1.id,
        })
        fname = self.get_file('order_totalprice_not_match.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: The amount total in order with origin \'Beezup sale number: '
            '407-3315028-8261943\' does not match with Odoo calcules:\nTotal '
            'amount in file: 99999.0\nTotal amount in Odoo: 23.95.'),
            wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertFalse(sales_1.partner_id.parent_id)
        self.assertEquals(sales_1.partner_invoice_id, sales_1.partner_id)
        self.assertEquals(sales_1.partner_shipping_id, sales_1.partner_id)
        self.assertEquals(sales_1.partner_id.email, 'ray@test.com')
        self.assertEquals(sales_1.partner_id.phone, '911000111')
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '45631')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_fr)
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.10, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_10)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.10, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.10, 2))
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(
            sales_1.picking_ids[0].partner_id, sales_1.partner_id)
        self.assertEquals(
            sales_1.picking_ids[1].partner_id, sales_1.partner_id)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(sales_1.invoice_ids.partner_id, sales_1.partner_id)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id, self.cash_journal_test)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_order_with_serveral_lines_create_ok(self):
        fname = self.get_file('order_with_serveral_lines_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'journal_payment_id': self.cash_journal_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_3 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 405-9692877-4031515'),
        ])
        self.assertEquals(len(sales_3), 0)
        partner_3 = self.env['res.partner'].search([
            ('name', '=', 'Juan Rute'),
        ])
        self.assertEquals(len(partner_3), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertEquals(sales_1.partner_id.email, 'ray@test.com')
        self.assertEquals(sales_1.partner_id.phone, '911000111')
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '45631')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_fr)
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.10, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_10)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.10, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.10, 2))
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id, self.cash_journal_test)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)
        partner_3 = self.env['res.partner'].search([
            ('name', '=', 'Juan Rute'),
        ])
        self.assertEquals(len(partner_3), 1)
        sales_3 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 405-9692877-4031515'),
        ])
        self.assertEquals(len(sales_3), 1)
        self.assertEquals(sales_3.partner_id.name, 'Juan Rute')
        self.assertEquals(sales_3.partner_id.email, 'juan@test.es')
        self.assertEquals(sales_3.partner_id.phone, '910123123')
        self.assertEquals(sales_3.partner_id.mobile, '666112233')
        self.assertEquals(sales_3.partner_id.vat, '')
        self.assertEquals(sales_3.partner_id.street, 'Calle Sol, 22')
        self.assertEquals(sales_3.partner_id.street2, 'Villa Sotea')
        self.assertEquals(sales_3.partner_id.city, 'Biarritz')
        self.assertEquals(sales_3.partner_id.zip, '64200')
        self.assertEquals(sales_3.partner_id.state_id.name, 'Biarritz')
        self.assertEquals(sales_3.partner_id.state_id.code, '00Biarritz')
        self.assertEquals(sales_3.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_3.partner_id.property_account_position_id,
            self.fiscal_position_fr)
        self.assertEquals(sales_3.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_3.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_3.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_3.order_line), 6)
        for line in sales_3.order_line:
            self.assertEquals(line.tax_id, self.tax_10)
        line_product_52469 = sales_3.order_line.filtered(
            lambda ln: ln.product_id.default_code == '52469')
        self.assertTrue(line_product_52469)
        self.assertEquals(line_product_52469.product_id.name, 'Product test 3')
        self.assertEquals(line_product_52469.product_uom_qty, 2)
        price_unit_product_52469 = round(37.54 / 1.10, 2)
        self.assertEquals(
            line_product_52469.price_unit, price_unit_product_52469)
        line_product_52470 = sales_3.order_line.filtered(
            lambda ln: ln.product_id.default_code == '52470')
        self.assertTrue(line_product_52470)
        self.assertEquals(line_product_52470.product_id.name, 'Product test 4')
        self.assertEquals(line_product_52470.product_uom_qty, 2)
        price_unit_product_52470 = round(43.33 / 1.10, 2)
        self.assertEquals(
            line_product_52470.price_unit, price_unit_product_52470)
        line_product_52258 = sales_3.order_line.filtered(
            lambda ln: ln.product_id.default_code == '52258')
        self.assertTrue(line_product_52258)
        self.assertEquals(line_product_52258.product_id.name, 'Product test 5')
        self.assertEquals(line_product_52258.product_uom_qty, 1)
        price_unit_product_52258 = round(36.93 / 1.10, 2)
        self.assertEquals(
            line_product_52258.price_unit, price_unit_product_52258)
        price_unit_ship_prods_52469_52470 = round(5.98 / 1.10, 2)
        ship_line_prods_52469_52470 = sales_3.order_line.filtered(
            lambda ln: ln.product_id == self.shipping_product_test
            and ln.price_unit == price_unit_ship_prods_52469_52470)
        self.assertEquals(len(ship_line_prods_52469_52470), 2)
        for ship_line in ship_line_prods_52469_52470:
            self.assertEquals(
                ship_line.product_id.name, 'Shipping costs')
            self.assertEquals(ship_line.product_uom_qty, 1)
        price_unit_ship_prods_52258 = round(2.99 / 1.10, 2)
        ship_line_product_52258 = sales_3.order_line.filtered(
            lambda ln: ln.product_id == self.shipping_product_test
            and ln.price_unit == price_unit_ship_prods_52258)
        self.assertEquals(len(ship_line_product_52258), 1)
        self.assertEquals(
            ship_line_product_52258.product_id.name, 'Shipping costs')
        self.assertEquals(ship_line_product_52258.product_uom_qty, 1)
        amount_untaxed_lines = (
            price_unit_product_52469 * 2
            + price_unit_product_52470 * 2
            + price_unit_product_52258 * 1
            + price_unit_ship_prods_52469_52470 * 2
            + price_unit_ship_prods_52258 * 1)
        self.assertEquals(sales_3.amount_untaxed, amount_untaxed_lines)
        round_tax_diff = (
            amount_untaxed_lines * 0.10 - sales_3.amount_tax < 0.02)
        self.assertTrue(round_tax_diff)
        round_total_diff = (
            amount_untaxed_lines * 1.10 - sales_3.amount_total < 0.02)
        self.assertTrue(round_total_diff)
        self.assertEquals(sales_3.state, 'sale')
        self.assertEquals(len(sales_3.picking_ids), 2)
        self.assertEquals(sales_3.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_3.picking_ids[0].state, 'done')
        self.assertEquals(sales_3.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_3.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_3.invoice_ids), 1)
        self.assertEquals(sales_3.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_3.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_3.invoice_ids.payment_ids.journal_id, self.cash_journal_test)

    def test_import_order_with_serveral_lines_write_draft_ok(self):
        order = self.env['sale.order'].create({
            'origin': 'Beezup sale number: 407-3315028-8261943',
            'partner_id': self.partner_test1.id,
        })
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product1.id,
            'product_uom_qty': 1,
            'product_uom': self.ref('uom.product_uom_unit'),
        })
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product2.id,
            'product_uom_qty': 1,
            'product_uom': self.ref('uom.product_uom_unit'),
        })
        fname = self.get_file('order_with_serveral_lines_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(len(sales_1.order_line), 2)
        self.assertEquals(
            sales_1.order_line[0].product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line[0].product_uom_qty, 1)
        self.assertEquals(sales_1.order_line[0].price_unit, 10)
        self.assertEquals(sales_1.order_line[0].tax_id, self.tax_21)
        self.assertEquals(
            sales_1.order_line[1].product_id.name, 'Product test 2')
        self.assertEquals(sales_1.order_line[1].product_uom_qty, 1)
        self.assertEquals(sales_1.order_line[1].price_unit, 100)
        self.assertEquals(sales_1.order_line[1].tax_id, self.tax_21)
        self.assertEquals(sales_1.amount_untaxed, 10 + 100)
        self.assertEquals(sales_1.amount_tax, round(10 * 0.21 + 100 * 0.21, 2))
        self.assertEquals(
            sales_1.amount_total, round(10 * 1.21 + 100 * 1.21, 2))
        self.assertEquals(sales_1.state, 'draft')
        self.assertEquals(len(sales_1.picking_ids), 0)
        self.assertEquals(len(sales_1.invoice_ids), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_3 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 405-9692877-4031515'),
        ])
        self.assertEquals(len(sales_3), 0)
        partner_3 = self.env['res.partner'].search([
            ('name', '=', 'Juan Rute'),
        ])
        self.assertEquals(len(partner_3), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertEquals(sales_1.partner_id.email, 'ray@test.com')
        self.assertEquals(sales_1.partner_id.phone, '911000111')
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '45631')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_fr)
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.10, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_10)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.10, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.10, 2))
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id, self.cash_journal_test)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)
        partner_3 = self.env['res.partner'].search([
            ('name', '=', 'Juan Rute'),
        ])
        self.assertEquals(len(partner_3), 1)
        sales_3 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 405-9692877-4031515'),
        ])
        self.assertEquals(len(sales_3), 1)
        self.assertEquals(sales_3.partner_id.name, 'Juan Rute')
        self.assertEquals(sales_3.partner_id.email, 'juan@test.es')
        self.assertEquals(sales_3.partner_id.phone, '910123123')
        self.assertEquals(sales_3.partner_id.mobile, '666112233')
        self.assertEquals(sales_3.partner_id.vat, '')
        self.assertEquals(sales_3.partner_id.street, 'Calle Sol, 22')
        self.assertEquals(sales_3.partner_id.street2, 'Villa Sotea')
        self.assertEquals(sales_3.partner_id.city, 'Biarritz')
        self.assertEquals(sales_3.partner_id.zip, '64200')
        self.assertEquals(sales_3.partner_id.state_id.name, 'Biarritz')
        self.assertEquals(sales_3.partner_id.state_id.code, '00Biarritz')
        self.assertEquals(sales_3.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_3.partner_id.property_account_position_id,
            self.fiscal_position_fr)
        self.assertEquals(sales_3.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_3.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_3.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_3.order_line), 6)
        for line in sales_3.order_line:
            self.assertEquals(line.tax_id, self.tax_10)
        line_product_52469 = sales_3.order_line.filtered(
            lambda ln: ln.product_id.default_code == '52469')
        self.assertTrue(line_product_52469)
        self.assertEquals(line_product_52469.product_id.name, 'Product test 3')
        self.assertEquals(line_product_52469.product_uom_qty, 2)
        price_unit_product_52469 = round(37.54 / 1.10, 2)
        self.assertEquals(
            line_product_52469.price_unit, price_unit_product_52469)
        line_product_52470 = sales_3.order_line.filtered(
            lambda ln: ln.product_id.default_code == '52470')
        self.assertTrue(line_product_52470)
        self.assertEquals(line_product_52470.product_id.name, 'Product test 4')
        self.assertEquals(line_product_52470.product_uom_qty, 2)
        price_unit_product_52470 = round(43.33 / 1.10, 2)
        self.assertEquals(
            line_product_52470.price_unit, price_unit_product_52470)
        line_product_52258 = sales_3.order_line.filtered(
            lambda ln: ln.product_id.default_code == '52258')
        self.assertTrue(line_product_52258)
        self.assertEquals(line_product_52258.product_id.name, 'Product test 5')
        self.assertEquals(line_product_52258.product_uom_qty, 1)
        price_unit_product_52258 = round(36.93 / 1.10, 2)
        self.assertEquals(
            line_product_52258.price_unit, price_unit_product_52258)
        price_unit_ship_prods_52469_52470 = round(5.98 / 1.10, 2)
        ship_line_prods_52469_52470 = sales_3.order_line.filtered(
            lambda ln: ln.product_id == self.shipping_product_test
            and ln.price_unit == price_unit_ship_prods_52469_52470)
        self.assertEquals(len(ship_line_prods_52469_52470), 2)
        for ship_line in ship_line_prods_52469_52470:
            self.assertEquals(
                ship_line.product_id.name, 'Shipping costs')
            self.assertEquals(ship_line.product_uom_qty, 1)
        price_unit_ship_prods_52258 = round(2.99 / 1.10, 2)
        ship_line_product_52258 = sales_3.order_line.filtered(
            lambda ln: ln.product_id == self.shipping_product_test
            and ln.price_unit == price_unit_ship_prods_52258)
        self.assertEquals(len(ship_line_product_52258), 1)
        self.assertEquals(
            ship_line_product_52258.product_id.name, 'Shipping costs')
        self.assertEquals(ship_line_product_52258.product_uom_qty, 1)
        amount_untaxed_lines = (
            price_unit_product_52469 * 2
            + price_unit_product_52470 * 2
            + price_unit_product_52258 * 1
            + price_unit_ship_prods_52469_52470 * 2
            + price_unit_ship_prods_52258 * 1)
        self.assertEquals(sales_3.amount_untaxed, amount_untaxed_lines)
        round_tax_diff = (
            amount_untaxed_lines * 0.10 - sales_3.amount_tax < 0.02)
        self.assertTrue(round_tax_diff)
        round_total_diff = (
            amount_untaxed_lines * 1.10 - sales_3.amount_total < 0.02)
        self.assertTrue(round_total_diff)
        self.assertEquals(sales_3.state, 'sale')
        self.assertEquals(len(sales_3.picking_ids), 2)
        self.assertEquals(sales_3.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_3.picking_ids[0].state, 'done')
        self.assertEquals(sales_3.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_3.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_3.invoice_ids), 1)
        self.assertEquals(sales_3.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_3.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_3.invoice_ids.payment_ids.journal_id, self.cash_journal_test)

    def test_import_order_with_serveral_lines_write_confirm_error(self):
        order = self.env['sale.order'].create({
            'origin': 'Beezup sale number: 407-3315028-8261943',
            'partner_id': self.partner_test1.id,
        })
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product1.id,
            'product_uom_qty': 1,
            'product_uom': self.ref('uom.product_uom_unit'),
        })
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product2.id,
            'product_uom_qty': 1,
            'product_uom': self.ref('uom.product_uom_unit'),
        })
        order.action_confirm()
        self.assertNotEquals(order.state, 'draft')
        fname = self.get_file('order_with_serveral_lines_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(len(sales_1.order_line), 2)
        self.assertEquals(
            sales_1.order_line[0].product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line[0].product_uom_qty, 1)
        self.assertEquals(sales_1.order_line[0].price_unit, 10)
        self.assertEquals(sales_1.order_line[0].tax_id, self.tax_21)
        self.assertEquals(
            sales_1.order_line[1].product_id.name, 'Product test 2')
        self.assertEquals(sales_1.order_line[1].product_uom_qty, 1)
        self.assertEquals(sales_1.order_line[1].price_unit, 100)
        self.assertEquals(sales_1.order_line[1].tax_id, self.tax_21)
        self.assertEquals(sales_1.amount_untaxed, 10 + 100)
        self.assertEquals(sales_1.amount_tax, round(10 * 0.21 + 100 * 0.21, 2))
        self.assertEquals(
            sales_1.amount_total, round(10 * 1.21 + 100 * 1.21, 2))
        self.assertNotEquals(sales_1.state, 'draft')
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_3 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 405-9692877-4031515'),
        ])
        self.assertEquals(len(sales_3), 0)
        partner_3 = self.env['res.partner'].search([
            ('name', '=', 'Juan Rute'),
        ])
        self.assertEquals(len(partner_3), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: The order with origin \'Beezup sale number: '
            '407-3315028-8261943\' cannot be modified because it is not in a '
            'draft state.'), wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Partner test 1')
        self.assertEquals(len(sales_1.order_line), 2)
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_es)

        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)
        partner_3 = self.env['res.partner'].search([
            ('name', '=', 'Juan Rute'),
        ])
        self.assertEquals(len(partner_3), 1)
        sales_3 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 405-9692877-4031515'),
        ])
        self.assertEquals(len(sales_3), 1)
        self.assertEquals(sales_3.partner_id.name, 'Juan Rute')
        self.assertEquals(sales_3.partner_id.email, 'juan@test.es')
        self.assertEquals(sales_3.partner_id.phone, '910123123')
        self.assertEquals(sales_3.partner_id.mobile, '666112233')
        self.assertEquals(sales_3.partner_id.vat, '')
        self.assertEquals(sales_3.partner_id.street, 'Calle Sol, 22')
        self.assertEquals(sales_3.partner_id.street2, 'Villa Sotea')
        self.assertEquals(sales_3.partner_id.city, 'Biarritz')
        self.assertEquals(sales_3.partner_id.zip, '64200')
        self.assertEquals(sales_3.partner_id.state_id.name, 'Biarritz')
        self.assertEquals(sales_3.partner_id.state_id.code, '00Biarritz')
        self.assertEquals(sales_3.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_3.partner_id.property_account_position_id,
            self.fiscal_position_fr)
        self.assertEquals(sales_3.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_3.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_3.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_3.order_line), 6)
        for line in sales_3.order_line:
            self.assertEquals(line.tax_id, self.tax_10)
        line_product_52469 = sales_3.order_line.filtered(
            lambda ln: ln.product_id.default_code == '52469')
        self.assertTrue(line_product_52469)
        self.assertEquals(line_product_52469.product_id.name, 'Product test 3')
        self.assertEquals(line_product_52469.product_uom_qty, 2)
        price_unit_product_52469 = round(37.54 / 1.10, 2)
        self.assertEquals(
            line_product_52469.price_unit, price_unit_product_52469)
        line_product_52470 = sales_3.order_line.filtered(
            lambda ln: ln.product_id.default_code == '52470')
        self.assertTrue(line_product_52470)
        self.assertEquals(line_product_52470.product_id.name, 'Product test 4')
        self.assertEquals(line_product_52470.product_uom_qty, 2)
        price_unit_product_52470 = round(43.33 / 1.10, 2)
        self.assertEquals(
            line_product_52470.price_unit, price_unit_product_52470)
        line_product_52258 = sales_3.order_line.filtered(
            lambda ln: ln.product_id.default_code == '52258')
        self.assertTrue(line_product_52258)
        self.assertEquals(line_product_52258.product_id.name, 'Product test 5')
        self.assertEquals(line_product_52258.product_uom_qty, 1)
        price_unit_product_52258 = round(36.93 / 1.10, 2)
        self.assertEquals(
            line_product_52258.price_unit, price_unit_product_52258)
        price_unit_ship_prods_52469_52470 = round(5.98 / 1.10, 2)
        ship_line_prods_52469_52470 = sales_3.order_line.filtered(
            lambda ln: ln.product_id == self.shipping_product_test
            and ln.price_unit == price_unit_ship_prods_52469_52470)
        self.assertEquals(len(ship_line_prods_52469_52470), 2)
        for ship_line in ship_line_prods_52469_52470:
            self.assertEquals(
                ship_line.product_id.name, 'Shipping costs')
            self.assertEquals(ship_line.product_uom_qty, 1)
        price_unit_ship_prods_52258 = round(2.99 / 1.10, 2)
        ship_line_product_52258 = sales_3.order_line.filtered(
            lambda ln: ln.product_id == self.shipping_product_test
            and ln.price_unit == price_unit_ship_prods_52258)
        self.assertEquals(len(ship_line_product_52258), 1)
        self.assertEquals(
            ship_line_product_52258.product_id.name, 'Shipping costs')
        self.assertEquals(ship_line_product_52258.product_uom_qty, 1)
        amount_untaxed_lines = (
            price_unit_product_52469 * 2
            + price_unit_product_52470 * 2
            + price_unit_product_52258 * 1
            + price_unit_ship_prods_52469_52470 * 2
            + price_unit_ship_prods_52258 * 1)
        self.assertEquals(sales_3.amount_untaxed, amount_untaxed_lines)
        round_tax_diff = (
            amount_untaxed_lines * 0.10 - sales_3.amount_tax < 0.02)
        self.assertTrue(round_tax_diff)
        round_total_diff = (
            amount_untaxed_lines * 1.10 - sales_3.amount_total < 0.02)
        self.assertTrue(round_total_diff)
        self.assertEquals(sales_3.state, 'sale')
        self.assertEquals(len(sales_3.picking_ids), 2)
        self.assertEquals(sales_3.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_3.picking_ids[0].state, 'done')
        self.assertEquals(sales_3.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_3.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_3.invoice_ids), 1)
        self.assertEquals(sales_3.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_3.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_3.invoice_ids.payment_ids.journal_id, self.cash_journal_test)

    def test_import_order_with_serveral_lines_duply_product_error(self):
        order1 = self.env['sale.order'].create({
            'origin': 'Beezup sale number: 407-3315028-8261943',
            'partner_id': self.partner_test1.id,
        })
        self.env['sale.order.line'].create({
            'order_id': order1.id,
            'product_id': self.product1.id,
            'product_uom_qty': 1,
            'product_uom': self.ref('uom.product_uom_unit'),
        })
        self.env['sale.order.line'].create({
            'order_id': order1.id,
            'product_id': self.product2.id,
            'product_uom_qty': 1,
            'product_uom': self.ref('uom.product_uom_unit'),
        })
        order2 = self.env['sale.order'].create({
            'origin': 'Beezup sale number: 407-3315028-8261943',
            'partner_id': self.partner_test1.id,
        })
        self.env['sale.order.line'].create({
            'order_id': order2.id,
            'product_id': self.product1.id,
            'product_uom_qty': 10,
            'product_uom': self.ref('uom.product_uom_unit'),
        })
        fname = self.get_file('order_with_serveral_lines_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 2)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: More than one sale order with origin \'Beezup sale number: '
            '407-3315028-8261943\' has been found. The order details could '
            'not be imported.'), wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 2)
        sale1_1 = sales_1.filtered(lambda so: len(so.order_line) == 2)
        self.assertEquals(sale1_1.partner_id.name, 'Partner test 1')
        self.assertEquals(
            sale1_1.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sale1_1.state, 'draft')
        self.assertEquals(len(sale1_1.order_line), 2)
        for line in sale1_1.order_line:
            self.assertEquals(line.tax_id, self.tax_21)
        line_product1 = sale1_1.order_line.filtered(
            lambda ln: ln.product_id == self.product1)
        self.assertEquals(len(line_product1), 1)
        self.assertEquals(line_product1.product_uom_qty, 1)
        self.assertEquals(line_product1.price_unit, 10)
        line_product2 = sale1_1.order_line.filtered(
            lambda ln: ln.product_id == self.product2)
        self.assertEquals(len(line_product2), 1)
        self.assertEquals(line_product2.product_uom_qty, 1)
        self.assertEquals(line_product2.price_unit, 100)
        sale1_2 = sales_1.filtered(lambda so: len(so.order_line) == 1)
        self.assertEquals(sale1_2.partner_id.name, 'Partner test 1')
        self.assertEquals(sale1_2.state, 'draft')
        self.assertEquals(len(sale1_2.order_line), 1)
        self.assertEquals(sale1_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sale1_2.order_line.product_uom_qty, 10)
        self.assertEquals(sale1_2.order_line.price_unit, 10)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)
        partner_3 = self.env['res.partner'].search([
            ('name', '=', 'Juan Rute'),
        ])
        self.assertEquals(len(partner_3), 1)
        sales_3 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 405-9692877-4031515'),
        ])
        self.assertEquals(len(sales_3), 1)
        self.assertEquals(sales_3.partner_id.name, 'Juan Rute')
        self.assertEquals(sales_3.partner_id.email, 'juan@test.es')
        self.assertEquals(sales_3.partner_id.phone, '910123123')
        self.assertEquals(sales_3.partner_id.mobile, '666112233')
        self.assertEquals(sales_3.partner_id.vat, '')
        self.assertEquals(sales_3.partner_id.street, 'Calle Sol, 22')
        self.assertEquals(sales_3.partner_id.street2, 'Villa Sotea')
        self.assertEquals(sales_3.partner_id.city, 'Biarritz')
        self.assertEquals(sales_3.partner_id.zip, '64200')
        self.assertEquals(sales_3.partner_id.state_id.name, 'Biarritz')
        self.assertEquals(sales_3.partner_id.state_id.code, '00Biarritz')
        self.assertEquals(sales_3.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_3.partner_id.property_account_position_id,
            self.fiscal_position_fr)
        self.assertEquals(sales_3.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_3.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_3.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_3.order_line), 6)
        for line in sales_3.order_line:
            self.assertEquals(line.tax_id, self.tax_10)
        line_product_52469 = sales_3.order_line.filtered(
            lambda ln: ln.product_id.default_code == '52469')
        self.assertTrue(line_product_52469)
        self.assertEquals(line_product_52469.product_id.name, 'Product test 3')
        self.assertEquals(line_product_52469.product_uom_qty, 2)
        price_unit_product_52469 = round(37.54 / 1.10, 2)
        self.assertEquals(
            line_product_52469.price_unit, price_unit_product_52469)
        line_product_52470 = sales_3.order_line.filtered(
            lambda ln: ln.product_id.default_code == '52470')
        self.assertTrue(line_product_52470)
        self.assertEquals(line_product_52470.product_id.name, 'Product test 4')
        self.assertEquals(line_product_52470.product_uom_qty, 2)
        price_unit_product_52470 = round(43.33 / 1.10, 2)
        self.assertEquals(
            line_product_52470.price_unit, price_unit_product_52470)
        line_product_52258 = sales_3.order_line.filtered(
            lambda ln: ln.product_id.default_code == '52258')
        self.assertTrue(line_product_52258)
        self.assertEquals(line_product_52258.product_id.name, 'Product test 5')
        self.assertEquals(line_product_52258.product_uom_qty, 1)
        price_unit_product_52258 = round(36.93 / 1.10, 2)
        self.assertEquals(
            line_product_52258.price_unit, price_unit_product_52258)
        price_unit_ship_prods_52469_52470 = round(5.98 / 1.10, 2)
        ship_line_prods_52469_52470 = sales_3.order_line.filtered(
            lambda ln: ln.product_id == self.shipping_product_test
            and ln.price_unit == price_unit_ship_prods_52469_52470)
        self.assertEquals(len(ship_line_prods_52469_52470), 2)
        for ship_line in ship_line_prods_52469_52470:
            self.assertEquals(
                ship_line.product_id.name, 'Shipping costs')
            self.assertEquals(ship_line.product_uom_qty, 1)
        price_unit_ship_prods_52258 = round(2.99 / 1.10, 2)
        ship_line_product_52258 = sales_3.order_line.filtered(
            lambda ln: ln.product_id == self.shipping_product_test
            and ln.price_unit == price_unit_ship_prods_52258)
        self.assertEquals(len(ship_line_product_52258), 1)
        self.assertEquals(
            ship_line_product_52258.product_id.name, 'Shipping costs')
        self.assertEquals(ship_line_product_52258.product_uom_qty, 1)
        amount_untaxed_lines = (
            price_unit_product_52469 * 2
            + price_unit_product_52470 * 2
            + price_unit_product_52258 * 1
            + price_unit_ship_prods_52469_52470 * 2
            + price_unit_ship_prods_52258 * 1)
        self.assertEquals(sales_3.amount_untaxed, amount_untaxed_lines)
        round_tax_diff = (
            amount_untaxed_lines * 0.10 - sales_3.amount_tax < 0.02)
        self.assertTrue(round_tax_diff)
        round_total_diff = (
            amount_untaxed_lines * 1.10 - sales_3.amount_total < 0.02)
        self.assertTrue(round_total_diff)
        self.assertEquals(sales_3.state, 'sale')
        self.assertEquals(len(sales_3.picking_ids), 2)
        self.assertEquals(sales_3.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_3.picking_ids[0].state, 'done')
        self.assertEquals(sales_3.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_3.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_3.invoice_ids), 1)
        self.assertEquals(sales_3.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_3.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_3.invoice_ids.payment_ids.journal_id, self.cash_journal_test)

    def test_new_fields_ok(self):
        fname = self.get_file('sample_new_fields_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertEquals(sales_1.partner_id.email, 'ray@test.com')
        self.assertEquals(sales_1.partner_id.phone, '911000111')
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '45631')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_fr)
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.10, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_10)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.10, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.10, 2))
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id, self.cash_journal_test)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_new_fields_error(self):
        fname = self.get_file('sample_new_fields_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
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
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
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
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)

    def test_import_new_state_id_without_country_create_ok(self):
        fname = self.get_file(
            'sample_new_state_id_without_country_create_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' will be '
            'assigned.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: No fiscal position found for country code \'00\''),
            wizard.line_ids[1].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        fposition_nocountry = self.create_fiscal_position_no_country()
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' will be '
            'assigned.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' is assigned.'),
            wizard.line_ids[1].name)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' will be '
            'assigned.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' is assigned.'),
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertEquals(sales_1.partner_id.email, 'ray@test.com')
        self.assertEquals(sales_1.partner_id.phone, '911000111')
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '45631')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Test state')
        self.assertEquals(sales_1.partner_id.country_id.code, '00')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            fposition_nocountry)
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.07, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_7)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.07, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.07, 2))
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id, self.cash_journal_test)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_new_state_id_without_country_write_ok(self):
        self.env['sale.order'].create({
            'origin': 'Beezup sale number: 407-3315028-8261943',
            'partner_id': self.partner_test1.id,
        })
        fname = self.get_file(
            'sample_new_state_id_without_country_create_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' will be '
            'assigned.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: No fiscal position found for country code \'00\''),
            wizard.line_ids[1].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        fposition_nocountry = self.create_fiscal_position_no_country()
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' will be '
            'assigned.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' is assigned.'),
            wizard.line_ids[1].name)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' will be '
            'assigned.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' is assigned.'),
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertEquals(sales_1.partner_id.email, 'ray@test.com')
        self.assertEquals(sales_1.partner_id.phone, '911000111')
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '45631')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Test state')
        self.assertEquals(sales_1.partner_id.country_id.code, '00')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            fposition_nocountry)
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.07, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_7)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.07, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.07, 2))
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id, self.cash_journal_test)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_state_id_without_country_create_ok(self):
        fname = self.get_file('sample_state_id_without_country.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' will be '
            'assigned.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: No fiscal position found for country code \'00\''),
            wizard.line_ids[1].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        fposition_nocountry = self.create_fiscal_position_no_country()
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' will be '
            'assigned.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' is assigned.'),
            wizard.line_ids[1].name)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' will be '
            'assigned.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' is assigned.'),
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertEquals(sales_1.partner_id.email, 'ray@test.com')
        self.assertEquals(sales_1.partner_id.phone, '911000111')
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '45631')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, '00')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            fposition_nocountry)
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.07, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_7)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.07, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.07, 2))
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id, self.cash_journal_test)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_state_id_without_country_write_ok(self):
        self.env['sale.order'].create({
            'origin': 'Beezup sale number: 407-3315028-8261943',
            'partner_id': self.partner_test1.id,
        })
        fname = self.get_file('sample_state_id_without_country.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' will be '
            'assigned.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: No fiscal position found for country code \'00\''),
            wizard.line_ids[1].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Partner test 1')
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        fposition_nocountry = self.create_fiscal_position_no_country()
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' will be '
            'assigned.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' is assigned.'),
            wizard.line_ids[1].name)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' will be '
            'assigned.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' is assigned.'),
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertEquals(sales_1.partner_id.email, 'ray@test.com')
        self.assertEquals(sales_1.partner_id.phone, '911000111')
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '45631')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, '00')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            fposition_nocountry)
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.07, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_7)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.07, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.07, 2))
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id, self.cash_journal_test)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_empty_state_id_empty_country_id_create_ok(self):
        fname = self.get_file(
            'sample_empty_state_id_empty_country_id.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' will be '
            'assigned.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: No fiscal position found for country code \'00\''),
            wizard.line_ids[1].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        fposition_nocountry = self.create_fiscal_position_no_country()
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 3)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' will be '
            'assigned.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' is assigned.'),
            wizard.line_ids[1].name)
        self.assertIn(_(
            '2: State name empty not found; not assigned.'),
            wizard.line_ids[2].name)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 3)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' will be '
            'assigned.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' is assigned.'),
            wizard.line_ids[1].name)
        self.assertIn(_(
            '2: State name empty not found; not assigned.'),
            wizard.line_ids[2].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertEquals(sales_1.partner_id.email, 'ray@test.com')
        self.assertEquals(sales_1.partner_id.phone, '911000111')
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '45631')
        self.assertFalse(sales_1.partner_id.state_id)
        self.assertEquals(sales_1.partner_id.country_id.code, '00')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            fposition_nocountry)
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.07, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_7)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.07, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.07, 2))
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id, self.cash_journal_test)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_empty_state_id_empty_country_id_write_ok(self):
        self.env['sale.order'].create({
            'origin': 'Beezup sale number: 407-3315028-8261943',
            'partner_id': self.partner_test1.id,
        })
        fname = self.get_file(
            'sample_empty_state_id_empty_country_id.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' will be '
            'assigned.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: No fiscal position found for country code \'00\''),
            wizard.line_ids[1].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Partner test 1')
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        fposition_nocountry = self.create_fiscal_position_no_country()
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 3)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' will be '
            'assigned.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' is assigned.'),
            wizard.line_ids[1].name)
        self.assertIn(_(
            '2: State name empty not found; not assigned.'),
            wizard.line_ids[2].name)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 3)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' will be '
            'assigned.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Country code empty not found; \'No country\' is assigned.'),
            wizard.line_ids[1].name)
        self.assertIn(_(
            '2: State name empty not found; not assigned.'),
            wizard.line_ids[2].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertEquals(sales_1.partner_id.email, 'ray@test.com')
        self.assertEquals(sales_1.partner_id.phone, '911000111')
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '45631')
        self.assertFalse(sales_1.partner_id.state_id)
        self.assertEquals(sales_1.partner_id.country_id.code, '00')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            fposition_nocountry)
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.07, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_7)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.07, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.07, 2))
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id, self.cash_journal_test)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_empty_no_required_fields_create_ok(self):
        fname = self.get_file('sample_empty_no_required_fields.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 4)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Email data not found; not assigned'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Street data not found; not assigned'), wizard.line_ids[1].name)
        self.assertIn(_(
            '2: City data not found; not assigned'), wizard.line_ids[2].name)
        self.assertIn(_(
            '2: Zip data not found; not assigned'), wizard.line_ids[3].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 4)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Email data not found; not assigned'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Street data not found; not assigned'), wizard.line_ids[1].name)
        self.assertIn(_(
            '2: City data not found; not assigned'), wizard.line_ids[2].name)
        self.assertIn(_(
            '2: Zip data not found; not assigned'), wizard.line_ids[3].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertFalse(sales_1.partner_id.email)
        self.assertFalse(sales_1.partner_id.phone)
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertFalse(sales_1.partner_id.street)
        self.assertFalse(sales_1.partner_id.street2)
        self.assertFalse(sales_1.partner_id.city)
        self.assertFalse(sales_1.partner_id.zip)
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_fr)
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.10, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_10)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.10, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.10, 2))
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id, self.cash_journal_test)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_empty_no_required_fields_street_write_ok(self):
        self.env['sale.order'].create({
            'origin': 'Beezup sale number: 407-3315028-8261943',
            'partner_id': self.partner_test1.id,
        })
        fname = self.get_file('sample_empty_no_required_fields.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 4)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Email data not found; not assigned'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Street data not found; not assigned'), wizard.line_ids[1].name)
        self.assertIn(_(
            '2: City data not found; not assigned'), wizard.line_ids[2].name)
        self.assertIn(_(
            '2: Zip data not found; not assigned'), wizard.line_ids[3].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Partner test 1')
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 4)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Email data not found; not assigned'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Street data not found; not assigned'), wizard.line_ids[1].name)
        self.assertIn(_(
            '2: City data not found; not assigned'), wizard.line_ids[2].name)
        self.assertIn(_(
            '2: Zip data not found; not assigned'), wizard.line_ids[3].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertFalse(sales_1.partner_id.email)
        self.assertFalse(sales_1.partner_id.phone)
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertFalse(sales_1.partner_id.street)
        self.assertFalse(sales_1.partner_id.street2)
        self.assertFalse(sales_1.partner_id.city)
        self.assertFalse(sales_1.partner_id.zip)
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_fr)
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.10, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_10)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.10, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.10, 2))
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id, self.cash_journal_test)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_line_canceled(self):
        fname = self.get_file('sample_line_canceled.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Column \'Order_Status_MarketPlaceStatus\' with value '
            'canceled; the order line will not be imported.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '3: Column \'Order_Status_MarketPlaceStatus\' with value '
            'canceled; the order line will not be imported.'),
            wizard.line_ids[1].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Column \'Order_Status_MarketPlaceStatus\' with value '
            'canceled; the order line will not be imported.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '3: Column \'Order_Status_MarketPlaceStatus\' with value '
            'canceled; the order line will not be imported.'),
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)

    def test_import_line_canceled_several_lines(self):
        fname = self.get_file('sample_line_canceled_several_lines.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Column \'Order_Status_MarketPlaceStatus\' with value '
            'canceled; the order line will not be imported.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '5: Column \'Order_Status_MarketPlaceStatus\' with value '
            'canceled; the order line will not be imported.'),
            wizard.line_ids[1].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Column \'Order_Status_MarketPlaceStatus\' with value '
            'canceled; the order line will not be imported.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '5: Column \'Order_Status_MarketPlaceStatus\' with value '
            'canceled; the order line will not be imported.'),
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Juan Rute'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 405-9692877-4031515'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Juan Rute')
        self.assertEquals(sales_1.partner_id.email, 'juan@test.es')
        self.assertEquals(sales_1.partner_id.phone, '910123123')
        self.assertEquals(sales_1.partner_id.mobile, '666112233')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, 'Calle Sol, 22')
        self.assertEquals(sales_1.partner_id.street2, 'Villa Sotea')
        self.assertEquals(sales_1.partner_id.city, 'Biarritz')
        self.assertEquals(sales_1.partner_id.zip, '64200')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Biarritz')
        self.assertEquals(sales_1.partner_id.state_id.code, '00Biarritz')
        self.assertEquals(sales_1.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_fr)
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 4)
        for line in sales_1.order_line:
            self.assertEquals(line.tax_id, self.tax_10)
        line_product_52470 = sales_1.order_line.filtered(
            lambda ln: ln.product_id.default_code == '52470')
        self.assertTrue(line_product_52470)
        self.assertEquals(line_product_52470.product_id.name, 'Product test 4')
        self.assertEquals(line_product_52470.product_uom_qty, 2)
        price_unit_product_52470 = round(43.33 / 1.10, 2)
        self.assertEquals(
            line_product_52470.price_unit, price_unit_product_52470)
        line_product_52258 = sales_1.order_line.filtered(
            lambda ln: ln.product_id.default_code == '52258')
        self.assertTrue(line_product_52258)
        self.assertEquals(line_product_52258.product_id.name, 'Product test 5')
        self.assertEquals(line_product_52258.product_uom_qty, 1)
        price_unit_product_52258 = round(36.93 / 1.10, 2)
        self.assertEquals(
            line_product_52258.price_unit, price_unit_product_52258)
        price_unit_ship_prods_52470 = round(5.98 / 1.10, 2)
        ship_line_prods_52470 = sales_1.order_line.filtered(
            lambda ln: ln.product_id == self.shipping_product_test
            and ln.price_unit == price_unit_ship_prods_52470)
        self.assertEquals(len(ship_line_prods_52470), 1)
        self.assertEquals(len(ship_line_prods_52470), 1)
        self.assertEquals(
            ship_line_prods_52470.product_id.name, 'Shipping costs')
        self.assertEquals(ship_line_prods_52470.product_uom_qty, 1)
        price_unit_ship_prods_52258 = round(2.99 / 1.10, 2)
        ship_line_product_52258 = sales_1.order_line.filtered(
            lambda ln: ln.product_id == self.shipping_product_test
            and ln.price_unit == price_unit_ship_prods_52258)
        self.assertEquals(len(ship_line_product_52258), 1)
        self.assertEquals(
            ship_line_product_52258.product_id.name, 'Shipping costs')
        self.assertEquals(ship_line_product_52258.product_uom_qty, 1)
        amount_untaxed_lines = (
            price_unit_product_52470 * 2
            + price_unit_product_52258 * 1
            + price_unit_ship_prods_52470 * 1
            + price_unit_ship_prods_52258 * 1)
        self.assertEquals(
            sales_1.amount_untaxed, round(amount_untaxed_lines, 2))
        round_tax_diff = (
            amount_untaxed_lines * 0.10 - sales_1.amount_tax < 0.02)
        self.assertTrue(round_tax_diff)
        round_total_diff = (
            amount_untaxed_lines * 1.10 - sales_1.amount_total < 0.02)
        self.assertTrue(round_total_diff)
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id, self.cash_journal_test)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Amparo García'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 405-9692877-4031516'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Amparo García')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'juan@test.es')
        self.assertEquals(sales_2.partner_id.phone, '910123123')
        self.assertEquals(sales_2.partner_id.mobile, '666112233')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Sol, 22')
        self.assertEquals(sales_2.partner_id.street2, 'Villa Sotea')
        self.assertEquals(sales_2.partner_id.city, 'Biarritz')
        self.assertEquals(sales_2.partner_id.zip, '64200')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Biarritz')
        self.assertEquals(sales_2.partner_id.state_id.code, '00Biarritz')
        self.assertEquals(sales_2.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_fr)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 4)
        for line in sales_2.order_line:
            self.assertEquals(line.tax_id, self.tax_10)
        line_product_52470 = sales_2.order_line.filtered(
            lambda ln: ln.product_id.default_code == '52470')
        self.assertTrue(line_product_52470)
        self.assertEquals(line_product_52470.product_id.name, 'Product test 4')
        self.assertEquals(line_product_52470.product_uom_qty, 2)
        price_unit_product_52470 = round(43.33 / 1.10, 2)
        self.assertEquals(
            line_product_52470.price_unit, price_unit_product_52470)
        line_product_52258 = sales_2.order_line.filtered(
            lambda ln: ln.product_id.default_code == '52258')
        self.assertTrue(line_product_52258)
        self.assertEquals(line_product_52258.product_id.name, 'Product test 5')
        self.assertEquals(line_product_52258.product_uom_qty, 1)
        price_unit_product_52258 = round(36.93 / 1.10, 2)
        self.assertEquals(
            line_product_52258.price_unit, price_unit_product_52258)
        price_unit_ship_prods_52470 = round(5.98 / 1.10, 2)
        ship_line_prods_52470 = sales_2.order_line.filtered(
            lambda ln: ln.product_id == self.shipping_product_test
            and ln.price_unit == price_unit_ship_prods_52470)
        self.assertEquals(len(ship_line_prods_52470), 1)
        self.assertEquals(len(ship_line_prods_52470), 1)
        self.assertEquals(
            ship_line_prods_52470.product_id.name, 'Shipping costs')
        self.assertEquals(ship_line_prods_52470.product_uom_qty, 1)
        price_unit_ship_prods_52258 = round(2.99 / 1.10, 2)
        ship_line_product_52258 = sales_2.order_line.filtered(
            lambda ln: ln.product_id == self.shipping_product_test
            and ln.price_unit == price_unit_ship_prods_52258)
        self.assertEquals(len(ship_line_product_52258), 1)
        self.assertEquals(
            ship_line_product_52258.product_id.name, 'Shipping costs')
        self.assertEquals(ship_line_product_52258.product_uom_qty, 1)
        amount_untaxed_lines = (
            price_unit_product_52470 * 2
            + price_unit_product_52258 * 1
            + price_unit_ship_prods_52470 * 1
            + price_unit_ship_prods_52258 * 1)
        self.assertEquals(
            sales_2.amount_untaxed, round(amount_untaxed_lines, 2))
        self.assertTrue(round_total_diff)
        self.assertEquals(sales_2.state, 'draft')

    def test_import_create_default_code_sufix(self):
        fname = self.get_file('sample_default_code_sufix.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertEquals(sales_1.partner_id.email, 'ray@test.com')
        self.assertEquals(sales_1.partner_id.phone, '911000111')
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '45631')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_fr)
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.10, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_10)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.10, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.10, 2))
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id, self.cash_journal_test)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_import_write_default_code_sufix(self):
        self.env['sale.order'].create({
            'origin': 'Beezup sale number: 407-3315028-8261943',
            'partner_id': self.partner_test1.id,
        })
        fname = self.get_file('sample_default_code_sufix.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertEquals(sales_1.partner_id.email, 'ray@test.com')
        self.assertEquals(sales_1.partner_id.phone, '911000111')
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '45631')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_fr)
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.10, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_10)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.10, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.10, 2))
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id, self.cash_journal_test)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)

    def test_country_fiscal_position(self):
        fname = self.get_file('sample_country_fiscal_position.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '4: Country code empty not found; \'No country\' will be '
            'assigned.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '5: The country \'ZZ\' does not exist; \'No country\' is '
            'assigned.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '4: No fiscal position found for country code \'00\'.'),
            wizard.line_ids[2].name)
        self.assertIn(_(
            '5: No fiscal position found for country code \'00\'.'),
            wizard.line_ids[3].name)
        fposition_nocountry = self.create_fiscal_position_no_country()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 4)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '4: Country code empty not found; \'No country\' will be '
            'assigned.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '4: Country code empty not found; \'No country\' is assigned.'),
            wizard.line_ids[1].name)
        self.assertIn(_(
            '5: The country \'ZZ\' does not exist; \'No country\' is '
            'assigned.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '5: The country \'ZZ\' does not exist; \'No country\' is '
            'assigned.'), wizard.line_ids[3].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_3 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 405-9692877-4031515'),
        ])
        self.assertEquals(len(sales_3), 0)
        partner_3 = self.env['res.partner'].search([
            ('name', '=', 'Juan Rute'),
        ])
        self.assertEquals(len(partner_3), 0)
        sales_4 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 405-9692877-4031516'),
        ])
        self.assertEquals(len(sales_4), 0)
        partner_4 = self.env['res.partner'].search([
            ('name', '=', 'Amparo García'),
        ])
        self.assertEquals(len(partner_4), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 4)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '4: Country code empty not found; \'No country\' will be '
            'assigned.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '4: Country code empty not found; \'No country\' is assigned.'),
            wizard.line_ids[1].name)
        self.assertIn(_(
            '5: The country \'ZZ\' does not exist; \'No country\' is '
            'assigned.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '5: The country \'ZZ\' does not exist; \'No country\' is '
            'assigned.'), wizard.line_ids[3].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertEquals(sales_1.partner_id.email, 'ray@test.com')
        self.assertEquals(sales_1.partner_id.phone, '911000111')
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '45631')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_fr)
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.10, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_10)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.10, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.10, 2))
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id, self.cash_journal_test)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)
        partner_3 = self.env['res.partner'].search([
            ('name', '=', 'Juan Rute'),
        ])
        self.assertEquals(len(partner_3), 1)
        sales_3 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 405-9692877-4031515'),
        ])
        self.assertEquals(len(sales_3), 1)
        self.assertEquals(sales_3.partner_id.name, 'Juan Rute')
        self.assertEquals(sales_3.partner_id.email, 'juan@test.es')
        self.assertEquals(sales_3.partner_id.phone, '910123123')
        self.assertEquals(sales_3.partner_id.mobile, '666112233')
        self.assertEquals(sales_3.partner_id.vat, '')
        self.assertEquals(sales_3.partner_id.street, 'Calle Sol, 22')
        self.assertEquals(sales_3.partner_id.street2, 'Villa Sotea')
        self.assertEquals(sales_3.partner_id.city, 'Biarritz')
        self.assertEquals(sales_3.partner_id.zip, '64200')
        self.assertEquals(sales_3.partner_id.state_id.name, 'Biarritz')
        self.assertEquals(sales_3.partner_id.state_id.code, '00Biarritz')
        self.assertEquals(sales_3.partner_id.country_id.code, '00')
        self.assertEquals(
            sales_3.partner_id.property_account_position_id,
            fposition_nocountry)
        self.assertEquals(sales_3.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_3.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_3.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_3.order_line), 1)
        self.assertEquals(sales_3.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_3.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.07, 2)
        self.assertEquals(sales_3.order_line.price_unit, price_unit)
        self.assertEquals(sales_3.order_line.tax_id, self.tax_7)
        self.assertEquals(sales_3.amount_untaxed, price_unit)
        self.assertEquals(sales_3.amount_tax, round(price_unit * 0.07, 2))
        self.assertEquals(sales_3.amount_total, round(price_unit * 1.07, 2))
        self.assertEquals(sales_3.state, 'draft')
        self.assertEquals(len(sales_3.picking_ids), 0)
        self.assertEquals(len(sales_3.invoice_ids), 0)
        partner_4 = self.env['res.partner'].search([
            ('name', '=', 'Amparo García'),
        ])
        self.assertEquals(len(partner_4), 1)
        sales_4 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 405-9692877-4031516'),
        ])
        self.assertEquals(len(sales_4), 1)
        self.assertEquals(sales_4.partner_id.name, u'Amparo García')
        self.assertEquals(sales_4.partner_id.email, 'juan@test.es')
        self.assertEquals(sales_4.partner_id.phone, '910123123')
        self.assertEquals(sales_4.partner_id.mobile, '666112233')
        self.assertEquals(sales_4.partner_id.vat, '')
        self.assertEquals(sales_4.partner_id.street, 'Calle Sol, 22')
        self.assertEquals(sales_4.partner_id.street2, 'Villa Sotea')
        self.assertEquals(sales_4.partner_id.city, 'Biarritz')
        self.assertEquals(sales_4.partner_id.zip, '64200')
        self.assertEquals(sales_4.partner_id.state_id.name, 'Biarritz')
        self.assertEquals(sales_4.partner_id.state_id.code, '00Biarritz')
        self.assertEquals(sales_4.partner_id.country_id.code, '00')
        self.assertEquals(
            sales_4.partner_id.property_account_position_id,
            fposition_nocountry)
        self.assertEquals(sales_4.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_4.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_4.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(sales_4.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_4.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.07, 2)
        self.assertEquals(sales_4.order_line.price_unit, price_unit)
        self.assertEquals(sales_4.order_line.tax_id, self.tax_7)
        self.assertEquals(sales_4.amount_untaxed, price_unit)
        self.assertEquals(sales_4.amount_tax, round(price_unit * 0.07, 2))
        self.assertEquals(sales_4.amount_total, round(price_unit * 1.07, 2))
        self.assertEquals(sales_4.state, 'draft')
        self.assertEquals(len(sales_4.picking_ids), 0)
        self.assertEquals(len(sales_4.invoice_ids), 0)

    def test_import_phone_mobile(self):
        fname = self.get_file('sample_phone_mobile.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '4: Phone and mobile data not found; not assigned.'),
            wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '4: Phone and mobile data not found; not assigned.'),
            wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertEquals(sales_1.partner_id.email, 'ray@test.com')
        self.assertEquals(sales_1.partner_id.phone, '911000111')
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '45631')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_fr)
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.10, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_10)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.10, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.10, 2))
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id, self.cash_journal_test)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertFalse(sales_2.partner_id.phone)
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.21, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_21)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.21, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)
        sales_3 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 405-9692877-4031515'),
        ])
        self.assertEquals(len(sales_3), 1)
        self.assertEquals(sales_3.partner_id.name, 'Juan Rute')
        self.assertEquals(sales_3.partner_id.email, 'juan@test.es')
        self.assertFalse(sales_3.partner_id.phone)
        self.assertFalse(sales_3.partner_id.mobile)
        self.assertEquals(sales_3.partner_id.vat, '')
        self.assertEquals(sales_3.partner_id.street, 'Calle Sol, 22')
        self.assertEquals(sales_3.partner_id.street2, 'Villa Sotea')
        self.assertEquals(sales_3.partner_id.city, 'Biarritz')
        self.assertEquals(sales_3.partner_id.zip, '64200')
        self.assertEquals(sales_3.partner_id.state_id.name, 'Biarritz')
        self.assertEquals(sales_3.partner_id.state_id.code, '00Biarritz')
        self.assertEquals(sales_3.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_3.partner_id.property_account_position_id,
            self.fiscal_position_fr)
        self.assertEquals(sales_3.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_3.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_3.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_3.order_line), 1)
        self.assertEquals(sales_3.order_line.product_id.name, 'Product test 2')
        self.assertEquals(sales_3.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.10, 2)
        self.assertEquals(sales_3.order_line.price_unit, price_unit)
        self.assertEquals(sales_3.order_line.tax_id, self.tax_10)
        self.assertEquals(sales_3.amount_untaxed, price_unit)
        self.assertEquals(sales_3.amount_tax, round(price_unit * 0.10, 2))
        self.assertEquals(sales_3.amount_total, round(price_unit * 1.10, 2))
        self.assertEquals(len(sales_3.picking_ids), 2)
        self.assertEquals(sales_3.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_3.picking_ids[0].state, 'done')
        self.assertEquals(sales_3.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_3.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_3.invoice_ids), 1)
        self.assertEquals(sales_3.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_3.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_3.invoice_ids.payment_ids.journal_id, self.cash_journal_test)

    def test_import_create_product_invoice_policy_order_error(self):
        fname = self.get_file('sample_product_invoice_policy_order.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 1)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 1)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: The invoice policy of the products of order with origin '
            'Beezup sale number: 407-3315028-8261943 is [\'order\'] and is '
            'not contemplated. It must be \'delivery\', so the pickings and '
            'the invoice has not been created; check manually.'),
            wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertFalse(sales_1.partner_id.parent_id)
        self.assertEquals(sales_1.partner_invoice_id, sales_1.partner_id)
        self.assertEquals(sales_1.partner_shipping_id, sales_1.partner_id)
        self.assertEquals(sales_1.partner_id.email, 'ray@test.com')
        self.assertEquals(sales_1.partner_id.phone, '911000111')
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '45631')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_fr)
        self.assertEquals(
            sales_1.fiscal_position_id,
            self.fiscal_position_fr)
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(
            sales_1.order_line.product_id.name,
            'Product test invoice policy order')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.10, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_10)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.10, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.10, 2))
        self.assertEquals(sales_1.state, 'draft')
        self.assertEquals(len(sales_1.picking_ids), 0)
        self.assertEquals(len(sales_1.invoice_ids), 0)
        self.check_manual_confirm_and_transfer(sales_1)

    def test_import_write_product_invoice_policy_order_error(self):
        self.env['sale.order'].create({
            'origin': 'Beezup sale number: 407-3315028-8261943',
            'partner_id': self.partner_test1.id,
        })
        fname = self.get_file('sample_product_invoice_policy_order.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 1)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 1)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: The invoice policy of the products of order with origin '
            'Beezup sale number: 407-3315028-8261943 is [\'order\'] and is '
            'not contemplated. It must be \'delivery\', so the pickings and '
            'the invoice has not been created; check manually.'),
            wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertFalse(sales_1.partner_id.parent_id)
        self.assertEquals(sales_1.partner_invoice_id, sales_1.partner_id)
        self.assertEquals(sales_1.partner_shipping_id, sales_1.partner_id)
        self.assertEquals(sales_1.partner_id.email, 'ray@test.com')
        self.assertEquals(sales_1.partner_id.phone, '911000111')
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '45631')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_fr)
        self.assertEquals(
            sales_1.fiscal_position_id,
            self.fiscal_position_fr)
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(
            sales_1.order_line.product_id.name,
            'Product test invoice policy order')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.10, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_10)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.10, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.10, 2))
        self.assertEquals(sales_1.state, 'draft')
        self.assertEquals(len(sales_1.picking_ids), 0)
        self.assertEquals(len(sales_1.invoice_ids), 0)
        self.check_manual_confirm_and_transfer(sales_1)

    def test_import_product_not_exist(self):
        self.env.user.company_id.beezup_tax_ids = [(6, 0, self.tax_10.ids)]
        self.assertEquals(self.env.user.company_id.beezup_tax_ids, self.tax_10)
        fname = self.get_file('sample_default_code_not_exist.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'connector_beezup.template_sale_beezup').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        sale_beezup = self.env['import.template.sale_beezup'].with_context(
            wizard_id=wizard.id).create({
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'journal_payment_id': self.cash_journal_test.id,
            })
        sale_beezup.action_import_file()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: No product found for default_code \'3322\'; the product is '
            'created'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: No product found for default_code \'1234\'; the product '
            'is created'), wizard.line_ids[1].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_beezup.pricelist_id, self.pricelist_test)
        self.assertEquals(sale_beezup.carrier_id, self.carrier_test)
        self.assertEquals(sale_beezup.payment_mode_id, self.payment_mode_test)
        self.assertEquals(
            sale_beezup.shipping_product_id, self.shipping_product_test)
        self.assertEquals(
            sale_beezup.journal_payment_id, self.cash_journal_test)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: No product found for default_code \'3322\'; the product is '
            'created'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: No product found for default_code \'1234\'; the product '
            'is created'), wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Raymond okeke'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-3315028-8261943'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Raymond okeke')
        self.assertFalse(sales_1.partner_id.parent_id)
        self.assertEquals(sales_1.partner_invoice_id, sales_1.partner_id)
        self.assertEquals(sales_1.partner_shipping_id, sales_1.partner_id)
        self.assertEquals(sales_1.partner_id.email, 'ray@test.com')
        self.assertEquals(sales_1.partner_id.phone, '911000111')
        self.assertEquals(sales_1.partner_id.mobile, '665008937')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '45631')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'FR')
        self.assertEquals(
            sales_1.partner_id.property_account_position_id,
            self.fiscal_position_fr)
        self.assertEquals(
            sales_1.fiscal_position_id,
            self.fiscal_position_fr)
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertIn(
            'SmartWatch U Reloj Inteligente 8',
            sales_1.order_line.product_id.name)
        self.assertEquals(sales_1.order_line.product_id.default_code, '3322')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        price_unit = round(23.95 / 1.10, 2)
        self.assertEquals(sales_1.order_line.price_unit, price_unit)
        self.assertEquals(sales_1.order_line.tax_id, self.tax_10)
        self.assertEquals(sales_1.amount_untaxed, price_unit)
        self.assertEquals(sales_1.amount_tax, round(price_unit * 0.10, 2))
        self.assertEquals(sales_1.amount_total, round(price_unit * 1.10, 2))
        self.assertEquals(sales_1.state, 'sale')
        self.assertEquals(len(sales_1.picking_ids), 2)
        self.assertEquals(
            sales_1.picking_ids[0].partner_id, sales_1.partner_id)
        self.assertEquals(
            sales_1.picking_ids[1].partner_id, sales_1.partner_id)
        self.assertEquals(sales_1.picking_ids[0].picking_type_code, 'incoming')
        self.assertEquals(sales_1.picking_ids[0].state, 'done')
        self.assertEquals(sales_1.picking_ids[1].picking_type_code, 'outgoing')
        self.assertEquals(sales_1.picking_ids[1].state, 'done')
        self.assertEquals(len(sales_1.invoice_ids), 1)
        self.assertEquals(sales_1.invoice_ids.partner_id, sales_1.partner_id)
        self.assertEquals(sales_1.invoice_ids.state, 'paid')
        self.assertEquals(len(sales_1.invoice_ids.payment_ids), 1)
        self.assertEquals(
            sales_1.invoice_ids.payment_ids.journal_id, self.cash_journal_test)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'Antonia Pérez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Beezup sale number: 407-7546216-0559553'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'Antonia Pérez')
        self.assertFalse(sales_2.partner_id.parent_id)
        self.assertEquals(sales_2.partner_invoice_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(sales_2.partner_id.email, 'antonia@test.com')
        self.assertEquals(sales_2.partner_id.phone, '666888999')
        self.assertEquals(sales_2.partner_id.mobile, '666000666')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, 'Calle Real, 3')
        self.assertEquals(sales_2.partner_id.street2, '')
        self.assertEquals(sales_2.partner_id.city, 'ALICANTE')
        self.assertEquals(sales_2.partner_id.zip, '3012')
        self.assertEquals(
            sales_2.partner_id.state_id.name, 'Alacant (Alicante)')
        self.assertEquals(sales_2.partner_id.state_id.code, 'A')
        self.assertEquals(sales_2.partner_id.country_id.code, 'ES')
        self.assertEquals(
            sales_2.partner_id.property_account_position_id,
            self.fiscal_position_es)
        self.assertEquals(sales_2.fiscal_position_id, self.fiscal_position_es)
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertIn('Adhesivo Teclado', sales_2.order_line.product_id.name)
        self.assertEquals(sales_2.order_line.product_id.default_code, '1234')
        self.assertEquals(sales_2.order_line.product_uom_qty, 1)
        price_unit = round(4.75 / 1.10, 2)
        self.assertEquals(sales_2.order_line.price_unit, price_unit)
        self.assertEquals(sales_2.order_line.tax_id, self.tax_10)
        self.assertEquals(sales_2.amount_untaxed, price_unit)
        self.assertEquals(sales_2.amount_tax, round(price_unit * 0.10, 2))
        self.assertEquals(sales_2.amount_total, round(price_unit * 1.10, 2))
        self.assertEquals(sales_2.state, 'draft')
        self.assertEquals(len(sales_2.picking_ids), 0)
        self.assertEquals(len(sales_2.invoice_ids), 0)
