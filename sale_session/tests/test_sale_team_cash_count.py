###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import SavepointCase

_log = logging.getLogger(__name__)


class TestSaleTeamCashCount(SavepointCase):

    def setUp(self):
        super().setUp()
        users_obj = self.env['res.users'].with_context(no_reset_password=True)
        self.user_company1 = users_obj.create({
            'name': 'Test User company 1',
            'login': 'user_company1',
            'email': 'testcompany1@test.com',
            'company_ids': [(6, 0, [self.env.ref('base.main_company').id])],
            'company_id': self.env.ref('base.main_company').id,
            'groups_id': [(6, 0, [
                self.env.ref('account.group_account_manager').id,
                self.env.ref('sales_team.group_sale_manager').id,
            ])],
        })
        self.company_2 = self.env['res.company'].create({
            'name': 'Company 2',
        })
        self.user_company2 = users_obj.create({
            'name': 'Test User company 2',
            'login': 'user_company2',
            'email': 'testcompany2@test.com',
            'company_ids': [(6, 0, [self.company_2.id])],
            'company_id': self.company_2.id,
            'groups_id': [(6, 0, [
                self.env.ref('account.group_account_manager').id,
                self.env.ref('sales_team.group_sale_manager').id,
            ])],
        })
        templates = self.env['account.chart.template'].search([], limit=1)
        if not templates:
            _log.warning(
                'Test skipped because there is no chart of account defined '
                'new company')
            self.skipTest('No Chart of account found')
            return
        if not templates.existing_accounting(self.env.user.company_id):
            templates.try_loading_for_current_company()
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.stock_inventory_adjust(self.product, 1000)
        self.service_product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Test service product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
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
        invoice_journal = self.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1)
        user_type = self.env.ref('account.data_account_type_liquidity')
        mismatch_account = self.env['account.account'].create({
            'code': '79999',
            'name': 'Mismatch account for test close session',
            'user_type_id': user_type.id,
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
        self.team_company2 = self.env['crm.team'].create({
            'name': 'Test Sale Team company 2',
            'require_sale_session': True,
            'company_id': self.company_2.id,
        })

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

    def test_crm_team(self):
        with self.assertRaises(ValidationError):
            self.env['crm.team'].create({
                'name': 'Test Sale Team',
                'require_sale_session': True,
                'cash_money_values': 'a,'
            })
        self.env['crm.team'].create({
            'name': 'Test Sale Team',
            'require_sale_session': True,
            'cash_money_values': '1,'
        })
        self.env['crm.team'].create({
            'name': 'Test Sale Team',
            'require_sale_session': True,
            'cash_money_values': False
        })
        team = self.env['crm.team'].create({
            'name': 'Test Sale Team',
            'require_sale_session': True,
            'cash_money_values': '1,2,3,'
        })
        self.assertEquals(round(sum(team.get_cash_money_values()), 2), 6)
        team.cash_money_values = '0.1,0.2,0.3'
        self.assertEquals(round(sum(team.get_cash_money_values()), 2), 0.6)

    def test_sale_session_multicompany(self):
        self.env(user=self.user_company2)['sale.session'].create({
            'team_id': self.team_company2.id
        })
        self.assertFalse(
            self.env(user=self.user_company1)['sale.session'].search([]))

    def test_sale_session(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        self.assertTrue(session.name)
        self.assertIn('SS', session.name)
        self.assertEquals(session.open_date.date(), fields.Date.today())
        self.assertEquals(session.close_date, False)
        self.assertEquals(session.validation_date, False)
        self.assertFalse(session.get_current_sale_session(self.team.id))
        journal = self.team.cash_payment_journal_id
        self.team.cash_payment_journal_id = False
        with self.assertRaises(UserError):
            session.action_open()
        self.team.cash_payment_journal_id = journal
        session.action_open()
        self.assertEquals(session.state, 'open')
        self.assertEquals(
            session.get_current_sale_session(self.team.id), session)
        journal = self.team.cash_payment_journal_id
        self.team.cash_payment_journal_id = False
        session.state = 'draft'
        with self.assertRaises(UserError):
            session.action_open()
        self.team.cash_payment_journal_id = journal
        session.action_open()
        new_session = session.copy()
        self.assertEquals(new_session.state, 'draft')
        with self.assertRaises(ValidationError):
            new_session.action_open()

    def _create_sale(self, session, payment_type=None):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'session_id': session and session.id or False,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'tax_id': [(6, 0, [])],
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })
        journals = {
            'cash': self.cash_journal,
            'bank': self.bank_journal,
        }
        if payment_type in journals:
            sale.session_pay(sale.amount_total, journals[payment_type])
        return sale

    def test_session_previous(self):
        def close_session(session):
            wizard = self.env['sale.session.close'].create({
                'session_id': session.id,
            })
            wizard.action_confirm()

        session_1 = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        self.assertFalse(session_1.previous_id)
        session_1.action_open()
        self.assertFalse(session_1.previous_id)
        session_2 = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        self.assertEquals(session_2.previous_id, session_1)
        close_session(session_1)
        session_2.action_open()
        self.assertEquals(session_2.previous_id, session_1)
        session_3 = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        self.assertEquals(session_3.previous_id, session_2)
        session_4 = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        self.assertEquals(session_4.previous_id, session_2)
        close_session(session_2)
        session_4.action_open()
        self.assertEquals(session_4.previous_id, session_2)
        self.assertEquals(session_3.previous_id, session_2)
        close_session(session_4)
        session_3.action_open()
        self.assertEquals(session_3.previous_id, session_4)

    def test_create_seale_with_session_draft(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        self.assertFalse(session.previous_id)
        with self.assertRaises(UserError):
            self._create_sale(session, 'bank')
        session.action_open()
        self.assertFalse(session.previous_id)
        self._create_sale(session, 'bank')
        new_session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        with self.assertRaises(ValidationError):
            new_session.action_open()
        self.assertFalse(session.previous_id)
        action = session.action_close()
        self.assertFalse(session.previous_id)
        wizard = self.env['sale.session.close'].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEquals(session.state, 'close')
        with self.assertRaises(UserError):
            self._create_sale(session, 'bank')

    def test_session_sale_pay_cash(self):
        with self.assertRaises(UserError):
            self._create_sale(False)
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        session.action_open()
        self.assertEquals(self.team.get_actual_total_cash(), 0)
        sale = self._create_sale(session, 'cash')
        self.assertEquals(self.team.get_actual_total_cash(), 100)
        self.assertEquals(session.total_payment_cash, sale.amount_total)
        self.assertEquals(session.total_payment_bank, 0)
        self.assertEquals(session.total_payment, sale.amount_total)

    def test_session_sale_pay_bank(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        session.action_open()
        self.assertEquals(self.team.get_actual_total_cash(), 0)
        sale = self._create_sale(session, 'bank')
        self.assertEquals(self.team.get_actual_total_cash(), 0)
        self.assertEquals(session.total_payment_cash, 0)
        self.assertEquals(session.total_payment_bank, sale.amount_total)
        self.assertEquals(session.total_payment, sale.amount_total)

    def test_session_sale_credit(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        session.action_open()
        sale = self._create_sale(session)
        sale.action_confirm()
        self.assertEquals(self.team.get_actual_total_cash(), 0)
        self.assertEquals(session.total_payment_cash, 0)
        self.assertEquals(session.total_payment_bank, 0)
        self.assertEquals(session.total_payment, 0)

    def test_session_close_with_sales(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        session.action_open()
        self._create_sale(session, 'cash')
        self._create_sale(session, 'bank')
        self._create_sale(session, 'credit')
        self.assertEquals(self.team.get_actual_total_cash(), 100)
        self.assertEquals(session.total_payment_cash, 100)
        self.assertEquals(session.total_payment_bank, 100)
        self.assertEquals(session.total_payment, 200)
        wizard = self.env['sale.session.close'].create({
            'session_id': session.id,
        })
        self.assertEquals(wizard.total_payment_cash, 100)
        wizard.action_confirm()
        self.assertEquals(session.state, 'close')
        self.assertEquals(session.close_date.date(), fields.Date.today())
        self.assertEquals(session.balance_end, 200)
        self.assertEquals(self.team.get_actual_total_cash(), 100)
        self.assertEquals(session.balance_diff, 200)

    def test_session_close_and_new_with_sales_and_send(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        session.action_open()
        self.assertEquals(self.team.get_actual_total_cash(), 0)
        self._create_sale(session, 'cash')
        self._create_sale(session, 'bank')
        self._create_sale(session, 'credit')
        self.assertEquals(session.total_payment_cash, 100)
        self.assertEquals(session.total_payment_bank, 100)
        self.assertEquals(session.total_payment, 200)
        self.assertEquals(self.team.get_actual_total_cash(), 100)
        wizard = self.env['sale.session.close'].create({
            'session_id': session.id,
            'amount_send': 20,
        })
        self.assertEquals(wizard.total_payment_cash, 100)
        wizard.action_confirm()
        self.assertEquals(session.state, 'close')
        self.assertEquals(session.close_date.date(), fields.Date.today())
        self.assertEquals(session.balance_end, 200)
        self.assertEquals(session.balance_diff, 200)
        internal_payment = self.env['account.payment'].create({
            'payment_type': 'transfer',
            'amount': 20,
            'journal_id': self.cash_journal.id,
            'destination_journal_id': self.bank_journal.id,
            'payment_method_id': self.env.ref(
                'account.account_payment_method_manual_in').id,
        })
        internal_payment.post()
        new_session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        new_session.action_open()
        self.assertEquals(self.team.get_actual_total_cash(), 80)
        self._create_sale(new_session, 'cash')
        self._create_sale(new_session, 'bank')
        self._create_sale(new_session, 'credit')
        self.assertEquals(new_session.total_payment_cash, 100)
        self.assertEquals(new_session.total_payment_bank, 100)
        self.assertEquals(self.team.get_actual_total_cash(), 180)
        self.assertEquals(new_session.total_payment, 200)
        self.assertEquals(self.team.get_actual_total_cash(), 180)

    def test_session_payment(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        self.assertEquals(self.team.get_actual_total_cash(), 0)
        journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        self.assertTrue(journal)
        payment = session.register_payment(self.partner, journal, 100)
        self.assertEquals(payment.state, 'posted')
        self.assertEquals(payment.partner_id, self.partner)
        self.assertEquals(len(session.payment_ids), 1)
        self.assertEquals(sum(session.payment_ids.mapped('amount_signed')), 100)
        self.assertEquals(self.team.get_actual_total_cash(), 100)
        self.assertEquals(session.balance_end, 100)
        wizard = self.env['sale.session.payment'].create({
            'session_id': session.id,
            'partner_id': self.partner.id,
            'journal_id': journal.id,
            'amount': 50,
        })
        wizard.action_confirm()
        self.assertEquals(len(session.payment_ids), 2)
        self.assertEquals(sum(session.payment_ids.mapped('amount_signed')), 150)
        self.assertEquals(self.team.get_actual_total_cash(), 150)
        self.assertEquals(session.balance_end, 150)
        payment_method = self.env['account.payment.method'].search([
            ('payment_type', '=', 'outbound'),
        ], limit=1)
        self.assertTrue(payment_method)
        payment = self.env['account.payment'].create({
            'payment_method_id': payment_method.id,
            'journal_id': journal.id,
            'partner_id': self.partner.id,
            'partner_type': 'customer',
            'payment_type': 'outbound',
            'sale_session_id': session.id,
            'amount': 50,
        })
        self.assertEquals(payment.payment_type, 'outbound')
        payment.post()
        self.assertEquals(sum(session.payment_ids.mapped('amount_signed')), 100)

    def test_session_expense(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        self.assertEquals(self.team.get_actual_total_cash(), 0)
        journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        self.assertTrue(journal)
        payment = session.register_payment(self.partner, journal, 100)
        self.assertEquals(payment.state, 'posted')
        self.assertEquals(payment.partner_id, self.partner)
        self.assertEquals(len(session.payment_ids), 1)
        self.assertEquals(sum(session.payment_ids.mapped('amount_signed')), 100)
        self.assertEquals(self.team.get_actual_total_cash(), 100)
        self.assertEquals(session.balance_end, 100)
        wizard = self.env['sale.session.payment'].create({
            'session_id': session.id,
            'journal_id': journal.id,
            'amount': 80,
            'payment_type': 'outbound',
            'communication': 'Test expense',
        })
        wizard.action_confirm()
        self.assertEquals(len(session.payment_ids), 2)
        self.assertEquals(sum(session.payment_ids.mapped('amount_signed')), 20)
        self.assertEquals(self.team.get_actual_total_cash(), 20)

    def test_session_close(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        session.action_open()
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'session_id': session.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })
        bank_journal = self.env['account.journal'].search(
            [('type', '=', 'bank')], limit=1)
        wizard = self.env['sale.order.payment'].create({
            'sale_id': sale.id,
            'journal_id': bank_journal.id,
            'amount': sale.amount_total,
        })
        wizard.action_confirm()
        self.assertEquals(session.balance_end, sale.amount_total)
        cash_journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        wizard = self.env['sale.session.payment'].create({
            'session_id': session.id,
            'partner_id': self.partner.id,
            'journal_id': cash_journal.id,
            'amount': 50,
        })
        wizard.action_confirm()
        wizard = self.env['sale.session.payment'].create({
            'session_id': session.id,
            'partner_id': self.partner.id,
            'journal_id': cash_journal.id,
            'amount': 50,
        })
        wizard.action_confirm()
        self.assertEquals(
            session.balance_end, sale.amount_total + 100)
        wizard = self.env['sale.session.close'].create({
            'session_id': session.id,
        })
        wizard.action_confirm()
        self.assertIsNot(session.close_date, False)
        self.assertIs(session.validation_date, False)
        self.assertEquals(len(wizard.journal_line_ids), 2)
        bank_line = wizard.journal_line_ids.filtered(
            lambda bl: bl.journal_id == bank_journal)
        self.assertEquals(bank_line.amount_total, sale.amount_total)

    def test_session_open_and_close_cash_count(self):
        self.team.cash_money_values = (
            '0.01,0.05,0.10,0.20,0.50,1,2,5,10,20,50,100,200,500')
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        cash_payment_journal = session.team_id.cash_payment_journal_id
        self.assertEquals(
            cash_payment_journal.default_debit_account_id.opening_debit, 0)
        self.assertEquals(
            cash_payment_journal.default_debit_account_id.opening_credit, 0)
        wizard = self.env['sale.session.wizard_cash_count'].create({
            'session_id': session.id,
            'type': 'open',
        })
        self.assertEquals(wizard.team_id, session.team_id)
        cash_count_ids = wizard.journal_cash_count_ids
        self.assertEquals(len(cash_count_ids), 1)
        self.assertEquals(len(cash_count_ids.line_ids), 14)
        line = cash_count_ids.line_ids[0]
        line.quantity = 3
        self.assertEquals(cash_count_ids.amount_total, 0.03)
        wizard.action_confirm()
        open_cash_counts = session.open_cash_count_ids
        self.assertEquals(len(open_cash_counts), 1)
        self.assertEquals(len(open_cash_counts.cash_count_line_ids), 14)
        self.assertEquals(len(session.close_cash_count_ids), 0)
        self.assertEquals(session.open_cash_count_total, 0.03)
        self.assertEquals(session.close_cash_count_total, 0)
        self.assertEquals(session.balance_start, 0.00)
        self.assertEquals(session.cash_count_start, 0.03)
        self.assertEquals(
            cash_payment_journal.default_debit_account_id.opening_credit, 0)
        mismatch_open_move_lines = session.mismatch_open_move_ids.line_ids
        mismtch_acc_move_line = mismatch_open_move_lines.filtered(
            lambda ln: ln.account_id.id == session.team_id.mismatch_account.id)
        self.assertEquals(mismtch_acc_move_line.credit, 0.03)
        self.assertEquals(mismtch_acc_move_line.debit, 0.00)
        cash_acc_move_line = session.mismatch_open_move_ids.line_ids.filtered(
            lambda ln: ln.account_id.id != session.team_id.mismatch_account.id)
        self.assertEquals(cash_acc_move_line.credit, 0.00)
        self.assertEquals(cash_acc_move_line.debit, 0.03)
        self.assertEquals(session.open_cash_count_mismatch, 0.03)
        action = session.action_close()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEquals(session.mismatch_open_move_ids.state, 'draft')
        action = session.action_validate()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEquals(session.mismatch_open_move_ids.state, 'posted')
        wizard = self.env['sale.session.wizard_cash_count'].create({
            'session_id': session.id,
            'type': 'close',
        })
        self.assertEquals(wizard.team_id, session.team_id)
        cash_count_ids = wizard.journal_cash_count_ids
        self.assertEquals(len(cash_count_ids), 1)
        self.assertEquals(len(cash_count_ids.line_ids), 14)
        line = cash_count_ids.line_ids[0]
        line.quantity = 3
        self.assertEquals(wizard.journal_cash_count_ids.amount_total, 0.03)
        wizard.action_confirm()
        self.assertEquals(session.close_cash_count_total, 0.03)
        self.assertFalse(session.mismatch_close_move_ids)

    def test_session_open_and_close_cash_count_mismatch(self):
        self.team.cash_money_values = (
            '0.01,0.05,0.10,0.20,0.50,1,2,5,10,20,50,100,200,500')
        self.team.cash_count_type = 'open-close'
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        cash_payment_journal = session.team_id.cash_payment_journal_id
        self.assertEquals(
            cash_payment_journal.default_debit_account_id.opening_debit, 0)
        self.assertEquals(
            cash_payment_journal.default_debit_account_id.opening_credit, 0)
        wizard = self.env['sale.session.wizard_cash_count'].create({
            'session_id': session.id,
            'type': 'open',
        })
        self.assertEquals(wizard.team_id, session.team_id)
        cash_count_ids = wizard.journal_cash_count_ids
        self.assertEquals(len(cash_count_ids), 1)
        self.assertEquals(len(cash_count_ids.line_ids), 14)
        line = cash_count_ids.line_ids[0]
        line.quantity = 3
        self.assertEquals(wizard.journal_cash_count_ids.amount_total, 0.03)
        wizard.action_confirm()
        open_cash_counts = session.open_cash_count_ids
        self.assertEquals(len(open_cash_counts), 1)
        self.assertEquals(len(open_cash_counts.cash_count_line_ids), 14)
        self.assertEquals(len(session.close_cash_count_ids), 0)
        self.assertEquals(session.open_cash_count_total, 0.03)
        self.assertEquals(session.close_cash_count_total, 0)
        self.assertEquals(session.balance_start, 0.00)
        self.assertEquals(session.cash_count_start, 0.03)
        self.assertEquals(
            cash_payment_journal.default_debit_account_id.opening_credit, 0)
        mismatch_open_move_lines = session.mismatch_open_move_ids.line_ids
        mismtch_acc_move_line = mismatch_open_move_lines.filtered(
            lambda ln: ln.account_id.id == session.team_id.mismatch_account.id)
        self.assertEquals(mismtch_acc_move_line.credit, 0.03)
        self.assertEquals(mismtch_acc_move_line.debit, 0.00)
        cash_acc_move_line = session.mismatch_open_move_ids.line_ids.filtered(
            lambda ln: ln.account_id.id != session.team_id.mismatch_account.id)
        self.assertEquals(cash_acc_move_line.credit, 0.00)
        self.assertEquals(cash_acc_move_line.debit, 0.03)
        self.assertEquals(session.open_cash_count_mismatch, 0.03)
        action = session.action_close()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEquals(session.mismatch_open_move_ids.state, 'draft')
        action = session.action_validate()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        self.assertEquals(session.mismatch_open_move_ids.state, 'draft')
        wizard.action_confirm()
        self.assertEquals(session.mismatch_open_move_ids.state, 'posted')

    def test_session_close_wizard_without_open_session(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        session.register_payment(self.partner, journal, 100)
        wizard_obj = self.env['sale.session.close']
        wizard = wizard_obj.create({
            'session_id': session.id,
        })
        self.assertEquals(wizard.team_id, session.team_id)
        self.assertEquals(len(wizard.journal_line_ids), 1)
        self.assertEquals(wizard.journal_line_ids.amount_total, 100)
        self.assertEquals(self.team.get_actual_total_cash(), 100)
        session.team_id.cash_min_for_open_session = 10
        wizard = wizard_obj.create({
            'session_id': session.id,
        })
        self.assertEquals(session.team_id.cash_min_for_open_session, 10)
        self.assertEquals(session.total_payment_cash, 100)
        self.assertEquals(session.amount_send, 0)
        self.assertEquals(wizard.amount_send, 90)
        self.assertEquals(self.team.get_actual_total_cash(), 100)
        wizard.amount_send = 1000
        with self.assertRaises(ValidationError):
            wizard.action_confirm()
        wizard.amount_send = 30
        wizard.action_confirm()
        self.assertEquals(session.close_date.date(), fields.Date.today())
        self.assertEquals(session.amount_send, 30)
        self.assertEquals(self.team.get_actual_total_cash(), 100)

    def test_session_close_and_validate(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        session.register_payment(self.partner, journal, 100)
        self._create_sale(session, payment_type='cash')
        self._create_sale(session, payment_type='bank')
        self._create_sale(session, payment_type='bank')
        self._create_sale(session, payment_type='credit')
        wizard = self.env['sale.session.close'].create({
            'session_id': session.id,
        })
        self.assertEquals(wizard.team_id, session.team_id)
        self.assertEquals(len(wizard.journal_line_ids), 2)
        self.assertEquals(wizard.journal_line_ids[0].amount_total, 200)
        self.assertEquals(wizard.journal_line_ids[1].amount_total, 200)
        self.assertEquals(self.team.get_actual_total_cash(), 200)
        session.team_id.cash_min_for_open_session = 10
        wizard = self.env['sale.session.close'].create({
            'session_id': session.id,
        })
        self.assertEquals(session.team_id.cash_min_for_open_session, 10)
        self.assertEquals(session.total_payment_cash, 200)
        self.assertEquals(session.amount_send, 0)
        self.assertEquals(wizard.amount_send, 190)
        self.assertEquals(self.team.get_actual_total_cash(), 200)
        wizard.amount_send = 1000
        with self.assertRaises(ValidationError):
            wizard.action_confirm()
        wizard.amount_send = 30
        wizard.action_confirm()
        self.assertEquals(session.close_date.date(), fields.Date.today())
        self.assertEquals(session.amount_send, 30)
        self.assertEquals(self.team.get_actual_total_cash(), 200)
        validate_wizard = self.env['sale.session.validate'].create({
            'session_id': session.id,
            'amount_send': session.amount_send,
        })
        with self.assertRaises(ValidationError):
            validate_wizard.action_confirm()
        validate_wizard.journal_id = self.bank_journal.id
        validate_wizard.action_confirm()
        self.assertEquals(session.validation_date.date(), fields.Date.today())
        self.assertTrue(session.validate_move_id)
        self.assertEquals(session.validate_move_id.state, 'posted')
        move = session.validate_move_id
        self.assertEquals(
            move.line_ids[0].partner_id, session.company_id.partner_id)
        debit_account = self.bank_journal.default_debit_account_id
        debit_line = move.line_ids.filtered(
            lambda ln: ln.account_id == debit_account)
        self.assertEquals(debit_line.debit, 30)
        self.assertEquals(debit_line.credit, 0)
        self.assertIn(session.name, debit_line.name)
        credit_line = move.line_ids.filtered(
            lambda ln: ln.account_id != debit_account)
        self.assertEquals(credit_line.debit, 0)
        self.assertEquals(credit_line.credit, 30)
        with self.assertRaises(UserError):
            session.action_revert_to_close()
        self.bank_journal.update_posted = True
        session.action_revert_to_close()
        self.assertFalse(session.validate_move_id)
        self.assertFalse(session.validation_date)
        self.assertEquals(session.state, 'close')
        session2 = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session2.action_open()
        with self.assertRaises(ValidationError):
            session.action_revert_to_open()

    def test_session_close_and_validate_editing_amount_to_send(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        session.register_payment(self.partner, journal, 100)
        self._create_sale(session, payment_type='cash')
        self._create_sale(session, payment_type='bank')
        self._create_sale(session, payment_type='bank')
        self._create_sale(session, payment_type='credit')
        wizard = self.env['sale.session.close'].create({
            'session_id': session.id,
        })
        self.assertEquals(wizard.team_id, session.team_id)
        self.assertEquals(len(wizard.journal_line_ids), 2)
        self.assertEquals(wizard.journal_line_ids[0].amount_total, 200)
        self.assertEquals(wizard.journal_line_ids[1].amount_total, 200)
        self.assertEquals(self.team.get_actual_total_cash(), 200)
        session.team_id.cash_min_for_open_session = 10
        wizard = self.env['sale.session.close'].create({
            'session_id': session.id,
        })
        self.assertEquals(session.team_id.cash_min_for_open_session, 10)
        self.assertEquals(session.total_payment_cash, 200)
        self.assertEquals(session.amount_send, 0)
        self.assertEquals(wizard.amount_send, 190)
        self.assertEquals(self.team.get_actual_total_cash(), 200)
        wizard.amount_send = 1000
        with self.assertRaises(ValidationError):
            wizard.action_confirm()
        wizard.amount_send = 30
        wizard.action_confirm()
        self.assertEquals(session.close_date.date(), fields.Date.today())
        self.assertEquals(session.amount_send, 30)
        self.assertEquals(self.team.get_actual_total_cash(), 200)
        validate_wizard = self.env['sale.session.validate'].create({
            'session_id': session.id,
            'amount_send': session.amount_send,
        })
        validate_wizard.amount_send = 50
        with self.assertRaises(ValidationError):
            validate_wizard.action_confirm()
        validate_wizard.journal_id = self.bank_journal.id
        validate_wizard.action_confirm()
        self.assertEquals(session.validation_date.date(), fields.Date.today())
        self.assertTrue(session.validate_move_id)
        self.assertEquals(session.validate_move_id.state, 'posted')
        move = session.validate_move_id
        self.assertEquals(
            move.line_ids[0].partner_id, session.company_id.partner_id)
        debit_account = self.bank_journal.default_debit_account_id
        debit_line = move.line_ids.filtered(
            lambda ln: ln.account_id == debit_account)
        self.assertEquals(debit_line.debit, 50)
        self.assertEquals(debit_line.credit, 0)
        self.assertIn(session.name, debit_line.name)
        credit_line = move.line_ids.filtered(
            lambda ln: ln.account_id != debit_account)
        self.assertEquals(credit_line.debit, 0)
        self.assertEquals(credit_line.credit, 50)
        with self.assertRaises(UserError):
            session.action_revert_to_close()
        self.bank_journal.update_posted = True
        session.action_revert_to_close()
        self.assertFalse(session.validate_move_id)
        self.assertFalse(session.validation_date)
        self.assertEquals(session.state, 'close')
        session2 = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session2.action_open()
        with self.assertRaises(ValidationError):
            session.action_revert_to_open()

    def test_cash_min_for_open_session(self):
        session1 = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        self.assertEquals(self.team.get_actual_total_cash(), 0)
        session1.action_open()
        cash_journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        self.team.write({
            'cash_payment_journal_id': cash_journal.id,
        })
        action = session1.action_close()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEquals(session1.state, 'close')
        self.team.cash_min_for_open_session = 1000
        session2 = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        with self.assertRaises(UserError):
            session2.action_open()
        self.team.cash_min_for_open_session = 0
        session2.action_open()
        session2.register_payment(self.partner, cash_journal, 1000)
        action = session2.action_close()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        session3 = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session3.action_open()
        self.assertEquals(self.team.get_actual_total_cash(), 1000)
        self.assertEquals(session3.balance_end, 1000)

    def test_action_confirm_and_pay(self):
        payment_term = self.env['account.payment.term'].create({
            'name': 'Test Payment term',
        })
        self.partner.property_payment_term_id = payment_term.id
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        session.action_open()
        self.assertEquals(session.balance_start, 0)
        invoice_journal = self.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1)
        cash_journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        self.team.write({
            'invoice_journal_ids': [(6, 0, [invoice_journal.id])],
            'cash_payment_journal_id': cash_journal.id,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'session_id': session.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })
        sale.session_pay(
            sale.amount_total, sale.team_id.cash_payment_journal_id)
        self.assertEquals(sale.picking_ids.state, 'done')
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(sale.invoice_ids.state, 'paid')
        self.assertEquals(len(sale.picking_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertFalse(invoice.payment_term_id)
        self.assertEquals(invoice.payment_ids[0].amount, sale.amount_total)
        self.assertEquals(self.team.get_actual_total_cash(), 115)

    def test_payment(self):
        payment_term = self.env['account.payment.term'].create({
            'name': 'Test Payment term',
        })
        self.partner.property_payment_term_id = payment_term.id
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        session.action_open()
        self.assertEquals(self.team.get_actual_total_cash(), 0)
        invoice_journal = self.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1)
        cash_journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        self.team.write({
            'invoice_journal_ids': [(6, 0, [invoice_journal.id])],
            'cash_payment_journal_id': cash_journal.id,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'session_id': session.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1,
                    'tax_id': [(6, 0, [])],
                }),
            ]
        })
        wizard = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': sale.id,
            'journal_id': cash_journal.id,
            'amount': 150,
        })
        self.assertEquals(wizard.amount_change, 50)
        wizard.action_pay()
        payment = sale.invoice_ids.payment_ids
        self.assertEquals(payment.amount, 100)
        self.assertEquals(payment.partner_id, sale.partner_id)
        self.assertEquals(payment.journal_id, cash_journal)
        self.assertEquals(self.team.get_actual_total_cash(), 100)

    def test_action_confirm_and_pay_with_wizard(self):
        payment_term = self.env['account.payment.term'].create({
            'name': 'Test Payment term',
        })
        self.partner.property_payment_term_id = payment_term.id
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        session.action_open()
        invoice_journal = self.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1)
        cash_journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        self.team.write({
            'invoice_journal_ids': [(6, 0, [invoice_journal.id])],
            'cash_payment_journal_id': cash_journal.id,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'session_id': session.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'tax_id': [(6, 0, [])],
                    'product_uom_qty': 1}),
            ]
        })
        self.assertEquals(len(sale.order_line[0].tax_id), 0)
        wizard = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': sale.id,
            'journal_id': cash_journal.id,
            'amount': 250,
        })
        self.assertEquals(wizard.amount_total, 100)
        self.assertEquals(wizard.amount, 250)
        self.assertEquals(wizard.amount_change, 150)
        wizard.action_pay()
        invoice = sale.invoice_ids[0]
        self.assertEquals(invoice.payment_ids[0].amount, sale.amount_total)
        self.assertEquals(self.team.get_actual_total_cash(), 100)

    def test_action_confirm_and_pay_with_wizard_autocomplete_amount(self):
        payment_term = self.env['account.payment.term'].create({
            'name': 'Test Payment term',
        })
        self.partner.property_payment_term_id = payment_term.id
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        session.action_open()
        invoice_journal = self.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1)
        cash_journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        self.team.write({
            'autocomplete_amount': True,
            'invoice_journal_ids': [(6, 0, [invoice_journal.id])],
            'cash_payment_journal_id': cash_journal.id,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'session_id': session.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'tax_id': [(6, 0, [])],
                    'product_uom_qty': 1}),
            ]
        })
        self.assertEquals(len(sale.order_line[0].tax_id), 0)
        wizard = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': sale.id,
            'journal_id': cash_journal.id,
        })
        self.assertEquals(wizard.amount, wizard.amount_total)
        wizard.action_pay()
        invoice = sale.invoice_ids[0]
        self.assertEquals(invoice.payment_ids[0].amount, sale.amount_total)
        self.assertEquals(self.team.get_actual_total_cash(), 100)

    def test_action_confirm_and_pay_without_stock(self):
        self.stock_inventory_adjust(self.product, 0)
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        self.assertEquals(self.team.get_actual_total_cash(), 0)
        journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        self.team.cash_payment_journal_id = journal.id
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'session_id': session.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 100}),
            ]
        })
        with self.assertRaises(UserError):
            sale.session_pay(
                sale.amount_total, sale.team_id.cash_payment_journal_id)
        self.assertNotEquals(sale.picking_ids.state, 'done')
        self.assertEquals(sale.state, 'sale')
        self.assertFalse(sale.invoice_ids)
        self.assertEquals(self.team.get_actual_total_cash(), 0)

    def test_action_confirm_and_pay_force_stock(self):
        self.stock_inventory_adjust(self.product, 0)
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        self.assertEquals(self.team.get_actual_total_cash(), 0)
        journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        self.team.cash_payment_journal_id = journal.id
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'session_id': session.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 100}),
            ]
        })
        self.team.force_stock = True
        sale.session_pay(
            sale.amount_total, sale.team_id.cash_payment_journal_id)
        self.assertEquals(sale.picking_ids.state, 'done')
        self.assertEquals(sale.state, 'sale')
        self.assertTrue(sale.invoice_ids)
        self.assertEquals(sale.amount_total, 11500)
        self.assertEquals(self.team.get_actual_total_cash(), 11500)

    def test_action_confirm_and_pay_service_product(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        self.assertEquals(self.team.get_actual_total_cash(), 0)
        journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        self.team.cash_payment_journal_id = journal.id
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'session_id': session.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.service_product.id,
                    'price_unit': 100,
                    'product_uom_qty': 100}),
            ]
        })
        sale.session_pay(
            sale.amount_total, sale.team_id.cash_payment_journal_id)
        self.assertEquals(sale.state, 'sale')
        self.assertTrue(sale.invoice_ids)
        self.assertEquals(sale.invoice_ids.state, 'paid')
        self.assertEquals(self.team.get_actual_total_cash(), 11500)
        self.assertEquals(session.balance_end, 11500)

    def test_session_with_sale_and_refund(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        session.action_open()
        self.assertEquals(self.team.get_actual_total_cash(), 0)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'session_id': session.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })
        wizard = self.env['sale.order.payment'].create({
            'sale_id': sale.id,
            'journal_id': journal.id,
            'amount': sale.amount_total,
        })
        wizard.action_confirm()
        self.assertEquals(session.balance_end, sale.amount_total)
        self.assertEquals(sale.state, 'sale')
        invoice = sale.invoice_ids
        self.assertEquals(len(sale.invoice_ids), 1)
        self.assertEquals(sale.invoice_ids.state, 'paid')
        account_invoice_refund = \
            self.env['account.invoice.refund'].with_context(
                active_id=invoice.id,
                active_ids=invoice.ids
            ).create(dict(
                description='Total refund',
                filter_refund='refund'
            ))
        account_invoice_refund.invoice_refund()
        self.assertEqual(1, len(invoice.refund_invoice_ids))
        refund_invoice = invoice.refund_invoice_ids[0]
        refund_invoice.compute_taxes()
        refund_invoice.action_invoice_open()
        self.assertEqual(refund_invoice.state, 'open')
        payment_method = self.env['account.payment.method'].search([
            ('payment_type', '=', 'outbound'),
        ], limit=1)
        payment = self.env['account.payment'].with_context(
            active_model='account.invoice',
            active_id=refund_invoice.id,
            active_ids=refund_invoice.ids,
        ).create({
            'payment_method_id': payment_method.id,
            'journal_id': journal.id,
            'sale_session_id': session.id,
        })
        payment.action_validate_invoice_payment()
        self.assertEqual(refund_invoice.state, 'paid')
        self.assertEquals(session.balance_start, 0)

    def test_session_mismatch(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        self.assertEquals(session.state, 'draft')
        session.action_open()
        self.assertEquals(session.state, 'open')
        journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        session.register_payment(self.partner, journal, 100)
        self.assertEquals(self.team.get_actual_total_cash(), 100)
        self.assertEquals(session.balance_start, 0)
        self.assertEquals(session.balance_end, 100)
        action = session.action_close()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEquals(session.state, 'close')
        self.assertEquals(session.balance_start, 0)
        self.assertEquals(session.balance_end, 100)
        self.assertEquals(session.total_cash, 100)
        self.assertEquals(session.close_cash_count_mismatch, 0)
        self.assertEquals(self.team.get_actual_total_cash(), 100)

    def test_close_session_with_cash_count_diff(self):
        payment_term = self.env['account.payment.term'].create({
            'name': 'Test Payment term',
        })
        self.partner.property_payment_term_id = payment_term.id
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        self.assertEquals(self.team.get_actual_total_cash(), 0)
        invoice_journal = self.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1)
        cash_journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        self.team.write({
            'invoice_journal_ids': [(6, 0, [invoice_journal.id])],
            'cash_payment_journal_id': cash_journal.id,
            'cash_money_values': '10,20',
            'cash_count_type': 'close',
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'session_id': session.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 150,
                    'tax_id': [(6, 0, [])],
                    'product_uom_qty': 1,
                }),
            ]
        })
        wizard = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': sale.id,
            'journal_id': cash_journal.id,
            'amount': 250,
        })
        self.assertEquals(sale.amount_total, 150)
        self.assertEquals(wizard.amount, 250)
        self.assertEquals(wizard.amount_total, 150)
        self.assertEquals(wizard.amount_change, 100)
        wizard.action_pay()
        self.assertEquals(self.team.get_actual_total_cash(), 150)
        self.assertEquals(wizard.session_id, session)
        cash_payments = session.payment_ids.filtered(
            lambda p: p.journal_id.type == 'cash')
        self.assertEquals(cash_payments.amount, 150)
        action = session.action_close()
        self.assertEquals(
            action['res_model'], 'sale.session.wizard_cash_count')
        wizard = self.env[action['res_model']].browse(action['res_id'])
        cash_count_ids = wizard.journal_cash_count_ids
        self.assertEquals(len(cash_count_ids), 1)
        self.assertEquals(len(cash_count_ids.line_ids), 2)
        line = cash_count_ids.line_ids[0]
        line.quantity = 3
        self.assertEquals(cash_count_ids[0].amount_total, 30)
        action = wizard.action_confirm()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEquals(session.balance_start, 0)
        self.assertEquals(session.state, 'close')
        self.assertEquals(len(session.open_cash_count_ids), 0)
        close_cash_counts = session.close_cash_count_ids
        self.assertEquals(len(close_cash_counts), 1)
        self.assertEquals(len(close_cash_counts.cash_count_line_ids), 2)
        self.assertEquals(session.open_cash_count_total, 0)
        self.assertEquals(session.close_cash_count_total, 30)
        self.assertTrue(session.mismatch_close_move_ids)
        self.assertEquals(session.mismatch_close_move_ids.state, 'draft')
        session.mismatch_close_move_ids.action_post()
        self.assertEquals(session.mismatch_close_move_ids.state, 'posted')
        self.assertEquals(session.total_cash, 150)
        self.assertEquals(session.close_cash_count_mismatch, 120)
        self.assertEquals(
            sum(session.mismatch_close_move_ids.line_ids.mapped('debit')), 120)
        session.mismatch_close_move_ids.journal_id.update_posted = True
        session.action_revert_to_open()
        self.assertFalse(session.mismatch_close_move_ids)
        self.assertEquals(session.state, 'open')
        self.assertEquals(session.total_payment_cash, 150)
        self.assertEquals(session.total_cash, 150)
        self.assertEquals(session.close_cash_count_mismatch, 120)
        session.amount_send = 10
        session.action_unlink_close_cash_counts()
        action = session.action_close()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        cash_count_ids = wizard.journal_cash_count_ids
        line = cash_count_ids.line_ids[0]
        line.quantity = 15
        self.assertEquals(cash_count_ids.amount_total, 150)
        action = wizard.action_confirm()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.amount_send = 50
        wizard.action_confirm()
        internal_payment = self.env['account.payment'].create({
            'payment_type': 'transfer',
            'amount': 50,
            'journal_id': self.cash_journal.id,
            'destination_journal_id': self.bank_journal.id,
            'payment_method_id': self.env.ref(
                'account.account_payment_method_manual_in').id,
        })
        internal_payment.post()
        self.assertEquals(session.state, 'close')
        self.team.cash_count_type = 'open-close'
        session2 = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        self.assertEquals(session2.previous_id, session)
        action = session2.action_open()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        cash_count_ids = wizard.journal_cash_count_ids
        line = cash_count_ids.line_ids[0]
        self.assertEquals(len(cash_count_ids.line_ids), 2)
        line = cash_count_ids.line_ids[0]
        line.quantity = 6
        wizard.action_confirm()
        self.assertEquals(cash_count_ids.amount_total, 60)
        self.assertEquals(session2.open_cash_count_total, 60)
        self.assertEquals(session2.open_cash_count_mismatch, -40)
        self.assertEquals(session2.state, 'open')

    def test_close_session_with_cash_count_diff_multiple_cash_journals(self):
        payment_term = self.env['account.payment.term'].create({
            'name': 'Test Payment term',
        })
        self.partner.property_payment_term_id = payment_term.id
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        self.assertEquals(self.team.get_actual_total_cash(), 0)
        invoice_journal = self.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1)
        cash_journals = self.env['account.journal'].search(
            [('type', '=', 'cash')])
        self.assertEquals(len(cash_journals), 2)
        self.team.write({
            'invoice_journal_ids': [(6, 0, [invoice_journal.id])],
            'payment_journal_ids': [(6, 0, cash_journals.ids)],
            'cash_payment_journal_id': cash_journals[0].id,
            'cash_money_values': '10,20',
            'cash_count_type': 'close',
        })
        sale_1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'session_id': session.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 150,
                    'tax_id': [(6, 0, [])],
                    'product_uom_qty': 1,
                }),
            ]
        })
        wizard = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': sale_1.id,
            'journal_id': cash_journals[0].id,
            'amount': 250,
        })
        self.assertEquals(sale_1.amount_total, 150)
        self.assertEquals(wizard.amount, 250)
        self.assertEquals(wizard.amount_total, 150)
        self.assertEquals(wizard.amount_change, 100)
        wizard.action_pay()
        self.assertEquals(self.team.get_actual_total_cash(), 150)
        self.assertEquals(wizard.session_id, session)
        cash_payments = session.payment_ids.filtered(
            lambda p: p.journal_id.type == 'cash')
        self.assertEquals(cash_payments.amount, 150)
        sale_2 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'session_id': session.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 50,
                    'tax_id': [(6, 0, [])],
                    'product_uom_qty': 1,
                }),
            ]
        })
        wizard = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': sale_2.id,
            'journal_id': cash_journals[1].id,
            'amount': 100,
        })
        self.assertEquals(sale_2.amount_total, 50)
        self.assertEquals(wizard.amount, 100)
        self.assertEquals(wizard.amount_total, 50)
        self.assertEquals(wizard.amount_change, 50)
        wizard.action_pay()
        self.assertEquals(self.team.get_actual_total_cash(), 200)
        self.assertEquals(wizard.session_id, session)
        cash_payments = session.payment_ids.filtered(
            lambda p: p.journal_id.type == 'cash')
        self.assertEquals(len(cash_payments), 2)
        self.assertEquals(sum(cash_payments.mapped('amount')), 200)
        action = session.action_close()
        self.assertEquals(
            action['res_model'], 'sale.session.wizard_cash_count')
        wizard = self.env[action['res_model']].browse(action['res_id'])
        cash_count_ids = wizard.journal_cash_count_ids
        self.assertEquals(len(cash_count_ids), 2)
        self.assertEquals(
            cash_count_ids[0].journal_id, cash_journals[0])
        self.assertEquals(
            cash_count_ids[1].journal_id, cash_journals[1])
        self.assertEquals(len(cash_count_ids[0].line_ids), 2)
        line = cash_count_ids[0].line_ids[0]
        line.quantity = 3
        self.assertEquals(cash_count_ids[0].amount_total, 30)
        action = wizard.action_confirm()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEquals(session.balance_start, 0)
        self.assertEquals(session.state, 'close')
        self.assertEquals(len(session.open_cash_count_ids), 0)
        close_cash_counts = session.close_cash_count_ids
        self.assertEquals(len(close_cash_counts), 2)
        self.assertEquals(
            len(close_cash_counts.mapped('cash_count_line_ids')), 4)
        self.assertEquals(session.open_cash_count_total, 0)
        self.assertEquals(session.close_cash_count_total, 30)

        self.assertTrue(session.mismatch_close_move_ids)
        self.assertEquals(True, all(
            mv.state == 'draft' for mv in session.mismatch_close_move_ids))
        session.mismatch_close_move_ids.action_post()
        self.assertEquals(True, all(
            mv.state == 'posted' for mv in session.mismatch_close_move_ids))
        self.assertEquals(session.total_cash, 200)
        self.assertEquals(session.close_cash_count_mismatch, 170)
        self.assertEquals(
            sum(session.mismatch_close_move_ids.mapped('line_ids.debit')), 170)
        mv_close_mismatch_1 = session.mismatch_close_move_ids[0]
        mv_close_mismatch_2 = session.mismatch_close_move_ids[1]
        self.assertEquals(
            sum(mv_close_mismatch_1.line_ids.mapped('debit')), 120)
        self.assertEquals(
            sum(mv_close_mismatch_2.line_ids.mapped('debit')), 50)
        self.assertEquals(mv_close_mismatch_1.journal_id, cash_journals[0])
        self.assertEquals(mv_close_mismatch_2.journal_id, cash_journals[1],)
        session.mismatch_close_move_ids.mapped('journal_id').write({
            'update_posted': True,
        })
        session.action_revert_to_open()
        self.assertFalse(session.mismatch_close_move_ids)
        self.assertEquals(session.state, 'open')
        self.assertEquals(session.total_payment_cash, 200)
        self.assertEquals(session.total_cash, 200)
        self.assertEquals(session.close_cash_count_mismatch, 170)
        session.amount_send = 10
        session.action_unlink_close_cash_counts()
        action = session.action_close()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        cash_count_ids = wizard.journal_cash_count_ids
        self.assertEquals(len(cash_count_ids), 2)
        self.assertEquals(
            cash_count_ids[0].journal_id, cash_journals[0])
        self.assertEquals(
            cash_count_ids[1].journal_id, cash_journals[1])
        self.assertEquals(len(cash_count_ids[0].line_ids), 2)
        line = cash_count_ids[0].line_ids[0]
        line.quantity = 15
        self.assertEquals(cash_count_ids[0].amount_total, 150)
        action = wizard.action_confirm()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.amount_send = 50
        wizard.action_confirm()
        internal_payment = self.env['account.payment'].create({
            'payment_type': 'transfer',
            'amount': 50,
            'journal_id': self.cash_journal.id,
            'destination_journal_id': self.bank_journal.id,
            'payment_method_id': self.env.ref(
                'account.account_payment_method_manual_in').id,
        })
        internal_payment.post()
        self.assertEquals(session.state, 'close')
        self.team.cash_count_type = 'open-close'
        session2 = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        self.assertEquals(session2.previous_id, session)
        action = session2.action_open()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        cash_count_ids = wizard.journal_cash_count_ids
        self.assertEquals(len(cash_count_ids), 2)
        self.assertEquals(
            cash_count_ids[0].journal_id, cash_journals[0])
        self.assertEquals(
            cash_count_ids[1].journal_id, cash_journals[1])
        line = cash_count_ids[0].line_ids[0]
        line.quantity = 6
        wizard.action_confirm()
        self.assertEquals(cash_count_ids[0].amount_total, 60)
        self.assertEquals(session2.open_cash_count_total, 60)
        self.assertEquals(session2.open_cash_count_mismatch, -90)
        self.assertEquals(session2.state, 'open')

    def test_cross_reference_previous(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
            'state': 'open',
        })
        session2 = self.env['sale.session'].create({
            'team_id': self.team.id,
            'previous_id': session.id,
        })
        with self.assertRaises(ValidationError):
            session.previous_id = session2.id
        session.state = 'close'
        session2.state = 'close'
        session3 = self.env['sale.session'].create({
            'team_id': self.team.id,
            'previous_id': session.id,
        })
        self.assertEquals(session3.previous_id, session2)

    def test_product_with_required_lot_action_confirm(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        self.assertEquals(session.state, 'draft')
        session.action_open()
        invoice_journal = self.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1)
        cash_journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        self.team.write({
            'invoice_journal_ids': [(6, 0, [invoice_journal.id])],
            'cash_payment_journal_id': cash_journal.id,
            'cash_money_values': '10,20',
            'cash_count_type': 'close',
        })
        self.product.tracking = 'serial'
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'session_id': session.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 150,
                    'tax_id': [(6, 0, [])],
                    'product_uom_qty': 1,
                }),
            ]
        })
        wizard = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': sale.id,
            'journal_id': cash_journal.id,
            'amount': 150,
        })
        action = wizard.action_confirm()
        self.assertNotIn('sale.order.confirm_select_lot', action)
        self.assertEquals(action['type'], 'ir.actions.act_window_close')
        self.assertEquals(sale.picking_ids.state, 'assigned')

    def test_product_with_required_lot_action_credit(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        self.assertEquals(session.state, 'draft')
        session.action_open()
        invoice_journal = self.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1)
        cash_journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        self.team.write({
            'invoice_journal_ids': [(6, 0, [invoice_journal.id])],
            'cash_payment_journal_id': cash_journal.id,
            'cash_money_values': '10,20',
            'cash_count_type': 'close',
        })
        self.stock_inventory_adjust(self.product, 0)
        self.product.tracking = 'serial'
        lot = self.env['stock.production.lot'].create({
            'name': 'Test lot',
            'product_id': self.product.id,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'session_id': session.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 150,
                    'tax_id': [(6, 0, [])],
                    'product_uom_qty': 1,
                }),
            ]
        })
        wizard = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': sale.id,
            'journal_id': cash_journal.id,
            'amount': 150,
        })
        self.assertEqual(wizard.step, 0)
        self.assertEquals(len(wizard.line_ids), 1)
        wizard.line_ids[0].lot_id = lot.id

        def get_product_qty_available_with_lot():
            return self.env['product.product'].with_context(
                lot_id=lot.id).browse(self.product.id).qty_available

        self.assertEquals(get_product_qty_available_with_lot(), 0)
        wizard = wizard.with_context(
            active_model='sale.order.confirm_and_pay',
            active_id=wizard.id,
        )
        with self.assertRaises(UserError):
            with self.env.cr.savepoint():
                wizard.action_credit()
        self.stock_inventory_adjust(self.product, 1, lot=lot)
        self.assertEquals(self.product.qty_available, 1)
        self.assertEquals(get_product_qty_available_with_lot(), 1)
        action = wizard.action_credit()
        self.assertEquals(self.product.qty_available, 0)
        self.assertEquals(get_product_qty_available_with_lot(), 0)
        self.assertEquals(action['type'], 'ir.actions.report')
        self.assertEquals(sale.picking_ids.state, 'done')

    def test_sale_session_cancel_balance_end(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        self.assertEquals(self.team.get_actual_total_cash(), 0)
        journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        self.team.cash_payment_journal_id = journal.id
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'session_id': session.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.service_product.id,
                    'price_unit': 100,
                    'product_uom_qty': 100}),
            ]
        })
        sale.session_pay(
            sale.amount_total, sale.team_id.cash_payment_journal_id)
        self.assertEquals(sale.state, 'sale')
        self.assertTrue(sale.invoice_ids)
        self.assertEquals(sale.invoice_ids.state, 'paid')
        self.assertEquals(self.team.get_actual_total_cash(), 11500)
        self.assertEquals(session.balance_end, 11500)
        invoice = sale.invoice_ids
        self.env['account.invoice.refund'].with_context(
            active_ids=[invoice.id]).create({
                'filter_refund': 'refund',
                'description': 'Total refund',
            }).invoice_refund()
        refund_invoice = invoice.refund_invoice_ids[0]
        sale.action_cancel()
        refund_invoice.action_invoice_open()
        payment_method = self.env['account.payment.method'].search([
            ('payment_type', '=', 'outbound'),
        ], limit=1)
        payment = self.env['account.payment'].with_context(
            active_model='account.invoice',
            active_id=refund_invoice.id,
            active_ids=refund_invoice.ids,
        ).create({
            'payment_method_id': payment_method.id,
            'journal_id': journal.id,
            'sale_session_id': session.id,
        })
        payment.action_validate_invoice_payment()
        self.assertEquals(session.balance_end, 0)
        self.assertEquals(self.team.get_actual_total_cash(), 0)
        for invoice in sale.invoice_ids:
            self.assertEquals(invoice.state, 'paid')

    def test_sale_confirm_user_error_without_stock(self):
        self.stock_inventory_adjust(self.product, 0)
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        self.assertEquals(self.team.get_actual_total_cash(), 0)
        journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        self.team.cash_payment_journal_id = journal.id
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'session_id': session.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 100}),
            ]
        })
        location = self.env.ref('stock.stock_location_stock')
        available_qty = self.env['stock.quant']._get_available_quantity(
            self.product, location)
        self.assertTrue(sale.order_line[0].product_uom_qty > available_qty)
        with self.assertRaises(UserError) as result:
            sale.session_pay(
                sale.amount_total, sale.team_id.cash_payment_journal_id)
        self.assertEqual(
            result.exception.name,
            '%s units of the product %s are ordered but '
            'only %s units in stock' % (
                sale.order_line[0].product_uom_qty, self.product.name,
                available_qty))
