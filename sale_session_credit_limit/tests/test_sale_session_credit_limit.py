###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestSaleSessionCreditLimit(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.credit_limit = 100
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
            'risk_sale_order_include': True,
            'credit_limit': self.credit_limit,
        })
        invoice_journal = self.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1)
        user_type = self.env.ref('account.data_account_type_liquidity')
        mismatch_account = self.env['account.account'].create({
            'code': '79999',
            'name': 'Mismatch account for test close session',
            'user_type_id': user_type.id,
        })
        account_bank = self.env['account.account'].create({
            'code': '110401',
            'user_type_id': self.ref('account.data_account_type_liquidity'),
            'name': 'Bank test account',
        })
        self.bank_journal = self.env['account.journal'].create({
            'code': 'BNK',
            'name': 'Bank journal test',
            'type': 'bank',
            'default_debit_account_id': account_bank.id,
            'default_credit_account_id': account_bank.id,
        })
        account_cash = self.env['account.account'].create({
            'code': '110402',
            'user_type_id': self.ref('account.data_account_type_liquidity'),
            'name': 'Bank test account',
        })
        self.cash_journal = self.env['account.journal'].create({
            'code': 'CASH',
            'name': 'Cash journal test',
            'type': 'cash',
            'default_debit_account_id': account_cash.id,
            'default_credit_account_id': account_cash.id,
            'update_posted': True,
        })
        self.team = self.env['crm.team'].create({
            'name': 'Test Sale Team',
            'invoice_journal_ids': [(6, 0, [invoice_journal.id])],
            'payment_journal_ids': [
                (6, 0, [self.cash_journal.id, self.bank_journal.id])],
            'cash_payment_journal_id': self.cash_journal.id,
            'require_sale_session': True,
            'mismatch_account': mismatch_account.id,
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.stock_inventory_adjust(self.product, 1000)

    def stock_inventory_adjust(self, product, qty, lot=None):
        location = self.env.ref('stock.stock_location_stock')
        inventory = self.env['stock.inventory'].create({
            'name': 'Add products for tests',
            'filter': 'partial',
            'location_id': location.id,
            'exhausted': True,
        })
        inventory.action_start()
        inventory.line_ids.create({
            'inventory_id': inventory.id,
            'product_id': product.id,
            'product_qty': qty,
            'location_id': location.id,
            'prod_lot_id': lot.id if lot else False,
        })
        inventory._action_done()
        return inventory

    def test_confirm_sale_with_session_financial_risk_exceeded(self):
        self.assertEqual(self.partner.credit_limit, self.credit_limit)
        self.assertTrue(self.partner.risk_sale_order_include)
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        self.assertFalse(session.previous_id)
        session.action_open()
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'session_id': session.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 110,
                    'product_uom_qty': 1,
                    'tax_id': [(6, 0, [])],
                }),
            ]
        })
        wizard = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': sale.id,
            'journal_id': self.cash_journal.id,
            'amount': 150,
        })
        self.assertEquals(wizard.amount_change, 40)
        self.assertEquals(sale.state, 'draft')
        wizard.action_pay()
        self.assertEquals(sale.state, 'sale')

    def test_confirm_sale_with_session_financial_risk_credit_exceeded(self):
        self.assertEqual(self.partner.credit_limit, self.credit_limit)
        self.assertTrue(self.partner.risk_sale_order_include)
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        self.assertFalse(session.previous_id)
        session.action_open()
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'session_id': session.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 110,
                    'product_uom_qty': 1,
                    'tax_id': [(6, 0, [])],
                }),
            ]
        })
        wizard = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': sale.id,
            'journal_id': self.cash_journal.id,
            'amount': 150,
        })
        self.assertEquals(wizard.amount_change, 40)
        self.assertEquals(sale.state, 'draft')
        res = wizard.action_credit()
        self.assertEquals(res['type'], 'ir.actions.act_window')
        self.assertEquals(res['res_model'], 'partner.risk.exceeded.wiz')
        self.assertEquals(sale.state, 'draft')

    def test_confirm_sale_with_session_financial_risk_ok(self):
        self.assertEquals(self.partner.credit_limit, self.credit_limit)
        self.assertTrue(self.partner.risk_sale_order_include)
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'session_id': session.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 80,
                    'product_uom_qty': 1,
                    'tax_id': [(6, 0, [])],
                }),
            ]
        })
        wizard = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': sale.id,
            'journal_id': self.cash_journal.id,
            'amount': 80,
        })
        self.assertFalse(wizard.risk_exception)
        self.assertEquals(wizard.amount_change, 0)
        self.assertEquals(sale.state, 'draft')
        wizard.action_pay()
        self.assertEquals(sale.state, 'sale')

    def test_confirm_sale_with_session_financial_risk_credit_ok(self):
        self.assertEqual(self.partner.credit_limit, self.credit_limit)
        self.assertTrue(self.partner.risk_sale_order_include)
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        self.assertFalse(session.previous_id)
        session.action_open()
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'session_id': session.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 70,
                    'product_uom_qty': 1,
                    'tax_id': [(6, 0, [])],
                }),
            ]
        })
        wizard = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': sale.id,
            'journal_id': self.cash_journal.id,
            'amount': 100,
        })
        self.assertFalse(wizard.risk_exception)
        self.assertEquals(wizard.amount_change, 30)
        self.assertEquals(sale.state, 'draft')
        wizard.action_credit()
        self.assertEquals(sale.state, 'sale')

    def test_confirm_sale_session_risk_ok_wizard_confirm(self):
        self.assertEquals(self.partner.credit_limit, self.credit_limit)
        self.assertTrue(self.partner.risk_sale_order_include)
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        self.assertFalse(session.previous_id)
        session.action_open()
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'session_id': session.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 80,
                    'product_uom_qty': 1,
                    'tax_id': [(6, 0, [])],
                }),
            ],
        })
        wizard = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': sale.id,
            'journal_id': self.cash_journal.id,
            'amount': 80,
        })
        self.assertFalse(wizard.risk_exception)
        self.assertEquals(wizard.amount_change, 0)
        self.assertEquals(sale.state, 'draft')
        wizard.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        self.assertEquals(len(sale.invoice_ids), 0)

    def test_confirm_sale_session_risk_exceeded_wizard_confirm(self):
        self.assertEquals(self.partner.credit_limit, self.credit_limit)
        self.assertTrue(self.partner.risk_sale_order_include)
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        self.assertFalse(session.previous_id)
        session.action_open()
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'session_id': session.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 110,
                    'product_uom_qty': 1,
                    'tax_id': [(6, 0, [])],
                }),
            ],
        })
        wizard = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': sale.id,
            'journal_id': self.cash_journal.id,
            'amount': 150,
        })
        self.assertEquals(wizard.amount_change, 40)
        self.assertEquals(sale.state, 'draft')
        wizard.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        self.assertEqual(len(sale.invoice_ids), 0)

    def test_confirm_sale_manual_with_financial_risk_ok(self):
        self.assertEquals(self.partner.credit_limit, self.credit_limit)
        self.assertTrue(self.partner.risk_sale_order_include)
        self.assertTrue(self.team.require_sale_session)
        self.team.require_sale_session = False
        self.assertFalse(self.team.require_sale_session)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 80,
                    'product_uom_qty': 1,
                    'tax_id': [(6, 0, [])],
                }),
            ],
        })
        self.assertEquals(sale.state, 'draft')
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')

    def test_confirm_sale_manual_with_financial_risk_exceeded(self):
        self.assertEquals(self.partner.credit_limit, self.credit_limit)
        self.assertTrue(self.partner.risk_sale_order_include)
        self.assertTrue(self.team.require_sale_session)
        self.team.require_sale_session = False
        self.assertFalse(self.team.require_sale_session)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 150,
                    'product_uom_qty': 1,
                    'tax_id': [(6, 0, [])],
                })
            ],
        })
        self.assertEquals(sale.state, 'draft')
        res = sale.action_confirm()
        self.assertEquals(res['type'], 'ir.actions.act_window')
        self.assertEquals(res['res_model'], 'partner.risk.exceeded.wiz')
        self.assertEquals(sale.state, 'draft')
