###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import os

from odoo.tests.common import TransactionCase


class TestImportTemplateSaleAmazon(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner1 = self.env['res.partner'].create({
            'name': 'Partner test 1',
            'customer': True,
        })
        self.partner2 = self.env['res.partner'].create({
            'name': 'Partner test 2',
            'customer': True,
        })
        self.fiscal_position_es = self.env['account.fiscal.position'].create({
            'name': 'Fiscal position es',
            'country_id': self.env.ref('base.es').id
        })
        partner_account = self.env['account.account'].create({
            'code': 'xxx',
            'user_type_id': self.ref('account.data_account_type_receivable'),
            'name': 'Partner account',
            'reconcile': True,
        })
        self.partner_parent_test = self.env['res.partner'].create({
            'name': 'Partner parent test',
            'customer': True,
            'vat': '12345678A',
            'property_account_receivable_id': partner_account.id,
            'property_account_position_id': self.fiscal_position_es.id,
        })
        self.tax_21 = self.env['account.tax'].create({
            'name': '%21%',
            'amount_type': 'percent',
            'amount': 21,
            'type_tax_use': 'sale',
        })
        self.product1 = self.env['product.product'].create({
            'name': 'Product test 1',
            'default_code': '92385',
            'list_price': 10,
            'type': 'product',
            'taxes_id': [(6, 0, self.tax_21.ids)],
        })
        self.product2 = self.env['product.product'].create({
            'name': 'Product test 2',
            'default_code': '50944',
            'list_price': 9,
            'type': 'product',
            'taxes_id': [(6, 0, self.tax_21.ids)],
        })
        self.product3 = self.env['product.product'].create({
            'name': 'Product test 3',
            'default_code': 'xxxxx',
            'list_price': 100,
            'type': 'product',
            'taxes_id': [(6, 0, [self.tax_21.id])]
        })
        self.shipping_product_test = self.env['product.product'].create({
            'name': 'Shipping costs',
            'type': 'service',
            'default_code': 'SHIPPTEST',
            'standard_price': 3,
            'list_price': 5,
            'taxes_id': [(6, 0, self.tax_21.ids)],
        })
        self.product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
            'taxes_id': [(6, 0, self.tax_21.ids)],
        })
        self.pricelist_test = self.env['product.pricelist'].create({
            'name': 'Pricelist test',
            'item_ids': [
                (0, 0, {
                    'applied_on': '3_global',
                    'compute_price': 'formula',
                    'base': 'list_price',
                    'price_surcharge': 0.99,
                }),
            ],
        })
        self.carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'delivery_type': 'fixed',
            'product_id': self.product_carrier.id,
        })
        self.payment_mode_test = self.env['account.payment.mode'].create({
            'name': 'Payment mode customer test',
            'payment_method_id': self.env.ref(
                'account.account_payment_method_manual_in').id,
            'payment_type': 'inbound',
            'bank_account_link': 'variable',
        })

    def get_sample(self, fname):
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.state_id.code, 'TX')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(sales_1.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        # @TODO 17.31=col AQ=vat-exclusive-item-price
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        # @TODO 3.6351=col N=item-tax
        self.assertEquals(sales_1.amount_tax, round(17.31 * 0.21, 2))
        # @TODO 20.9451=col M=item-price
        self.assertEquals(sales_1.amount_total, round(17.31 * 1.21, 2))
        self.check_manual_confirm_and_transfer(sales_1)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(sales_2.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.order_line.price_subtotal, 57.80)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))
        self.check_manual_confirm_and_transfer(sales_2)

    def test_import_write_ok(self):
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': self.partner1.id,
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(sales_1.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        # @TODO 17.31=col AQ=vat-exclusive-item-price
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        # @TODO 3.6351=col N=item-tax
        self.assertEquals(sales_1.amount_tax, round(17.31 * 0.21, 2))
        # @TODO 20.9451=col M=item-price
        self.assertEquals(sales_1.amount_total, round(17.31 * 1.21, 2))
        self.check_manual_confirm_and_transfer(sales_1)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(sales_2.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.order_line.price_subtotal, 57.80)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))
        self.check_manual_confirm_and_transfer(sales_2)

    def test_import_create_ok_force_partner(self):
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'force_partner': True,
                'parent_partner_id': self.partner_parent_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_1.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_1.partner_shipping_id, sales_1.partner_id)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.state_id.code, 'TX')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(sales_1.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        # @TODO 17.31=col AQ=vat-exclusive-item-price
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        # @TODO 3.6351=col N=item-tax
        self.assertEquals(sales_1.amount_tax, round(17.31 * 0.21, 2))
        # @TODO 20.9451=col M=item-price
        self.assertEquals(sales_1.amount_total, round(17.31 * 1.21, 2))
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(sales_2.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.order_line.price_subtotal, 57.80)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))

    def test_import_write_ok_force_partner(self):
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': self.partner1.id,
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'force_partner': True,
                'parent_partner_id': self.partner_parent_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_1.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_1.partner_shipping_id, sales_1.partner_id)
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.state_id.code, 'TX')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(sales_1.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        # @TODO 17.31=col AQ=vat-exclusive-item-price
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        # @TODO 3.6351=col N=item-tax
        self.assertEquals(sales_1.amount_tax, round(17.31 * 0.21, 2))
        # @TODO 20.9451=col M=item-price
        self.assertEquals(sales_1.amount_total, round(17.31 * 1.21, 2))
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(sales_2.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.order_line.price_subtotal, 57.80)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))

    def test_import_default_wizard_values_create_ok(self):
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
        default_shipping_product = self.env[
            'import.template.sale_amazon']._default_shipping_product_id()
        self.assertEquals(sale_amazon.pricelist_id.id, default_pricelist.id)
        self.assertEquals(sale_amazon.carrier_id.id, default_carrier.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, default_payment_mode.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, default_shipping_product.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.state_id.code, 'TX')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id, default_pricelist)
        self.assertEquals(sales_1.carrier_id, default_carrier)
        self.assertEquals(sales_1.payment_mode_id, default_payment_mode)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, round(17.31 * 0.21, 2))
        self.assertEquals(sales_1.amount_total, round(17.31 * 1.21, 2))
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id, default_pricelist)
        self.assertEquals(sales_2.carrier_id, default_carrier)
        self.assertEquals(sales_2.payment_mode_id, default_payment_mode)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.order_line.price_subtotal, 57.80)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))

    def test_import_default_wizard_values_write_ok(self):
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': self.partner1.id,
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
        default_shipping_product = self.env[
            'import.template.sale_amazon']._default_shipping_product_id()
        self.assertEquals(sale_amazon.pricelist_id.id, default_pricelist.id)
        self.assertEquals(sale_amazon.carrier_id.id, default_carrier.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, default_payment_mode.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, default_shipping_product.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.state_id.code, 'TX')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id, default_pricelist)
        self.assertEquals(sales_1.carrier_id, default_carrier)
        self.assertEquals(sales_1.payment_mode_id, default_payment_mode)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, round(17.31 * 0.21, 2))
        self.assertEquals(sales_1.amount_total, round(17.31 * 1.21, 2))
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id, default_pricelist)
        self.assertEquals(sales_2.carrier_id, default_carrier)
        self.assertEquals(sales_2.payment_mode_id, default_payment_mode)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.order_line.price_subtotal, 57.80)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))

    def test_import_default_wizard_values_create_ok_force_partner(self):
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
                'force_partner': True,
                'parent_partner_id': self.partner_parent_test.id,
            })
        sale_amazon.action_import_file()
        default_pricelist = self.env[
            'import.template.sale_amazon']._default_pricelist_id()
        default_carrier = self.env[
            'import.template.sale_amazon']._default_carrier_id()
        default_payment_mode = self.env[
            'import.template.sale_amazon']._default_payment_mode_id()
        default_shipping_product = self.env[
            'import.template.sale_amazon']._default_shipping_product_id()
        self.assertEquals(sale_amazon.pricelist_id.id, default_pricelist.id)
        self.assertEquals(sale_amazon.carrier_id.id, default_carrier.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, default_payment_mode.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, default_shipping_product.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_1.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_1.partner_shipping_id, sales_1.partner_id)
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.state_id.code, 'TX')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id, default_pricelist)
        self.assertEquals(sales_1.carrier_id, default_carrier)
        self.assertEquals(sales_1.payment_mode_id, default_payment_mode)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, round(17.31 * 0.21, 2))
        self.assertEquals(sales_1.amount_total, round(17.31 * 1.21, 2))
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id, default_pricelist)
        self.assertEquals(sales_2.carrier_id, default_carrier)
        self.assertEquals(sales_2.payment_mode_id, default_payment_mode)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.order_line.price_subtotal, 57.80)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))

    def test_import_default_wizard_values_write_ok_force_partner(self):
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': self.partner1.id,
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
                'force_partner': True,
                'parent_partner_id': self.partner_parent_test.id,
            })
        sale_amazon.action_import_file()
        default_pricelist = self.env[
            'import.template.sale_amazon']._default_pricelist_id()
        default_carrier = self.env[
            'import.template.sale_amazon']._default_carrier_id()
        default_payment_mode = self.env[
            'import.template.sale_amazon']._default_payment_mode_id()
        default_shipping_product = self.env[
            'import.template.sale_amazon']._default_shipping_product_id()
        self.assertEquals(sale_amazon.pricelist_id.id, default_pricelist.id)
        self.assertEquals(sale_amazon.carrier_id.id, default_carrier.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, default_payment_mode.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, default_shipping_product.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_1.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_1.partner_shipping_id, sales_1.partner_id)
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.state_id.code, 'TX')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id, default_pricelist)
        self.assertEquals(sales_1.carrier_id, default_carrier)
        self.assertEquals(sales_1.payment_mode_id, default_payment_mode)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, round(17.31 * 0.21, 2))
        self.assertEquals(sales_1.amount_total, round(17.31 * 1.21, 2))
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id, default_pricelist)
        self.assertEquals(sales_2.carrier_id, default_carrier)
        self.assertEquals(sales_2.payment_mode_id, default_payment_mode)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.order_line.price_subtotal, 57.80)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))

    def test_import_order_id_empty_create_error(self):
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(
            '2: Column \'order_id\' cannot be empty.', wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(
            '2: Column \'order_id\' cannot be empty.', wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(sales_2.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.order_line.price_subtotal, 57.80)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))

    def test_import_order_id_empty_write_error(self):
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': self.partner1.id,
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(
            '2: Column \'order_id\' cannot be empty.', wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(
            '2: Column \'order_id\' cannot be empty.', wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Partner test 1')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(sales_2.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.order_line.price_subtotal, 57.80)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))

    def test_import_order_id_empty_create_error_force_partner(self):
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'force_partner': True,
                'parent_partner_id': self.partner_parent_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(
            '2: Column \'order_id\' cannot be empty.', wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(
            '2: Column \'order_id\' cannot be empty.', wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(sales_2.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.order_line.price_subtotal, 57.80)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))

    def test_import_order_id_empty_write_error_force_partner(self):
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': self.partner1.id,
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'force_partner': True,
                'parent_partner_id': self.partner_parent_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(
            '2: Column \'order_id\' cannot be empty.', wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(
            '2: Column \'order_id\' cannot be empty.', wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Partner test 1')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(sales_2.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.order_line.price_subtotal, 57.80)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))

    def test_import_partner_id_empty_create_error(self):
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn('2: Contact empty not found.', wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn('2: Contact empty not found.', wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(sales_2.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.order_line.price_subtotal, 57.80)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))

    def test_import_partner_id_empty_write_error(self):
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': self.partner1.id,
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn('2: Contact empty not found.', wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn('2: Contact empty not found.', wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Partner test 1')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(sales_2.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.order_line.price_subtotal, 57.80)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))

    def test_import_partner_id_empty_create_error_force_partner(self):
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'force_partner': True,
                'parent_partner_id': self.partner_parent_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn('2: Contact empty not found.', wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn('2: Contact empty not found.', wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(sales_2.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.order_line.price_subtotal, 57.80)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))

    def test_import_partner_id_empty_write_error_force_partner(self):
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': self.partner1.id,
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'force_partner': True,
                'parent_partner_id': self.partner_parent_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn('2: Contact empty not found.', wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn('2: Contact empty not found.', wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Partner test 1')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(sales_2.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.order_line.price_subtotal, 57.80)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))

    def test_import_default_code_empty_create_error(self):
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(
            '2: Default code empty not found.', wizard.line_ids[0].name)
        self.assertIn(
            '2: Column \'product_id\' cannot be empty.',
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(
            '2: Default code empty not found.', wizard.line_ids[0].name)
        self.assertIn(
            '2: Column \'product_id\' cannot be empty.',
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(sales_2.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.order_line.price_subtotal, 57.80)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))

    def test_import_default_code_empty_write_error(self):
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': self.partner1.id,
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(
            '2: Default code empty not found.', wizard.line_ids[0].name)
        self.assertIn(
            '2: Column \'product_id\' cannot be empty.',
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(
            '2: Default code empty not found.', wizard.line_ids[0].name)
        self.assertIn(
            '2: Column \'product_id\' cannot be empty.',
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Partner test 1')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(sales_2.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.order_line.price_subtotal, 57.80)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))

    def test_import_default_code_empty_create_error_force_partner(self):
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'force_partner': True,
                'parent_partner_id': self.partner_parent_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(
            '2: Default code empty not found.', wizard.line_ids[0].name)
        self.assertIn(
            '2: Column \'product_id\' cannot be empty.',
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(
            '2: Default code empty not found.', wizard.line_ids[0].name)
        self.assertIn(
            '2: Column \'product_id\' cannot be empty.',
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(sales_2.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.order_line.price_subtotal, 57.80)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))

    def test_import_default_code_empty_write_error_force_partner(self):
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': self.partner1.id,
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'force_partner': True,
                'parent_partner_id': self.partner_parent_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(
            '2: Default code empty not found.', wizard.line_ids[0].name)
        self.assertIn(
            '2: Column \'product_id\' cannot be empty.',
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(
            '2: Default code empty not found.', wizard.line_ids[0].name)
        self.assertIn(
            '2: Column \'product_id\' cannot be empty.',
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Partner test 1')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.parent_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_invoice_id, self.partner_parent_test)
        self.assertEquals(sales_2.partner_shipping_id, sales_2.partner_id)
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, self.partner_parent_test.vat)
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(sales_2.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.order_line.price_subtotal, 57.80)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))

    def test_import_duply_product_create_error(self):
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(
            '2: More than one product found for 92385.',
            wizard.line_ids[0].name)
        self.assertIn(
            '3: More than one product found for 92385.',
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(
            '2: More than one product found for 92385.',
            wizard.line_ids[0].name)
        self.assertIn(
            '3: More than one product found for 92385.',
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)

    def test_import_duply_product_write_error(self):
        self.env['product.product'].create({
            'name': 'Product test duply',
            'default_code': '92385',
            'list_price': 33,
            'type': 'product',
        })
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': self.partner1.id,
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(
            '2: More than one product found for 92385.',
            wizard.line_ids[0].name)
        self.assertIn(
            '3: More than one product found for 92385.',
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(
            '2: More than one product found for 92385.',
            wizard.line_ids[0].name)
        self.assertIn(
            '3: More than one product found for 92385.',
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Partner test 1')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)

    def test_import_duply_product_create_error_force_partner(self):
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'force_partner': True,
                'parent_partner_id': self.partner_parent_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(
            '2: More than one product found for 92385.',
            wizard.line_ids[0].name)
        self.assertIn(
            '3: More than one product found for 92385.',
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(
            '2: More than one product found for 92385.',
            wizard.line_ids[0].name)
        self.assertIn(
            '3: More than one product found for 92385.',
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)

    def test_import_duply_product_write_error_force_partner(self):
        self.env['product.product'].create({
            'name': 'Product test duply',
            'default_code': '92385',
            'list_price': 33,
            'type': 'product',
        })
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': self.partner1.id,
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
                'force_partner': True,
                'parent_partner_id': self.partner_parent_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(
            '2: More than one product found for 92385.',
            wizard.line_ids[0].name)
        self.assertIn(
            '3: More than one product found for 92385.',
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(
            '2: More than one product found for 92385.',
            wizard.line_ids[0].name)
        self.assertIn(
            '3: More than one product found for 92385.',
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, 'Partner test 1')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)

    def test_import_duply_origin_error(self):
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': self.partner1.id,
        })
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': self.partner2.id,
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 2)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(
            '2: More than one sale order with origin \'Amazon sale number: '
            '406-9428643-3124325\' has been found. The order details could '
            'not be imported.',
            wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 2)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(sales_2.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.order_line.price_subtotal, 57.80)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))

    def test_import_order_with_serveral_lines_create_ok(self):
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(len(sales_1.order_line), 2)
        line_product1 = sales_1.order_line.filtered(
            lambda ln: ln.product_id == self.product1)
        self.assertEquals(len(line_product1), 1)
        self.assertEquals(line_product1.product_uom_qty, 1)
        self.assertEquals(line_product1.price_unit, 17.31)
        line_product2 = sales_1.order_line.filtered(
            lambda ln: ln.product_id == self.product2)
        self.assertEquals(len(line_product2), 1)
        self.assertEquals(line_product2.product_uom_qty, 3)
        self.assertEquals(line_product2.price_unit, round(57.81 / 3, 2))

        self.assertEquals(sales_1.amount_untaxed, round(17.31 + 57.81, 2))
        self.assertEquals(
            sales_1.amount_tax, round(17.31 * 0.21 + 57.81 * 0.21, 2))
        self.assertEquals(
            sales_1.amount_total, round(17.31 * 1.21 + 57.81 * 1.21, 2))
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(sales_2.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 8.65)
        self.assertEquals(sales_2.order_line.price_subtotal, 17.30)
        self.assertEquals(sales_2.amount_untaxed, 17.30)
        self.assertEquals(sales_2.amount_tax, round(17.30 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(17.30 * 1.21, 2))

    def test_import_order_with_serveral_lines_write_draft_ok(self):
        order = self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': self.partner1.id,
        })
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product1.id,
            'product_uom_qty': 1,
            'product_uom': self.product1.uom_id.id,
        })
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product3.id,
            'product_uom_qty': 1,
            'product_uom': self.product3.uom_id.id,
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(len(sales_1.order_line), 2)
        line_product1 = sales_1.order_line.filtered(
            lambda ln: ln.product_id == self.product1)
        self.assertEquals(len(line_product1), 1)
        self.assertEquals(line_product1.product_uom_qty, 1)
        self.assertEquals(line_product1.price_unit, 10)
        line_product3 = sales_1.order_line.filtered(
            lambda ln: ln.product_id == self.product3)
        self.assertEquals(len(line_product3), 1)
        self.assertEquals(line_product3.product_uom_qty, 1)
        self.assertEquals(line_product3.price_unit, 100)
        self.assertEquals(sales_1.amount_untaxed, 10 + 100)
        self.assertEquals(sales_1.amount_tax, round(10 * 0.21 + 100 * 0.21, 2))
        self.assertEquals(
            sales_1.amount_total, round(10 * 1.21 + 100 * 1.21, 2))
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(len(sales_1.order_line), 2)
        line_product1 = sales_1.order_line.filtered(
            lambda ln: ln.product_id == self.product1)
        self.assertEquals(len(line_product1), 1)
        self.assertEquals(line_product1.product_uom_qty, 1)
        self.assertEquals(line_product1.price_unit, 17.31)
        line_product2 = sales_1.order_line.filtered(
            lambda ln: ln.product_id == self.product2)
        self.assertEquals(len(line_product2), 1)
        self.assertEquals(line_product2.product_uom_qty, 3)
        self.assertEquals(line_product2.price_unit, round(57.81 / 3, 2))
        self.assertEquals(sales_1.amount_untaxed, round(17.31 + 57.81, 2))
        self.assertEquals(
            sales_1.amount_tax, round(17.31 * 0.21 + 57.81 * 0.21, 2))
        self.assertEquals(
            sales_1.amount_total, round(17.31 * 1.21 + 57.81 * 1.21, 2))
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(sales_2.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 8.65)
        self.assertEquals(sales_2.order_line.price_subtotal, 17.30)
        self.assertEquals(sales_2.amount_untaxed, 17.30)
        self.assertEquals(sales_2.amount_tax, round(17.30 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(17.30 * 1.21, 2))

    def test_import_order_with_serveral_lines_write_confirm_error(self):
        order = self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': self.partner1.id,
        })
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product1.id,
            'product_uom_qty': 1,
            'product_uom': self.product1.uom_id.id,
        })
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product3.id,
            'product_uom_qty': 1,
            'product_uom': self.product3.uom_id.id,
        })
        order.action_confirm()
        self.assertEquals(order.state, 'sale')
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(len(sales_1.order_line), 2)
        line_product1 = sales_1.order_line.filtered(
            lambda ln: ln.product_id == self.product1)
        self.assertEquals(len(line_product1), 1)
        self.assertEquals(line_product1.product_uom_qty, 1)
        self.assertEquals(line_product1.price_unit, 10)
        line_product3 = sales_1.order_line.filtered(
            lambda ln: ln.product_id == self.product3)
        self.assertEquals(len(line_product3), 1)
        self.assertEquals(line_product3.product_uom_qty, 1)
        self.assertEquals(line_product3.price_unit, 100)
        self.assertEquals(sales_1.amount_untaxed, 10 + 100)
        self.assertEquals(sales_1.amount_tax, round(10 * 0.21 + 100 * 0.21, 2))
        self.assertEquals(
            sales_1.amount_total, round(10 * 1.21 + 100 * 1.21, 2))
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(
            '2, 3: The order with origin \'Amazon sale number: '
            '406-9428643-3124325\' cannot be modified because it is not in a '
            'draft state.', wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(len(sales_1.order_line), 2)
        line_product1 = sales_1.order_line.filtered(
            lambda ln: ln.product_id == self.product1)
        self.assertEquals(len(line_product1), 1)
        self.assertEquals(line_product1.product_uom_qty, 1)
        self.assertEquals(line_product1.price_unit, 10)
        line_product3 = sales_1.order_line.filtered(
            lambda ln: ln.product_id == self.product3)
        self.assertEquals(len(line_product3), 1)
        self.assertEquals(line_product3.product_uom_qty, 1)
        self.assertEquals(line_product3.price_unit, 100)
        self.assertEquals(sales_1.amount_untaxed, 10 + 100)
        self.assertEquals(sales_1.amount_tax, round(10 * 0.21 + 100 * 0.21, 2))
        self.assertEquals(
            sales_1.amount_total, round(10 * 1.21 + 100 * 1.21, 2))
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(sales_2.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 8.65)
        self.assertEquals(sales_2.order_line.price_subtotal, 17.30)
        self.assertEquals(sales_2.amount_untaxed, 17.30)
        self.assertEquals(sales_2.amount_tax, round(17.30 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(17.30 * 1.21, 2))

    def test_import_order_with_serveral_lines_duply_order_error(self):
        order1 = self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': self.partner1.id,
        })
        self.env['sale.order.line'].create({
            'order_id': order1.id,
            'product_id': self.product1.id,
            'product_uom_qty': 1,
            'product_uom': self.product1.uom_id.id,
        })
        self.env['sale.order.line'].create({
            'order_id': order1.id,
            'product_id': self.product3.id,
            'product_uom_qty': 1,
            'product_uom': self.product3.uom_id.id,
        })
        order2 = self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': self.partner1.id,
        })
        self.env['sale.order.line'].create({
            'order_id': order2.id,
            'product_id': self.product1.id,
            'product_uom_qty': 10,
            'product_uom': self.product1.uom_id.id,
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 2)
        sale1_1 = sales_1.filtered(lambda so: len(so.order_line) == 2)
        self.assertEquals(len(sale1_1), 1)
        line_product1 = sale1_1.order_line.filtered(
            lambda ln: ln.product_id == self.product1)
        self.assertEquals(len(line_product1), 1)
        self.assertEquals(line_product1.product_uom_qty, 1)
        self.assertEquals(line_product1.price_unit, 10)
        line_product3 = sale1_1.order_line.filtered(
            lambda ln: ln.product_id == self.product3)
        self.assertEquals(len(line_product3), 1)
        self.assertEquals(line_product3.product_uom_qty, 1)
        self.assertEquals(line_product3.price_unit, 100)
        sale1_2 = sales_1.filtered(lambda so: len(so.order_line) == 1)
        self.assertEquals(len(sale1_2), 1)
        self.assertEquals(sale1_2.order_line.product_uom_qty, 10)
        self.assertEquals(sale1_2.order_line.price_unit, 10)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(
            '2, 3: More than one sale order with origin \'Amazon sale number: '
            '406-9428643-3124325\' has been found. The order details could '
            'not be imported.', wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 2)
        sale1_1 = sales_1.filtered(lambda so: len(so.order_line) == 2)
        self.assertEquals(len(sale1_1), 1)
        line_product1 = sale1_1.order_line.filtered(
            lambda ln: ln.product_id == self.product1)
        self.assertEquals(len(line_product1), 1)
        self.assertEquals(line_product1.product_uom_qty, 1)
        self.assertEquals(line_product1.price_unit, 10)
        line_product3 = sale1_1.order_line.filtered(
            lambda ln: ln.product_id == self.product3)
        self.assertEquals(len(line_product3), 1)
        self.assertEquals(line_product3.product_uom_qty, 1)
        self.assertEquals(line_product3.price_unit, 100)
        sale1_2 = sales_1.filtered(lambda so: len(so.order_line) == 1)
        self.assertEquals(len(sale1_2), 1)
        self.assertEquals(sale1_2.order_line.product_uom_qty, 10)
        self.assertEquals(sale1_2.order_line.price_unit, 10)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(sales_2.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 8.65)
        self.assertEquals(sales_2.order_line.price_subtotal, 17.30)
        self.assertEquals(sales_2.amount_untaxed, 17.30)
        self.assertEquals(sales_2.amount_tax, round(17.30 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(17.30 * 1.21, 2))

    def test_new_fields_ok(self):
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.state_id.code, 'TX')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_1.carrier_id, self.carrier_test)
        self.assertEquals(sales_1.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.order_line.sequence, 33)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, round(17.31 * 0.21, 2))
        self.assertEquals(sales_1.amount_total, round(17.31 * 1.21, 2))
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id, self.pricelist_test)
        self.assertEquals(sales_2.carrier_id, self.carrier_test)
        self.assertEquals(sales_2.payment_mode_id, self.payment_mode_test)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.order_line.price_subtotal, 57.80)
        self.assertEquals(sales_2.order_line.sequence, 44)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))

    def test_new_fields_error(self):
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(
            '2: The \'company_id\' column is a relational field and there is '
            'no defined function to convert it.', wizard.line_ids[0].name)
        self.assertIn(
            '3: The \'company_id\' column is a relational field and there is '
            'no defined function to convert it.', wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(
            '2: The \'company_id\' column is a relational field and there is '
            'no defined function to convert it.', wizard.line_ids[0].name)
        self.assertIn(
            '3: The \'company_id\' column is a relational field and there is '
            'no defined function to convert it.', wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)

    def test_import_create_disordered_columns_ok(self):
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.state_id.code, 'TX')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id.name, self.pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, self.carrier_test.name)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.order_line.sequence, 33)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, round(17.31 * 0.21, 2))
        self.assertEquals(sales_1.amount_total, round(17.31 * 1.21, 2))
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, self.pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, self.carrier_test.name)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.order_line.price_subtotal, 57.80)
        self.assertEquals(sales_2.order_line.sequence, 44)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_write_disordered_columns_ok(self):
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': self.partner1.id,
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.state_id.code, 'TX')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id.name, self.pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, self.carrier_test.name)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.order_line.sequence, 33)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, round(17.31 * 0.21, 2))
        self.assertEquals(sales_1.amount_total, round(17.31 * 1.21, 2))
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, self.pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, self.carrier_test.name)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.order_line.price_subtotal, 57.80)
        self.assertEquals(sales_2.order_line.sequence, 44)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_with_shipping_price_create_ok(self):
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.state_id.code, 'TX')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id.name, self.pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, self.carrier_test.name)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, round(17.31 * 0.21, 2))
        self.assertEquals(sales_1.amount_total, round(17.31 * 1.21, 2))
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, self.pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, self.carrier_test.name)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 2)
        line_product1 = sales_2.order_line.filtered(
            lambda ln: ln.product_id == self.product1)
        self.assertTrue(line_product1)
        self.assertEquals(line_product1.product_uom_qty, 2)
        self.assertEquals(line_product1.price_unit, 28.90)
        line_shipping_product = sales_2.order_line.filtered(
            lambda ln: ln.product_id == self.shipping_product_test)
        self.assertEquals(line_shipping_product.product_uom_qty, 1)
        self.assertEquals(line_shipping_product.price_unit, 4.24)
        amount_untaxed = 57.80 + 4.24
        self.assertEquals(sales_2.amount_untaxed, 57.80 + 4.24)
        self.assertEquals(sales_2.amount_tax, round(amount_untaxed * 0.21, 2))
        self.assertEquals(
            sales_2.amount_total, round(amount_untaxed * 1.21, 2))
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_with_shipping_price_write_ok(self):
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 403-7709102-2516320',
            'partner_id': self.partner1.id,
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.state_id.code, 'TX')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id.name, self.pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, self.carrier_test.name)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, round(17.31 * 0.21, 2))
        self.assertEquals(sales_1.amount_total, round(17.31 * 1.21, 2))
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_1.partner_id.state_id.code, 'TX')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, self.pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, self.carrier_test.name)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 2)
        line_product1 = sales_2.order_line.filtered(
            lambda ln: ln.product_id == self.product1)
        self.assertTrue(line_product1)
        self.assertEquals(line_product1.product_uom_qty, 2)
        self.assertEquals(line_product1.price_unit, 28.90)
        line_shipping_product = sales_2.order_line.filtered(
            lambda ln: ln.product_id == self.shipping_product_test)
        self.assertEquals(line_shipping_product.product_uom_qty, 1)
        self.assertEquals(line_shipping_product.price_unit, 4.24)
        amount_untaxed = 57.80 + 4.24
        self.assertEquals(sales_2.amount_untaxed, 57.80 + 4.24)
        self.assertEquals(sales_2.amount_tax, round(amount_untaxed * 0.21, 2))
        self.assertEquals(
            sales_2.amount_total, round(amount_untaxed * 1.21, 2))
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_new_state_id_without_country_create_ok(self):
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(
            '2: Country code empty not found; \'No country\' is assigned.',
            wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        state = self.env['res.country.state'].search([
            ('name', '=', 'Granada'),
            ('country_id', '=', self.env.ref('import_template.no_country').id),
        ])
        self.assertEquals(len(state), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(
            '2: Country code empty not found; \'No country\' is assigned.',
            wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        state = self.env['res.country.state'].search([
            ('name', '=', 'Granada'),
            ('country_id', '=', self.env.ref('import_template.no_country').id),
        ])
        self.assertEquals(len(state), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Granada')
        self.assertEquals(sales_1.partner_id.state_id.code, '00Granada')
        self.assertEquals(sales_1.partner_id.country_id.code, '00')
        self.assertEquals(sales_1.pricelist_id.name, self.pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, self.carrier_test.name)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, round(17.31 * 0.21, 2))
        self.assertEquals(sales_1.amount_total, round(17.31 * 1.21, 2))
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, self.pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, self.carrier_test.name)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_new_state_id_without_country_write_ok(self):
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': self.partner1.id,
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(
            '2: Country code empty not found; \'No country\' is assigned.',
            wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        state = self.env['res.country.state'].search([
            ('name', '=', 'Granada'),
            ('country_id', '=', self.env.ref('import_template.no_country').id),
        ])
        self.assertEquals(len(state), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(
            '2: Country code empty not found; \'No country\' is assigned.',
            wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        state = self.env['res.country.state'].search([
            ('name', '=', 'Granada'),
            ('country_id', '=', self.env.ref('import_template.no_country').id),
        ])
        self.assertEquals(len(state), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Granada')
        self.assertEquals(sales_1.partner_id.state_id.code, '00Granada')
        self.assertEquals(sales_1.partner_id.country_id.code, '00')
        self.assertEquals(sales_1.pricelist_id.name, self.pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, self.carrier_test.name)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, round(17.31 * 0.21, 2))
        self.assertEquals(sales_1.amount_total, round(17.31 * 1.21, 2))
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, self.pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, self.carrier_test.name)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_state_id_without_country_create_ok(self):
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(
            '2: Country code empty not found; \'No country\' is assigned.',
            wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        state = self.env['res.country.state'].search([
            ('name', '=', 'Texas'),
            ('country_id', '=', self.env.ref('import_template.no_country').id),
        ])
        self.assertEquals(len(state), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(
            '2: Country code empty not found; \'No country\' is assigned.',
            wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        state = self.env['res.country.state'].search([
            ('name', '=', 'Texas'),
            ('country_id', '=', self.env.ref('import_template.no_country').id),
        ])
        self.assertEquals(len(state), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.state_id.code, '00Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, '00')
        self.assertEquals(sales_1.pricelist_id.name, self.pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, self.carrier_test.name)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, round(17.31 * 0.21, 2))
        self.assertEquals(sales_1.amount_total, round(17.31 * 1.21, 2))
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, self.pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, self.carrier_test.name)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_state_id_without_country_write_ok(self):
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': self.partner1.id,
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(
            '2: Country code empty not found; \'No country\' is assigned.',
            wizard.line_ids[0].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        state = self.env['res.country.state'].search([
            ('name', '=', 'Texas'),
            ('country_id', '=', self.env.ref('import_template.no_country').id),
        ])
        self.assertEquals(len(state), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(
            '2: Country code empty not found; \'No country\' is assigned.',
            wizard.line_ids[0].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        state = self.env['res.country.state'].search([
            ('name', '=', 'Texas'),
            ('country_id', '=', self.env.ref('import_template.no_country').id),
        ])
        self.assertEquals(len(state), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.state_id.code, '00Texas')
        self.assertEquals(sales_1.partner_id.country_id.code, '00')
        self.assertEquals(sales_1.pricelist_id.name, self.pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, self.carrier_test.name)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, round(17.31 * 0.21, 2))
        self.assertEquals(sales_1.amount_total, round(17.31 * 1.21, 2))
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, self.pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, self.carrier_test.name)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_empty_state_id_empty_country_id_create_ok(self):
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(
            '2: Country code empty not found; \'No country\' is assigned.',
            wizard.line_ids[0].name)
        self.assertIn(
            '2: State name empty not found; not assigned.',
            wizard.line_ids[1].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(
            '2: Country code empty not found; \'No country\' is assigned.',
            wizard.line_ids[0].name)
        self.assertIn(
            '2: State name empty not found; not assigned.',
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertFalse(sales_1.partner_id.state_id.exists())
        self.assertEquals(sales_1.partner_id.country_id.code, '00')
        self.assertEquals(sales_1.pricelist_id.name, self.pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, self.carrier_test.name)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, round(17.31 * 0.21, 2))
        self.assertEquals(sales_1.amount_total, round(17.31 * 1.21, 2))
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, self.pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, self.carrier_test.name)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_empty_state_id_empty_country_id_write_ok(self):
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': self.partner1.id,
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(
            '2: Country code empty not found; \'No country\' is assigned.',
            wizard.line_ids[0].name)
        self.assertIn(
            '2: State name empty not found; not assigned.',
            wizard.line_ids[1].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(
            '2: Country code empty not found; \'No country\' is assigned.',
            wizard.line_ids[0].name)
        self.assertIn(
            '2: State name empty not found; not assigned.',
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertFalse(sales_1.partner_id.state_id.exists())
        self.assertEquals(sales_1.partner_id.country_id.code, '00')
        self.assertEquals(sales_1.pricelist_id.name, self.pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, self.carrier_test.name)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, round(17.31 * 0.21, 2))
        self.assertEquals(sales_1.amount_total, round(17.31 * 1.21, 2))
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, self.pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, self.carrier_test.name)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_empty_no_required_fields_create_ok(self):
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 5)
        self.assertEquals(wizard.total_warn, 5)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(
            '2: Email data not found; not assigned', wizard.line_ids[0].name)
        self.assertIn(
            '2: Phone data not found; not assigned', wizard.line_ids[1].name)
        self.assertIn(
            '2: Street data not found; not assigned', wizard.line_ids[2].name)
        self.assertIn(
            '2: City data not found; not assigned', wizard.line_ids[3].name)
        self.assertIn(
            '2: Zip data not found; not assigned', wizard.line_ids[4].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 5)
        self.assertEquals(wizard.total_warn, 5)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(
            '2: Email data not found; not assigned', wizard.line_ids[0].name)
        self.assertIn(
            '2: Phone data not found; not assigned', wizard.line_ids[1].name)
        self.assertIn(
            '2: Street data not found; not assigned', wizard.line_ids[2].name)
        self.assertIn(
            '2: City data not found; not assigned', wizard.line_ids[3].name)
        self.assertIn(
            '2: Zip data not found; not assigned', wizard.line_ids[4].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(sales_1.partner_id.email, '')
        self.assertEquals(sales_1.partner_id.phone, '')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, '')
        self.assertEquals(sales_1.partner_id.street2, '')
        self.assertEquals(sales_1.partner_id.city, '')
        self.assertEquals(sales_1.partner_id.zip, '')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.state_id.code, 'TX')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id.name, self.pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, self.carrier_test.name)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, round(17.31 * 0.21, 2))
        self.assertEquals(sales_1.amount_total, round(17.31 * 1.21, 2))
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, self.pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, self.carrier_test.name)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_empty_no_required_fields_street_write_ok(self):
        self.env['sale.order'].create({
            'origin': 'Amazon sale number: 406-9428643-3124325',
            'partner_id': self.partner1.id,
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 5)
        self.assertEquals(wizard.total_warn, 5)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(
            '2: Email data not found; not assigned', wizard.line_ids[0].name)
        self.assertIn(
            '2: Phone data not found; not assigned', wizard.line_ids[1].name)
        self.assertIn(
            '2: Street data not found; not assigned', wizard.line_ids[2].name)
        self.assertIn(
            '2: City data not found; not assigned', wizard.line_ids[3].name)
        self.assertIn(
            '2: Zip data not found; not assigned', wizard.line_ids[4].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 5)
        self.assertEquals(wizard.total_warn, 5)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(
            '2: Email data not found; not assigned', wizard.line_ids[0].name)
        self.assertIn(
            '2: Phone data not found; not assigned', wizard.line_ids[1].name)
        self.assertIn(
            '2: Street data not found; not assigned', wizard.line_ids[2].name)
        self.assertIn(
            '2: City data not found; not assigned', wizard.line_ids[3].name)
        self.assertIn(
            '2: Zip data not found; not assigned', wizard.line_ids[4].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(sales_1.partner_id.email, '')
        self.assertEquals(sales_1.partner_id.phone, '')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, '')
        self.assertEquals(sales_1.partner_id.street2, '')
        self.assertEquals(sales_1.partner_id.city, '')
        self.assertEquals(sales_1.partner_id.zip, '')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Texas')
        self.assertEquals(sales_1.partner_id.state_id.code, 'TX')
        self.assertEquals(sales_1.partner_id.country_id.code, 'US')
        self.assertEquals(sales_1.pricelist_id.name, self.pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, self.carrier_test.name)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, round(17.31 * 0.21, 2))
        self.assertEquals(sales_1.amount_total, round(17.31 * 1.21, 2))
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Armilla')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Colorado')
        self.assertEquals(sales_2.partner_id.state_id.code, 'CO')
        self.assertEquals(sales_2.partner_id.country_id.code, 'US')
        self.assertEquals(sales_2.pricelist_id.name, self.pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, self.carrier_test.name)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')

    def test_import_several_state_id_with_code_00(self):
        fname = self.get_sample(
            'sample_new_several_state_id_with_country.txt')
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
                'pricelist_id': self.pricelist_test.id,
                'carrier_id': self.carrier_test.id,
                'payment_mode_id': self.payment_mode_test.id,
                'shipping_product_id': self.shipping_product_test.id,
            })
        sale_amazon.action_import_file()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(
            '2: Country code empty not found; \'No country\' is assigned.',
            wizard.line_ids[0].name)
        self.assertIn(
            '3: Country code empty not found; \'No country\' is assigned.',
            wizard.line_ids[1].name)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 0)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 0)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 0)
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 0)
        state = self.env['res.country.state'].search([
            ('name', '=', 'Granada'),
            ('country_id', '=', self.env.ref('import_template.no_country').id),
        ])
        self.assertEquals(len(state), 0)
        wizard.with_context(
            wizard_id=wizard.id).action_import_from_simulation()
        self.assertEquals(sale_amazon.pricelist_id.id, self.pricelist_test.id)
        self.assertEquals(sale_amazon.carrier_id.id, self.carrier_test.id)
        self.assertEquals(
            sale_amazon.payment_mode_id.id, self.payment_mode_test.id)
        self.assertEquals(
            sale_amazon.shipping_product_id.id, self.shipping_product_test.id)
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(
            '2: Country code empty not found; \'No country\' is assigned.',
            wizard.line_ids[0].name)
        self.assertIn(
            '3: Country code empty not found; \'No country\' is assigned.',
            wizard.line_ids[1].name)
        partner_1 = self.env['res.partner'].search([
            ('name', '=', 'Esther María - Esther'),
        ])
        self.assertEquals(len(partner_1), 1)
        sales_1 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 406-9428643-3124325'),
        ])
        self.assertEquals(len(sales_1), 1)
        state = self.env['res.country.state'].search([
            ('name', '=', 'Granada'),
            ('country_id', '=', self.env.ref('import_template.no_country').id),
        ])
        self.assertEquals(len(state), 1)
        self.assertEquals(sales_1.partner_id.name, u'Esther María - Esther')
        self.assertEquals(
            sales_1.partner_id.email, 'r2rgb50lh44khpr@marketplace.amazon.es')
        self.assertEquals(sales_1.partner_id.phone, '626795384')
        self.assertEquals(sales_1.partner_id.vat, '')
        self.assertEquals(sales_1.partner_id.street, u'Calle Cañada 10')
        self.assertEquals(sales_1.partner_id.street2, 'Casa')
        self.assertEquals(sales_1.partner_id.city, 'Pamplona')
        self.assertEquals(sales_1.partner_id.zip, '08330')
        self.assertEquals(sales_1.partner_id.state_id.name, 'Granada')
        self.assertEquals(sales_1.partner_id.state_id.code, '00Granada')
        self.assertEquals(sales_1.partner_id.country_id.code, '00')
        self.assertEquals(sales_1.pricelist_id.name, self.pricelist_test.name)
        self.assertEquals(sales_1.carrier_id.name, self.carrier_test.name)
        self.assertEquals(
            sales_1.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_1.order_line), 1)
        self.assertEquals(sales_1.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_1.order_line.product_uom_qty, 1)
        self.assertEquals(sales_1.order_line.price_unit, 17.31)
        self.assertEquals(sales_1.amount_untaxed, 17.31)
        self.assertEquals(sales_1.amount_tax, round(17.31 * 0.21, 2))
        self.assertEquals(sales_1.amount_total, round(17.31 * 1.21, 2))
        self.assertEquals(
            sales_1.origin, 'Amazon sale number: 406-9428643-3124325')
        partner_2 = self.env['res.partner'].search([
            ('name', '=', 'José - Antonio Sánchez'),
        ])
        self.assertEquals(len(partner_2), 1)
        sales_2 = self.env['sale.order'].search([
            ('origin', '=', 'Amazon sale number: 403-7709102-2516320'),
        ])
        self.assertEquals(len(sales_2), 1)
        self.assertEquals(sales_2.partner_id.name, u'José - Antonio Sánchez')
        self.assertEquals(
            sales_2.partner_id.email, '0hyxzfkfkzxh77g@marketplace.amazon.es')
        self.assertEquals(sales_2.partner_id.phone, '665008937')
        self.assertEquals(sales_2.partner_id.vat, '')
        self.assertEquals(sales_2.partner_id.street, u'Calle Madrid')
        self.assertEquals(sales_2.partner_id.street2, u'33, 1ºB')
        self.assertEquals(sales_2.partner_id.city, u'Alhama')
        self.assertEquals(sales_2.partner_id.zip, '29793')
        self.assertEquals(sales_2.partner_id.state_id.name, 'Málaga')
        self.assertEquals(sales_2.partner_id.state_id.code, '00Málaga')
        self.assertEquals(sales_2.partner_id.country_id.code, '00')
        self.assertEquals(sales_2.pricelist_id.name, self.pricelist_test.name)
        self.assertEquals(sales_2.carrier_id.name, self.carrier_test.name)
        self.assertEquals(
            sales_2.payment_mode_id.name, self.payment_mode_test.name)
        self.assertEquals(len(sales_2.order_line), 1)
        self.assertEquals(sales_2.order_line.product_id.name, 'Product test 1')
        self.assertEquals(sales_2.order_line.product_uom_qty, 2)
        self.assertEquals(sales_2.order_line.price_unit, 28.90)
        self.assertEquals(sales_2.amount_untaxed, 57.80)
        self.assertEquals(sales_2.amount_tax, round(57.80 * 0.21, 2))
        self.assertEquals(sales_2.amount_total, round(57.80 * 1.21, 2))
        self.assertEquals(
            sales_2.origin, 'Amazon sale number: 403-7709102-2516320')
