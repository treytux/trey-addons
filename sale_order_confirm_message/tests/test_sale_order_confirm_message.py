###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSaleOrderConfirmMessage(TransactionCase):

    def setUp(self):
        super(TestSaleOrderConfirmMessage, self).setUp()
        self.company = self.env.user.company_id
        self.company.write({
            'sale_confirm_message_active': True,
            'sale_confirm_message_require_check': True,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
            'email': 'partner@test.com',
        })
        self.tax = self.env['account.tax'].create({
            'name': 'Test tax 21',
            'amount': 21.0,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
        })
        self.product = self.env['product.product'].create({
            'name': 'Service product',
            'type': 'service',
            'company_id': False,
            'list_price': 100.0,
            'taxes_id': [(6, 0, self.tax.ids)],
        })

    def _create_sale(self, qty=1.0, price=100.0, discount=0.0):
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'product_uom_qty': qty,
                    'price_unit': price,
                    'discount': discount,
                    'tax_id': [(6, 0, self.tax.ids)],
                }),
            ],
        })

    def _wizard(self, sale):
        return self.env['sale.order.confirm.message'].with_context(
            default_order_id=sale.id).create({})

    def test_confirm_opens_wizard(self):
        sale = self._create_sale()
        action = sale.action_confirm()
        self.assertEqual(action['res_model'], 'sale.order.confirm.message')
        self.assertEqual(action['target'], 'new')
        self.assertEqual(action['context']['default_order_id'], sale.id)
        self.assertEqual(sale.state, 'draft')

    def test_wizard_lines_populated(self):
        sale = self._create_sale(qty=3.0, price=50.0, discount=10.0)
        wizard = self._wizard(sale)
        self.assertEqual(len(wizard.line_ids), 1)
        line = wizard.line_ids
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.product_uom_qty, 3.0)
        self.assertEqual(line.price_unit, 50.0)
        self.assertEqual(line.discount, 10.0)
        self.assertEqual(line.tax_id, self.tax)
        self.assertEqual(line.price_subtotal, sale.order_line.price_subtotal)

    def test_wizard_header_fields(self):
        sale = self._create_sale()
        wizard = self._wizard(sale)
        self.assertEqual(wizard.partner_id, sale.partner_id)
        self.assertEqual(wizard.partner_shipping_id, sale.partner_shipping_id)
        self.assertEqual(wizard.partner_invoice_id, sale.partner_invoice_id)
        self.assertEqual(wizard.payment_term_id, sale.payment_term_id)
        self.assertEqual(wizard.payment_mode_id, sale.payment_mode_id)
        self.assertEqual(wizard.incoterm, sale.incoterm)

    def test_wizard_totals(self):
        sale = self._create_sale()
        wizard = self._wizard(sale)
        self.assertEqual(wizard.amount_untaxed, sale.amount_untaxed)
        self.assertEqual(wizard.amount_tax, sale.amount_tax)
        self.assertEqual(wizard.amount_total, sale.amount_total)
        self.assertEqual(wizard.currency_id, sale.currency_id)

    def test_confirm_requires_check(self):
        sale = self._create_sale()
        wizard = self._wizard(sale)
        self.assertTrue(wizard.require_check)
        with self.assertRaises(UserError):
            wizard.action_confirm_order()
        self.assertEqual(sale.state, 'draft')

    def test_confirm_success(self):
        sale = self._create_sale()
        wizard = self._wizard(sale)
        wizard.checked = True
        wizard.action_confirm_order()
        self.assertEqual(sale.state, 'sale')

    def test_check_not_required(self):
        self.company.sale_confirm_message_require_check = False
        sale = self._create_sale()
        wizard = self._wizard(sale)
        wizard.action_confirm_order()
        self.assertEqual(sale.state, 'sale')

    def test_bypass_context(self):
        sale = self._create_sale()
        result = sale.with_context(
            bypass_sale_confirm_message=True).action_confirm()
        self.assertTrue(result)
        self.assertEqual(sale.state, 'sale')

    def test_company_disabled(self):
        self.company.sale_confirm_message_active = False
        sale = self._create_sale()
        result = sale.action_confirm()
        self.assertTrue(result)
        self.assertEqual(sale.state, 'sale')

    def test_multi_order_raises(self):
        sale_1 = self._create_sale()
        sale_2 = self._create_sale()
        with self.assertRaises(UserError):
            (sale_1 + sale_2).action_confirm()
        self.assertEqual(sale_1.state, 'draft')
        self.assertEqual(sale_2.state, 'draft')

    def test_message_default(self):
        self.assertIn(
            'cannot be modified', self.company.sale_confirm_message_body)

    def test_wizard_lists_locked_fields(self):
        sale = self._create_sale()
        wizard = self._wizard(sale)
        for term in [
                '<li>Customer</li>',
                '<li>Delivery Address</li>',
                '<li>Invoice Address</li>',
                '<li>Payment Terms</li>',
                '<li>Payment Mode</li>',
                '<li>Incoterm</li>',
                '<li>Line data: product, quantity, unit price, taxes, discount '
                'and subtotal</li>',
                '<li>Order totals: untaxed amount, taxes and total</li>']:
            self.assertIn(term, wizard.locked_fields_html)

    def test_wizard_locked_fields_returned_by_onchange(self):
        sale = self._create_sale()
        model = self.env['sale.order.confirm.message'].with_context(
            default_order_id=sale.id)
        view = self.env.ref(
            'sale_order_confirm_message.sale_order_confirm_message_form')
        fvg = model.fields_view_get(view_id=view.id, view_type='form')
        spec = model._onchange_spec(fvg)
        defaults = model.default_get(list(fvg['fields']))
        values = {}
        for name, meta in fvg['fields'].items():
            if name in defaults:
                values[name] = defaults[name]
            elif meta['type'] in ('one2many', 'many2many'):
                values[name] = [(6, 0, [])]
            else:
                values[name] = False
        result = model.onchange(values, list(fvg['fields']), spec)
        self.assertIn(
            '<li>Customer</li>', result['value']['locked_fields_html'])

    def test_default_get_without_order_id_field(self):
        sale = self._create_sale()
        wizard_model = self.env['sale.order.confirm.message'].with_context(
            default_order_id=sale.id)
        defaults = wizard_model.default_get(['line_ids', 'partner_id'])
        self.assertEqual(defaults.get('order_id'), sale.id)
        wizard = wizard_model.new(defaults)
        self.assertEqual(wizard.partner_id, sale.partner_id)
        self.assertEqual(wizard.message, self.company.sale_confirm_message_body)
