###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSale(TransactionCase):

    def setUp(self):
        super().setUp()
        company, unit, area, user = self.create_company('1')
        self.company_1 = company
        self.unit_1 = unit
        self.area_1 = area
        self.user_1 = user
        company, unit, area, user = self.create_company('2')
        self.company_2 = company
        self.unit_2 = unit
        self.area_2 = area
        self.customer = self.env['res.partner'].create({
            'company_id': False,
            'company_type': 'company',
            'customer': True,
            'supplier': False,
            'name': 'Client',
        })

    def create_company(self, key):
        company = self.env['res.company'].create({
            'name': 'Company %s' % key,
        })
        old_company = self.env.user.company_id
        self.env.user.company_id = company.id
        coas = self.env['account.chart.template'].search([])
        coas.try_loading_for_current_company()
        self.env.user.company_id = old_company.id
        user = self.env['res.users'].create({
            'name': 'User %s' % key,
            'login': 'user_%s@test.com' % key,
            'company_ids': [(6, 0, [company.id])],
            'company_id': company.id,
        })
        unit = self.env['product.business.unit'].create({
            'name': 'Business unit %s' % key,
            'company_id': company.id,
        })
        area = self.env['product.business.area'].create({
            'name': 'Unit %s' % key,
            'unit_id': unit.id,
        })
        return company, unit, area, user

    def create_product(self, unit, area, list_price=33.33,
                       name='Service product'):
        return self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'unit_id': unit.id,
            'area_id': area.id,
            'name': name,
            'standard_price': round(list_price / 2),
            'list_price': list_price,
        })

    def create_mapping_journal(self, company, companies):
        journal = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', company.id)], limit=1)
        journals = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', 'in', [c.id for c in companies])])
        journal.intercompany_map_ids = [(6, 0, journals.ids)]

    def test_sale(self):
        product = self.create_product(self.unit_1, self.area_1, 33.33)
        sale = self.env['sale.order'].create({
            'company_id': self.company_1.id,
            'partner_id': self.customer.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': 33.33,
                    'product_uom_qty': 1}),
            ]
        })
        self.assertTrue(sale.name)
        self.assertEquals(len(sale.order_line), 1)
        self.assertEquals(sale.state, 'draft')
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(sale.invoice_count, 0)
        sale.action_invoice_create()
        self.assertEquals(sale.invoice_count, 1)
        self.assertEquals(
            sale.invoice_ids[0].company_id, self.unit_1.company_id)

    def test_sale_two_invoices_without_journal_mapping(self):
        product_1 = self.create_product(self.unit_1, self.area_1, 33.33)
        product_2 = self.create_product(self.unit_2, self.area_2, 33.33)
        sale = self.env['sale.order'].create({
            'company_id': self.company_1.id,
            'partner_id': self.customer.id,
            'order_line': [
                (0, 0, {
                    'product_id': product_1.id,
                    'price_unit': 33.33,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': product_2.id,
                    'price_unit': 33.33,
                    'product_uom_qty': 1}),
            ]
        })
        sale.action_confirm()
        with self.assertRaises(UserError) as user_error:
            sale.action_invoice_create()
        self.assertIn(
            'You must create a mapped for Journal', str(user_error.exception))

    def create_payment_mode(self, company, key):
        method = self.env['account.payment.method'].create({
            'name': 'Method %s' % key,
            'code': 'COD%s' % key,
            'payment_type': 'outbound',
        })
        return self.env['account.payment.mode'].create({
            'company_id': company.id,
            'bank_account_link': 'variable',
            'name': 'Payment mode, company 1',
            'payment_method_id': method.id,
        })

    def test_only_one_company(self):
        payment = self.create_payment_mode(self.env.user.company_id, '1')
        payment_2 = self.create_payment_mode(self.unit_2.company_id, '2')
        payment.intercompany_map_ids = [(6, 0, [payment_2.id])]
        product_2 = self.create_product(self.unit_2, self.area_2, 33.33)
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'payment_mode_id': payment.id,
            'order_line': [
                (0, 0, {
                    'product_id': product_2.id,
                    'price_unit': 33.33,
                    'product_uom_qty': 1}),
            ]
        })
        sale.action_confirm()
        self.create_mapping_journal(sale.company_id, [self.unit_2.company_id])
        sale.action_invoice_create()
        self.assertEquals(sale.invoice_count, 1)
        inv = sale.invoice_ids[0]
        company = inv.mapped('invoice_line_ids.product_id.unit_id.company_id')
        self.assertEquals(company, self.unit_2.company_id)
        self.assertEquals(inv.company_id, company)
        self.assertEquals(inv.account_id.company_id, company)
        self.assertEquals(inv.payment_mode_id.company_id, company)
        self.assertEquals(inv.journal_id.company_id, company)
        for line in inv.move_id.line_ids:
            self.assertEquals(line.company_id, inv.company_id)
            self.assertEquals(line.account_id.company_id, inv.company_id)
            self.assertEquals(line.journal_id.company_id, inv.company_id)
            self.assertEquals(line.tax_line_id.company_id, inv.company_id)

    def test_sale_two_invoices(self):
        product_1 = self.create_product(self.unit_1, self.area_1, 33.33)
        product_2 = self.create_product(self.unit_2, self.area_2, 33.33)
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'order_line': [
                (0, 0, {
                    'product_id': product_1.id,
                    'price_unit': 33.33,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': product_2.id,
                    'price_unit': 33.33,
                    'product_uom_qty': 1}),
            ]
        })
        sale.action_confirm()
        self.create_mapping_journal(
            sale.company_id, [self.unit_1.company_id, self.unit_2.company_id])
        sale.action_invoice_create()
        self.assertEquals(sale.invoice_count, 2)
        for inv in sale.invoice_ids:
            company = inv.mapped(
                'invoice_line_ids.product_id.unit_id.company_id')
            self.assertEquals(inv.company_id, company)
            self.assertEquals(inv.journal_id.company_id, company)
            for line in inv.move_id.line_ids:
                self.assertEquals(line.company_id, inv.company_id)
                self.assertEquals(line.account_id.company_id, inv.company_id)
                self.assertEquals(line.journal_id.company_id, inv.company_id)
                self.assertEquals(line.tax_line_id.company_id, inv.company_id)

    def test_sale_two_invoices_with_notes(self):
        product_1 = self.create_product(self.unit_1, self.area_1, name='P1')
        product_2 = self.create_product(self.unit_2, self.area_2, name='P2')
        sale = self.env['sale.order'].create({
            'company_id': self.unit_1.company_id.id,
            'partner_id': self.customer.id,
            'order_line': [
                (0, 0, {
                    'display_type': 'line_section',
                    'name': 'Section1'}),
                (0, 0, {
                    'display_type': 'line_note',
                    'name': 'Note1'}),
                (0, 0, {
                    'product_id': product_1.id,
                    'price_unit': 33.33,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'display_type': 'line_section',
                    'name': 'Section2'}),
                (0, 0, {
                    'display_type': 'line_note',
                    'name': 'Note2'}),
                (0, 0, {
                    'product_id': product_2.id,
                    'price_unit': 33.33,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'display_type': 'line_section',
                    'name': 'Section22'}),
            ]
        })
        sale.action_confirm()
        self.create_mapping_journal(
            self.unit_1.company_id, [self.unit_2.company_id])
        sale.action_invoice_create()
        self.assertEquals(sale.invoice_count, 2)
        lines = sale.invoice_ids.mapped('invoice_line_ids').filtered(
            lambda l: '1' in l.name)
        self.assertEquals(len(lines), 2)
        for line in lines:
            self.assertEquals(
                line.invoice_id.company_id, self.unit_1.company_id)
        lines = sale.invoice_ids.mapped('invoice_line_ids').filtered(
            lambda l: '2' in l.name)
        self.assertEquals(len(lines), 2)
        for line in lines:
            self.assertEquals(
                line.invoice_id.company_id, self.unit_2.company_id)

    def test_raise_need_journal_mapped(self):
        product_1 = self.create_product(self.unit_1, self.area_1, name='P1')
        product_2 = self.create_product(self.unit_2, self.area_2, name='P2')
        sale = self.env['sale.order'].create({
            'company_id': self.unit_1.company_id.id,
            'partner_id': self.customer.id,
            'order_line': [
                (0, 0, {
                    'product_id': product_1.id,
                    'price_unit': 33.33,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': product_2.id,
                    'price_unit': 33.33,
                    'product_uom_qty': 1}),
            ]
        })
        sale.action_confirm()
        with self.assertRaises(UserError):
            sale.action_invoice_create()

    def test_more_than_one_sale(self):
        product_1 = self.create_product(self.unit_1, self.area_1, name='P1')
        product_2 = self.create_product(self.unit_2, self.area_2, name='P2')
        sales = self.env['sale.order']
        sale1 = sales.create({
            'company_id': self.unit_1.company_id.id,
            'partner_id': self.customer.id,
            'order_line': [
                (0, 0, {
                    'display_type': 'line_section',
                    'name': 'Section1a'}),
                (0, 0, {
                    'display_type': 'line_note',
                    'name': 'Note1a'}),
                (0, 0, {
                    'product_id': product_1.id,
                    'price_unit': 33.33,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'display_type': 'line_section',
                    'name': 'Section2a'}),
                (0, 0, {
                    'display_type': 'line_note',
                    'name': 'Note2a'}),
                (0, 0, {
                    'product_id': product_2.id,
                    'price_unit': 33.33,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'display_type': 'line_section',
                    'name': 'Section22a'}),
            ]
        })
        sale1.action_confirm()
        sales |= sale1
        sale2 = sales.create({
            'company_id': self.unit_2.company_id.id,
            'partner_id': self.customer.id,
            'order_line': [
                (0, 0, {
                    'display_type': 'line_section',
                    'name': 'Section1b'}),
                (0, 0, {
                    'display_type': 'line_note',
                    'name': 'Note1b'}),
                (0, 0, {
                    'product_id': product_1.id,
                    'price_unit': 33.33,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'display_type': 'line_section',
                    'name': 'Section2b'}),
                (0, 0, {
                    'display_type': 'line_note',
                    'name': 'Note2b'}),
                (0, 0, {
                    'product_id': product_2.id,
                    'price_unit': 33.33,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'display_type': 'line_section',
                    'name': 'Section22b'}),
            ]
        })
        sale2.action_confirm()
        sales |= sale2
        self.create_mapping_journal(
            self.unit_1.company_id, [self.unit_2.company_id])
        self.create_mapping_journal(
            self.unit_2.company_id, [self.unit_1.company_id])
        sales.action_invoice_create()
        for sale in sales:
            self.assertEquals(sale.invoice_count, 2)
            lines = sale.invoice_ids.mapped('invoice_line_ids').filtered(
                lambda l: '1' in l.name)
            self.assertEquals(len(lines), 4)
            for line in lines:
                self.assertEquals(
                    line.invoice_id.company_id, self.unit_1.company_id)
            lines = sale.invoice_ids.mapped('invoice_line_ids').filtered(
                lambda l: '2' in l.name)
            self.assertEquals(len(lines), 4)
            for line in lines:
                self.assertEquals(
                    line.invoice_id.company_id, self.unit_2.company_id)
        wizard = self.env['account.invoice.confirm'].with_context({
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'account.invoice',
            'active_ids': sales.mapped('invoice_ids').ids,
            'active_id': 0}).create({})
        wizard.invoice_confirm()
