###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase

_log = logging.getLogger(__name__)


class TestSaleSession(TransactionCase):

    def setUp(self):
        super().setUp()
        templates = self.env['account.chart.template'].search([], limit=1)
        self.l10n_installed = self.env['ir.module.module'].search([
            ('name', '=', 'l10n_es'),
            ('state', '=', 'installed'),
        ])
        if not templates:
            _log.warning(
                'Test skipped because there is no chart of account defined '
                'new company')
            self.skipTest('No Chart of account found')
            return
        if not templates.existing_accounting(self.env.company):
            templates.try_loading(self.env.company)
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self._stock_inventory_adjust(self.product, 1000)
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
            'account_type': 'asset_cash',
            'name': 'Bank test account',
        })
        self.bank_journal = self.env['account.journal'].create({
            'code': 'BNK',
            'name': 'Bank journal test',
            'type': 'bank',
            'default_account_id': account_bank.id,
        })
        account_cash = self.env['account.account'].create({
            'code': '110402',
            'account_type': 'asset_cash',
            'name': 'Cash test account',
        })
        self.cash_journal = self.env['account.journal'].create({
            'code': 'CASH',
            'name': 'Cash journal test',
            'type': 'cash',
            'default_account_id': account_cash.id,
        })
        self.invoice_journal = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        mismatch_account = self.env['account.account'].create({
            'code': '79999',
            'name': 'Mismatch account for test close session',
            'account_type': 'expense',
        })
        self.team = self.env['crm.team'].create({
            'name': 'Test Sale Team',
            'invoice_journal_ids': [(6, 0, [self.invoice_journal.id])],
            'payment_journal_ids': [
                (6, 0, [self.cash_journal.id, self.bank_journal.id])],
            'cash_payment_journal_id': self.cash_journal.id,
            'require_sale_session': True,
            'mismatch_account': mismatch_account.id,
        })

    def _stock_inventory_adjust(self, product, qty, lot=None):
        inventory = self.env['stock.quant'].search([
            ('location_id', '=', self.stock_location.id),
            ('product_id', '=', self.product.id),
            ('lot_id', '=', lot.id if lot else False),
        ])
        if not inventory:
            inventory = self.env['stock.quant'].create({
                'product_id': product.id,
                'location_id': self.stock_location.id,
                'lot_id': lot.id if lot else False,
            })
        inventory.inventory_quantity = qty
        inventory.action_apply_inventory()

    def _create_and_pay_sale(self, session, payment_type=None):
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
            ],
        })
        journals = {
            'cash': self.cash_journal,
            'bank': self.bank_journal,
        }
        if payment_type in journals:
            sale.session_pay(
                amount=sale.amount_total,
                payment_journal=journals[payment_type])
        return sale

    def test_crm_team(self):
        with self.assertRaises(ValidationError):
            self.env['crm.team'].create({
                'name': 'Test Sale Team',
                'require_sale_session': True,
                'cash_money_values': 'a,',
            })
        self.env['crm.team'].create({
            'name': 'Test Sale Team',
            'require_sale_session': True,
            'cash_money_values': '1,',
        })
        self.env['crm.team'].create({
            'name': 'Test Sale Team',
            'require_sale_session': True,
            'cash_money_values': False,
        })
        team = self.env['crm.team'].create({
            'name': 'Test Sale Team',
            'require_sale_session': True,
            'cash_money_values': '1,2,3,',
        })
        self.assertEqual(round(sum(team.get_cash_money_values()), 2), 6.0)
        team.cash_money_values = '0.1,0.2,0.3'
        self.assertEqual(round(sum(team.get_cash_money_values()), 2), 0.6)

    def test_sale_session(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        self.assertTrue(session.name)
        self.assertIn('SS', session.name)
        self.assertEqual(session.open_date.date(), fields.Date.today())
        self.assertEqual(session.close_date, False)
        self.assertEqual(session.validation_date, False)
        self.assertFalse(session.get_current_sale_session(self.team.id))
        journal = self.team.cash_payment_journal_id
        self.team.cash_payment_journal_id = False
        with self.assertRaises(UserError):
            session.action_open()
        self.team.cash_payment_journal_id = journal
        session.action_open()
        self.assertEqual(session.state, 'open')
        self.assertEqual(
            session.get_current_sale_session(self.team.id), session)
        journal = self.team.cash_payment_journal_id
        self.team.cash_payment_journal_id = False
        session.state = 'draft'
        with self.assertRaises(UserError):
            session.action_open()
        self.team.cash_payment_journal_id = journal
        session.action_open()
        new_session = session.copy()
        self.assertEqual(new_session.state, 'draft')
        with self.assertRaises(ValidationError):
            new_session.action_open()

    def test_sale_sequences(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        self.assertTrue(session.name)
        self.assertIn('SS', session.name)
        self.assertNotIn('TEST', session.name)
        self.assertEqual(session.open_date.date(), fields.Date.today())
        sequence = self.env['ir.sequence'].create({
            'name': 'Test Sale Session Sequence',
            'code': 'sale.session.test',
            'implementation': 'standard',
            'prefix': 'TEST-SS-',
            'padding': 5,
        })
        self.team.sale_session_sequence_id = sequence.id
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        self.assertTrue(session.name)
        self.assertIn('TEST-SS', session.name)
        self.assertEqual(session.open_date.date(), fields.Date.today())

    def test_session_previous(self):
        def close_session(session):
            wizard = self.env['sale.session.close'].create({
                'session_id': session.id,
            })
            wizard.action_confirm()

        session_1 = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        self.assertFalse(session_1.previous_id)
        session_1.action_open()
        self.assertFalse(session_1.previous_id)
        session_2 = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        self.assertEqual(session_2.previous_id, session_1)
        close_session(session_1)
        session_2.action_open()
        self.assertEqual(session_2.previous_id, session_1)
        session_3 = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        self.assertEqual(session_3.previous_id, session_2)
        session_4 = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        self.assertEqual(session_4.previous_id, session_2)
        close_session(session_2)
        session_4.action_open()
        self.assertEqual(session_4.previous_id, session_2)
        self.assertEqual(session_3.previous_id, session_2)
        close_session(session_4)
        session_3.action_open()
        self.assertEqual(session_3.previous_id, session_4)

    def test_create_and_pay_sale_with_session_draft(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        self.assertFalse(session.previous_id)
        with self.assertRaises(UserError):
            self._create_and_pay_sale(session, payment_type='bank')
        session.action_open()
        self.assertFalse(session.previous_id)
        self._create_and_pay_sale(session, payment_type='bank')
        new_session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        with self.assertRaises(ValidationError):
            new_session.action_open()
        self.assertFalse(session.previous_id)
        action = session.action_close()
        self.assertFalse(session.previous_id)
        wizard = self.env['sale.session.close'].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEqual(session.state, 'close')
        with self.assertRaises(UserError):
            self._create_and_pay_sale(session, payment_type='bank')

    def test_pay_without_sale_session(self):
        with self.assertRaises(UserError):
            self._create_and_pay_sale(False, payment_type='cash')
        with self.assertRaises(UserError):
            self._create_and_pay_sale(False, payment_type='bank')

    def test_session_sale_pay_cash(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        self.assertEqual(self.team.get_actual_total_cash(), 0)
        sale = self._create_and_pay_sale(session, payment_type='cash')
        self.assertEqual(self.team.get_actual_total_cash(), 100)
        self.assertEqual(session.total_payment_cash, sale.amount_total)
        self.assertEqual(session.total_payment_bank, 0)
        self.assertEqual(session.total_payment, sale.amount_total)

    def test_session_sale_pay_bank(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        self.assertEqual(self.team.get_actual_total_cash(), 0)
        sale = self._create_and_pay_sale(session, payment_type='bank')
        self.assertEqual(self.team.get_actual_total_cash(), 0)
        self.assertEqual(session.total_payment_cash, 0)
        self.assertEqual(session.total_payment_bank, sale.amount_total)
        self.assertEqual(session.total_payment, sale.amount_total)

    def test_session_sale_credit(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        sale = self._create_and_pay_sale(session, payment_type='')
        sale.action_confirm()
        self.assertEqual(self.team.get_actual_total_cash(), 0)
        self.assertEqual(session.total_payment_cash, 0)
        self.assertEqual(session.total_payment_bank, 0)
        self.assertEqual(session.total_payment, 0)

    def test_session_close_with_sales(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        self._create_and_pay_sale(session, payment_type='cash')
        self._create_and_pay_sale(session, payment_type='bank')
        self._create_and_pay_sale(session, payment_type='credit')
        self.assertEqual(session.sale_count, 3)
        self.assertEqual(session.sale_line_count, 3)
        self.assertEqual(self.team.get_actual_total_cash(), 100)
        self.assertEqual(session.total_payment_cash, 100)
        self.assertEqual(session.total_payment_bank, 100)
        self.assertEqual(session.total_payment, 200)
        wizard = self.env['sale.session.close'].create({
            'session_id': session.id,
        })
        self.assertEqual(wizard.total_payment_cash, 100)
        wizard.action_confirm()
        self.assertEqual(session.state, 'close')
        self.assertEqual(session.close_date.date(), fields.Date.today())
        self.assertEqual(session.balance_end, 200)
        self.assertEqual(self.team.get_actual_total_cash(), 100)
        self.assertEqual(session.balance_diff, 200)

    def test_session_close_and_new_with_sales_and_send(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        self.assertEqual(self.team.get_actual_total_cash(), 0)
        self._create_and_pay_sale(session, payment_type='cash')
        self._create_and_pay_sale(session, payment_type='bank')
        self._create_and_pay_sale(session, payment_type='credit')
        self.assertEqual(session.total_payment_cash, 100)
        self.assertEqual(session.total_payment_bank, 100)
        self.assertEqual(session.total_payment, 200)
        self.assertEqual(self.team.get_actual_total_cash(), 100)
        wizard = self.env['sale.session.close'].create({
            'session_id': session.id,
            'amount_send': 20,
        })
        self.assertEqual(wizard.total_payment_cash, 100)
        wizard.action_confirm()
        self.assertEqual(session.state, 'close')
        self.assertEqual(session.close_date.date(), fields.Date.today())
        self.assertEqual(session.balance_end, 200)
        self.assertEqual(session.balance_diff, 200)
        internal_move = self.env['account.move'].create({
            'journal_id': self.cash_journal.id,
            'date': fields.Date.today(),
            'line_ids': [
                (0, 0, {
                    'account_id': self.cash_journal.default_account_id.id,
                    'debit': 0,
                    'credit': 20,
                }),
                (0, 0, {
                    'account_id': self.bank_journal.default_account_id.id,
                    'debit': 20,
                    'credit': 0,
                }),
            ],
        })
        internal_move.action_post()
        new_session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        new_session.action_open()
        self.assertEqual(self.team.get_actual_total_cash(), 80)
        self._create_and_pay_sale(new_session, 'cash')
        self._create_and_pay_sale(new_session, 'bank')
        self._create_and_pay_sale(new_session, 'credit')
        self.assertEqual(new_session.total_payment_cash, 100)
        self.assertEqual(new_session.total_payment_bank, 100)
        self.assertEqual(self.team.get_actual_total_cash(), 180)
        self.assertEqual(new_session.total_payment, 200)
        self.assertEqual(self.team.get_actual_total_cash(), 180)

    def test_session_payment(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        self.assertEqual(self.team.get_actual_total_cash(), 0)
        journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        self.assertTrue(journal)
        payment = session.register_payment(self.partner, journal, 100)
        self.assertEqual(payment.state, 'posted')
        self.assertEqual(payment.partner_id, self.partner)
        self.assertEqual(len(session.payment_ids), 1)
        self.assertEqual(sum(session.payment_ids.mapped('amount_signed')), 100)
        self.assertEqual(self.team.get_actual_total_cash(), 100)
        self.assertEqual(session.balance_end, 100)
        wizard = self.env['sale.session.payment'].create({
            'session_id': session.id,
            'partner_id': self.partner.id,
            'journal_id': journal.id,
        })
        wizard.amount = 50
        wizard.action_confirm()
        self.assertEqual(len(session.payment_ids), 2)
        self.assertEqual(sum(session.payment_ids.mapped('amount_signed')), 150)
        self.assertEqual(self.team.get_actual_total_cash(), 150)
        self.assertEqual(session.balance_end, 150)
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
        self.assertEqual(payment.payment_type, 'outbound')
        payment.action_post()
        self.assertEqual(sum(session.payment_ids.mapped('amount_signed')), 100)

    def test_session_close(self):
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
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ],
        })
        bank_journal = self.env['account.journal'].search(
            [('type', '=', 'bank')], limit=1)
        wizard = self.env['sale.order.payment'].create({
            'sale_id': sale.id,
            'journal_id': bank_journal.id,
        })
        wizard.amount = sale.amount_total
        wizard.action_confirm()
        self.assertEqual(session.balance_end, sale.amount_total)
        wizard = self.env['sale.session.payment'].create({
            'session_id': session.id,
            'partner_id': self.partner.id,
            'journal_id': self.cash_journal.id,
        })
        wizard.amount = 50
        wizard.action_confirm()
        wizard = self.env['sale.session.payment'].create({
            'session_id': session.id,
            'partner_id': self.partner.id,
            'journal_id': self.cash_journal.id,
        })
        wizard.amount = 50
        wizard.action_confirm()
        self.assertEqual(
            session.balance_end, sale.amount_total + 100)
        wizard = self.env['sale.session.close'].create({
            'session_id': session.id,
        })
        wizard.action_confirm()
        self.assertIsNot(session.close_date, False)
        self.assertIs(session.validation_date, False)
        self.assertEqual(len(wizard.journal_line_ids), 2)
        bank_line = wizard.journal_line_ids.filtered(
            lambda bl: bl.journal_id == bank_journal)
        self.assertEqual(bank_line.amount_total, sale.amount_total)

    def test_session_open_and_close_cash_count(self):
        self.team.cash_money_values = (
            '0.01,0.05,0.10,0.20,0.50,1,2,5,10,20,50,100,200,500')
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        cash_payment_journal = session.team_id.cash_payment_journal_id
        self.assertEqual(
            cash_payment_journal.default_account_id.opening_debit, 0)
        self.assertEqual(
            cash_payment_journal.default_account_id.opening_credit, 0)
        wizard = self.env['sale.session.wizard_cash_count'].create({
            'session_id': session.id,
            'type': 'open',
        })
        self.assertEqual(wizard.team_id, session.team_id)
        cash_count_ids = wizard.journal_cash_count_ids
        self.assertEqual(len(cash_count_ids), 1)
        self.assertEqual(len(cash_count_ids.line_ids), 14)
        line = cash_count_ids.line_ids[0]
        line.quantity = 3
        self.assertEqual(cash_count_ids.amount_total, 0.03)
        wizard.action_confirm()
        open_cash_counts = session.open_cash_count_ids
        self.assertEqual(len(open_cash_counts), 1)
        self.assertEqual(len(open_cash_counts.cash_count_line_ids), 14)
        self.assertEqual(len(session.close_cash_count_ids), 0)
        self.assertEqual(session.open_cash_count_total, 0.03)
        self.assertEqual(session.close_cash_count_total, 0)
        self.assertEqual(session.balance_start, 0.00)
        self.assertEqual(session.cash_count_start, 0.03)
        self.assertEqual(
            cash_payment_journal.default_account_id.opening_credit, 0)
        mismatch_open_move_lines = session.mismatch_open_move_ids.line_ids
        mismtch_acc_move_line = mismatch_open_move_lines.filtered(
            lambda ln: ln.account_id.id == session.team_id.mismatch_account.id)
        self.assertEqual(mismtch_acc_move_line.credit, 0.03)
        self.assertEqual(mismtch_acc_move_line.debit, 0.00)
        cash_acc_move_line = session.mismatch_open_move_ids.line_ids.filtered(
            lambda ln: ln.account_id.id != session.team_id.mismatch_account.id)
        self.assertEqual(cash_acc_move_line.credit, 0.00)
        self.assertEqual(cash_acc_move_line.debit, 0.03)
        self.assertEqual(session.open_cash_count_mismatch, 0.03)
        action = session.action_close()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEqual(session.mismatch_open_move_ids.state, 'draft')
        action = session.action_validate()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEqual(session.mismatch_open_move_ids.state, 'posted')
        wizard = self.env['sale.session.wizard_cash_count'].create({
            'session_id': session.id,
            'type': 'close',
        })
        self.assertEqual(wizard.team_id, session.team_id)
        cash_count_ids = wizard.journal_cash_count_ids
        self.assertEqual(len(cash_count_ids), 1)
        self.assertEqual(len(cash_count_ids.line_ids), 14)
        line = cash_count_ids.line_ids[0]
        line.quantity = 3
        self.assertEqual(wizard.journal_cash_count_ids.amount_total, 0.03)
        wizard.action_confirm()
        self.assertEqual(session.close_cash_count_total, 0.03)
        self.assertFalse(session.mismatch_close_move_ids)

    def test_session_open_and_close_cash_count_mismatch(self):
        self.team.cash_money_values = (
            '0.01,0.05,0.10,0.20,0.50,1,2,5,10,20,50,100,200,500')
        self.team.cash_count_type = 'open-close'
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        cash_payment_journal = session.team_id.cash_payment_journal_id
        self.assertEqual(
            cash_payment_journal.default_account_id.opening_debit, 0)
        self.assertEqual(
            cash_payment_journal.default_account_id.opening_credit, 0)
        wizard = self.env['sale.session.wizard_cash_count'].create({
            'session_id': session.id,
            'type': 'open',
        })
        self.assertEqual(wizard.team_id, session.team_id)
        cash_count_ids = wizard.journal_cash_count_ids
        self.assertEqual(len(cash_count_ids), 1)
        self.assertEqual(len(cash_count_ids.line_ids), 14)
        line = cash_count_ids.line_ids[0]
        line.quantity = 3
        self.assertEqual(wizard.journal_cash_count_ids.amount_total, 0.03)
        wizard.action_confirm()
        open_cash_counts = session.open_cash_count_ids
        self.assertEqual(len(open_cash_counts), 1)
        self.assertEqual(len(open_cash_counts.cash_count_line_ids), 14)
        self.assertEqual(len(session.close_cash_count_ids), 0)
        self.assertEqual(session.open_cash_count_total, 0.03)
        self.assertEqual(session.close_cash_count_total, 0)
        self.assertEqual(session.balance_start, 0.00)
        self.assertEqual(session.cash_count_start, 0.03)
        self.assertEqual(
            cash_payment_journal.default_account_id.opening_credit, 0)
        mismatch_open_move_lines = session.mismatch_open_move_ids.line_ids
        mismtch_acc_move_line = mismatch_open_move_lines.filtered(
            lambda ln: ln.account_id.id == session.team_id.mismatch_account.id)
        self.assertEqual(mismtch_acc_move_line.credit, 0.03)
        self.assertEqual(mismtch_acc_move_line.debit, 0.00)
        cash_acc_move_line = session.mismatch_open_move_ids.line_ids.filtered(
            lambda ln: ln.account_id.id != session.team_id.mismatch_account.id)
        self.assertEqual(cash_acc_move_line.credit, 0.00)
        self.assertEqual(cash_acc_move_line.debit, 0.03)
        self.assertEqual(session.open_cash_count_mismatch, 0.03)
        action = session.action_close()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEqual(session.mismatch_open_move_ids.state, 'draft')
        action = session.action_validate()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        self.assertEqual(session.mismatch_open_move_ids.state, 'draft')
        wizard.action_confirm()
        self.assertEqual(session.mismatch_open_move_ids.state, 'posted')

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
        self.assertEqual(wizard.team_id, session.team_id)
        self.assertEqual(len(wizard.journal_line_ids), 1)
        self.assertEqual(wizard.journal_line_ids.amount_total, 100)
        self.assertEqual(self.team.get_actual_total_cash(), 100)
        session.team_id.cash_min_for_open_session = 10
        wizard = wizard_obj.create({
            'session_id': session.id,
        })
        self.assertEqual(session.team_id.cash_min_for_open_session, 10)
        self.assertEqual(session.total_payment_cash, 100)
        self.assertEqual(session.amount_send, 0)
        self.assertEqual(wizard.amount_send, 90)
        self.assertEqual(self.team.get_actual_total_cash(), 100)
        wizard.amount_send = 1000
        with self.assertRaises(ValidationError):
            wizard.action_confirm()
        wizard.amount_send = 30
        wizard.action_confirm()
        self.assertEqual(session.close_date.date(), fields.Date.today())
        self.assertEqual(session.amount_send, 30)
        self.assertEqual(self.team.get_actual_total_cash(), 100)

    def test_session_close_and_validate(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        session.register_payment(self.partner, journal, 100)
        self._create_and_pay_sale(session, payment_type='cash')
        self._create_and_pay_sale(session, payment_type='bank')
        self._create_and_pay_sale(session, payment_type='bank')
        self._create_and_pay_sale(session, payment_type='credit')
        wizard = self.env['sale.session.close'].create({
            'session_id': session.id,
        })
        self.assertEqual(wizard.team_id, session.team_id)
        self.assertEqual(len(wizard.journal_line_ids), 2)
        self.assertEqual(wizard.journal_line_ids[0].amount_total, 200)
        self.assertEqual(wizard.journal_line_ids[1].amount_total, 200)
        self.assertEqual(self.team.get_actual_total_cash(), 200)
        session.team_id.cash_min_for_open_session = 10
        wizard = self.env['sale.session.close'].create({
            'session_id': session.id,
        })
        self.assertEqual(session.team_id.cash_min_for_open_session, 10)
        self.assertEqual(session.total_payment_cash, 200)
        self.assertEqual(session.amount_send, 0)
        self.assertEqual(wizard.amount_send, 190)
        self.assertEqual(self.team.get_actual_total_cash(), 200)
        wizard.amount_send = 1000
        with self.assertRaises(ValidationError):
            wizard.action_confirm()
        wizard.amount_send = 30
        wizard.action_confirm()
        self.assertEqual(session.close_date.date(), fields.Date.today())
        self.assertEqual(session.amount_send, 30)
        self.assertEqual(self.team.get_actual_total_cash(), 200)
        validate_wizard = self.env['sale.session.validate'].create({
            'session_id': session.id,
            'amount_send': session.amount_send,
        })
        with self.assertRaises(ValidationError):
            validate_wizard.action_confirm()
        validate_wizard.journal_id = self.bank_journal.id
        validate_wizard.action_confirm()
        self.assertEqual(session.validation_date.date(), fields.Date.today())
        self.assertTrue(session.validate_move_id)
        self.assertEqual(session.validate_move_id.state, 'posted')
        move = session.validate_move_id
        self.assertEqual(
            move.line_ids[0].partner_id, session.company_id.partner_id)
        debit_account = self.bank_journal.default_account_id
        debit_line = move.line_ids.filtered(
            lambda ln: ln.account_id == debit_account)
        self.assertEqual(debit_line.debit, 30)
        self.assertEqual(debit_line.credit, 0)
        self.assertIn(session.name, debit_line.name)
        credit_line = move.line_ids.filtered(
            lambda ln: ln.account_id != debit_account)
        self.assertEqual(credit_line.debit, 0)
        self.assertEqual(credit_line.credit, 30)
        session.action_revert_to_close()
        self.assertFalse(session.validate_move_id)
        self.assertFalse(session.validation_date)
        self.assertEqual(session.state, 'close')
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
        self._create_and_pay_sale(session, payment_type='cash')
        self._create_and_pay_sale(session, payment_type='bank')
        self._create_and_pay_sale(session, payment_type='bank')
        self._create_and_pay_sale(session, payment_type='credit')
        wizard = self.env['sale.session.close'].create({
            'session_id': session.id,
        })
        self.assertEqual(wizard.team_id, session.team_id)
        self.assertEqual(len(wizard.journal_line_ids), 2)
        self.assertEqual(wizard.journal_line_ids[0].amount_total, 200)
        self.assertEqual(wizard.journal_line_ids[1].amount_total, 200)
        self.assertEqual(self.team.get_actual_total_cash(), 200)
        session.team_id.cash_min_for_open_session = 10
        wizard = self.env['sale.session.close'].create({
            'session_id': session.id,
        })
        self.assertEqual(session.team_id.cash_min_for_open_session, 10)
        self.assertEqual(session.total_payment_cash, 200)
        self.assertEqual(session.amount_send, 0)
        self.assertEqual(wizard.amount_send, 190)
        self.assertEqual(self.team.get_actual_total_cash(), 200)
        wizard.amount_send = 1000
        with self.assertRaises(ValidationError):
            wizard.action_confirm()
        wizard.amount_send = 30
        wizard.action_confirm()
        self.assertEqual(session.close_date.date(), fields.Date.today())
        self.assertEqual(session.amount_send, 30)
        self.assertEqual(self.team.get_actual_total_cash(), 200)
        validate_wizard = self.env['sale.session.validate'].create({
            'session_id': session.id,
            'amount_send': session.amount_send,
        })
        validate_wizard.amount_send = 50
        with self.assertRaises(ValidationError):
            validate_wizard.action_confirm()
        validate_wizard.journal_id = self.bank_journal.id
        validate_wizard.action_confirm()
        self.assertEqual(session.validation_date.date(), fields.Date.today())
        self.assertTrue(session.validate_move_id)
        self.assertEqual(session.validate_move_id.state, 'posted')
        move = session.validate_move_id
        self.assertEqual(
            move.line_ids[0].partner_id, session.company_id.partner_id)
        debit_account = self.bank_journal.default_account_id
        debit_line = move.line_ids.filtered(
            lambda ln: ln.account_id == debit_account)
        self.assertEqual(debit_line.debit, 50)
        self.assertEqual(debit_line.credit, 0)
        self.assertIn(session.name, debit_line.name)
        credit_line = move.line_ids.filtered(
            lambda ln: ln.account_id != debit_account)
        self.assertEqual(credit_line.debit, 0)
        self.assertEqual(credit_line.credit, 50)
        session.action_revert_to_close()
        self.assertFalse(session.validate_move_id)
        self.assertFalse(session.validation_date)
        self.assertEqual(session.state, 'close')
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
        self.assertEqual(self.team.get_actual_total_cash(), 0)
        session1.action_open()
        self.team.write({
            'cash_payment_journal_id': self.cash_journal.id,
        })
        action = session1.action_close()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEqual(session1.state, 'close')
        self.team.cash_min_for_open_session = 1000
        session2 = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        with self.assertRaises(UserError):
            session2.action_open()
        self.team.cash_min_for_open_session = 0
        session2.action_open()
        session2.register_payment(self.partner, self.cash_journal, 1000)
        action = session2.action_close()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        session3 = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session3.action_open()
        self.assertEqual(self.team.get_actual_total_cash(), 1000)
        self.assertEqual(session3.balance_end, 1000)

    def test_action_confirm_and_pay(self):
        if not self.l10n_installed:
            self.skipTest('l10n_es module not installed')
        payment_term = self.env['account.payment.term'].create({
            'name': 'Test Payment term',
        })
        self.partner.property_payment_term_id = payment_term.id
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        self.assertEqual(session.balance_start, 0)
        self.team.write({
            'invoice_journal_ids': [(6, 0, [self.invoice_journal.id])],
            'cash_payment_journal_id': self.cash_journal.id,
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
            ],
        })
        sale.session_pay(
            amount=sale.amount_total,
            payment_journal=sale.team_id.cash_payment_journal_id)
        self.assertEqual(sale.picking_ids.state, 'done')
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(sale.invoice_ids.state, 'posted')
        self.assertEqual(len(sale.picking_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertEqual(invoice.payment_state, 'paid')
        self.assertEqual(self.team.get_actual_total_cash(), 121)
        self.assertIn(
            sale.team_id.cash_payment_journal_id.id,
            sale.sale_session_payment_journal_ids.ids)

    def test_payment(self):
        payment_term = self.env['account.payment.term'].create({
            'name': 'Test Payment term',
        })
        self.partner.property_payment_term_id = payment_term.id
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        self.assertEqual(self.team.get_actual_total_cash(), 0)
        self.team.write({
            'invoice_journal_ids': [(6, 0, [self.invoice_journal.id])],
            'cash_payment_journal_id': self.cash_journal.id,
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
            ],
        })
        wizard = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': sale.id,
            'journal_id': self.cash_journal.id,
        })
        wizard.amount = 150
        wizard._compute_amount()
        self.assertEqual(wizard.amount_change, 50)
        wizard.action_pay()
        self.assertEqual(sale.invoice_ids.payment_state, 'paid')
        self.assertEqual(sale.invoice_ids.amount_total, 100)
        self.assertEqual(sale.invoice_ids.partner_id, sale.partner_id)
        self.assertEqual(self.team.get_actual_total_cash(), 100)

    def test_action_confirm_and_pay_with_wizard(self):
        payment_term = self.env['account.payment.term'].create({
            'name': 'Test Payment term',
        })
        self.partner.property_payment_term_id = payment_term.id
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        self.team.write({
            'invoice_journal_ids': [(6, 0, [self.invoice_journal.id])],
            'cash_payment_journal_id': self.cash_journal.id,
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
            ],
        })
        self.assertEqual(len(sale.order_line[0].tax_id), 0)
        wizard = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': sale.id,
            'journal_id': self.cash_journal.id,
        })
        wizard.amount = 250
        wizard._compute_amount()
        self.assertEqual(wizard.amount_total, 100)
        self.assertEqual(wizard.amount, 250)
        self.assertEqual(wizard.amount_change, 150)
        wizard.action_pay()
        invoice = sale.invoice_ids[0]
        self.assertEqual(invoice.payment_state, 'paid')
        self.assertEqual(self.team.get_actual_total_cash(), 100)

    def test_action_confirm_and_pay_with_wizard_multi_payment(self):
        payment_term = self.env['account.payment.term'].create({
            'name': 'Test Payment term',
        })
        self.partner.property_payment_term_id = payment_term.id
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        self.team.write({
            'invoice_journal_ids': [(6, 0, [self.invoice_journal.id])],
            'cash_payment_journal_id': self.cash_journal.id,
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
            ],
        })
        self.assertEqual(len(sale.order_line[0].tax_id), 0)
        wizard = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': sale.id,
            'journal_id': self.cash_journal.id,
            'multi_payment': True,
        })
        wizard.payment_line_ids = [
            (0, 0, {
                'amount': 50,
                'journal_id': self.cash_journal.id,
            }),
            (0, 0, {
                'amount': 80,
                'journal_id': self.bank_journal.id,
            }),
        ]
        self.assertEqual(wizard.amount, 130)
        self.assertEqual(wizard.amount_total, 100)
        self.assertEqual(wizard.amount_change, 30)
        wizard.action_pay()
        invoice = sale.invoice_ids[0]
        self.assertEqual(invoice.payment_state, 'paid')
        self.assertEqual(self.team.get_actual_total_cash(), 50)
        self.assertIn(
            self.cash_journal.id, sale.sale_session_payment_journal_ids.ids)
        self.assertIn(
            self.bank_journal.id, sale.sale_session_payment_journal_ids.ids)

    def test_action_confirm_and_pay_with_wizard_autocomplete_amount(self):
        payment_term = self.env['account.payment.term'].create({
            'name': 'Test Payment term',
        })
        self.partner.property_payment_term_id = payment_term.id
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        self.team.write({
            'autocomplete_amount': True,
            'invoice_journal_ids': [(6, 0, [self.invoice_journal.id])],
            'cash_payment_journal_id': self.cash_journal.id,
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
            ],
        })
        self.assertEqual(len(sale.order_line[0].tax_id), 0)
        wizard = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': sale.id,
            'journal_id': self.cash_journal.id,
        })
        self.assertEqual(wizard.amount, wizard.amount_total)
        wizard.action_pay()
        cash_payments = session.payment_ids.filtered(
            lambda p: p.journal_id.type == 'cash')
        self.assertEqual(cash_payments.amount, 100)
        self.assertEqual(self.team.get_actual_total_cash(), 100)

    def test_action_confirm_and_pay_without_stock(self):
        self._stock_inventory_adjust(self.product, 0)
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        self.assertEqual(self.team.get_actual_total_cash(), 0)
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
            ],
        })
        inventory = self.env['stock.quant'].search([
            ('product_id', '=', self.product.id),
        ])
        inventory.inventory_quantity = 0
        inventory.action_apply_inventory()
        with self.assertRaises(UserError):
            sale.session_pay(
                amount=sale.amount_total,
                payment_journal=sale.team_id.cash_payment_journal_id)
        self.assertNotEqual(sale.picking_ids.state, 'done')
        self.assertEqual(sale.state, 'draft')
        self.assertFalse(sale.invoice_ids)
        self.assertEqual(self.team.get_actual_total_cash(), 0)

    def test_action_confirm_and_pay_force_stock(self):
        if not self.l10n_installed:
            self.skipTest('l10n_es module not installed')
        self._stock_inventory_adjust(self.product, 0)
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        self.assertEqual(self.team.get_actual_total_cash(), 0)
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
            ],
        })
        self.team.force_stock = True
        sale.session_pay(
            amount=sale.amount_total,
            payment_journal=sale.team_id.cash_payment_journal_id)
        self.assertEqual(sale.picking_ids.state, 'done')
        self.assertEqual(sale.state, 'sale')
        self.assertTrue(sale.invoice_ids)
        self.assertEqual(sale.amount_total, 12100)
        self.assertEqual(self.team.get_actual_total_cash(), 12100)

    def test_action_confirm_and_pay_service_product(self):
        if not self.l10n_installed:
            self.skipTest('l10n_es module not installed')
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        self.assertEqual(self.team.get_actual_total_cash(), 0)
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
            ],
        })
        sale.session_pay(
            amount=sale.amount_total,
            payment_journal=sale.team_id.cash_payment_journal_id)
        self.assertEqual(sale.state, 'sale')
        self.assertTrue(sale.invoice_ids)
        self.assertEqual(sale.invoice_ids.state, 'posted')
        self.assertEqual(self.team.get_actual_total_cash(), 12100)
        self.assertEqual(session.balance_end, 12100)

    def test_session_with_sale_and_refund(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        session.action_open()
        self.assertEqual(self.team.get_actual_total_cash(), 0)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'session_id': session.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ],
        })
        wizard = self.env['sale.order.payment'].create({
            'sale_id': sale.id,
            'journal_id': journal.id,
        })
        wizard.amount = sale.amount_total
        wizard.action_confirm()
        self.assertEqual(session.balance_end, sale.amount_total)
        self.assertEqual(sale.state, 'sale')
        invoice = sale.invoice_ids
        self.assertEqual(len(sale.invoice_ids), 1)
        self.assertEqual(sale.invoice_ids.state, 'posted')
        reversal_wizard = self.env['account.move.reversal'].with_context(
            active_model='account.move',
            active_ids=invoice.ids
        ).create({
            'refund_method': 'refund',
            'reason': 'Total refund',
            'journal_id': invoice.journal_id.id,
        })
        reversal_result = reversal_wizard.reverse_moves()
        refund_invoice = self.env['account.move'].browse(
            reversal_result['res_id'])
        refund_invoice.action_post()
        self.assertEqual(refund_invoice.state, 'posted')
        self.assertEqual(1, len(invoice.reversal_move_id))
        refund_invoice = invoice.reversal_move_id[0]
        payment_method = self.env['account.payment.method'].search([
            ('payment_type', '=', 'outbound'),
        ], limit=1)
        payment = self.env['account.payment'].create({
            'payment_type': 'outbound',
            'partner_type': 'customer',
            'partner_id': refund_invoice.partner_id.id,
            'amount': refund_invoice.amount_total,
            'date': fields.Date.today(),
            'payment_method_id': payment_method.id,
            'journal_id': journal.id,
            'sale_session_id': session.id,
            'ref': refund_invoice.name,
        })
        payment.action_post()
        partner_account = (
            refund_invoice.partner_id.property_account_receivable_id)
        lines_to_reconcile = (
            refund_invoice.line_ids + payment.line_ids).filtered(
                lambda line: line.account_id == partner_account
        )
        lines_to_reconcile.reconcile()
        self.assertEqual(session.balance_start, 0)
        self.assertEqual(session.balance_end, 0)

    def test_session_mismatch(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        self.assertEqual(session.state, 'draft')
        session.action_open()
        self.assertEqual(session.state, 'open')
        journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        session.register_payment(self.partner, journal, 100)
        self.assertEqual(self.team.get_actual_total_cash(), 100)
        self.assertEqual(session.balance_start, 0)
        self.assertEqual(session.balance_end, 100)
        action = session.action_close()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEqual(session.state, 'close')
        self.assertEqual(session.balance_start, 0)
        self.assertEqual(session.balance_end, 100)
        self.assertEqual(session.total_cash, 100)
        self.assertEqual(session.close_cash_count_mismatch, 0)
        self.assertEqual(self.team.get_actual_total_cash(), 100)

    def test_close_session_with_cash_count_diff(self):
        payment_term = self.env['account.payment.term'].create({
            'name': 'Test Payment term',
        })
        self.partner.property_payment_term_id = payment_term.id
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        self.assertEqual(self.team.get_actual_total_cash(), 0)
        self.team.write({
            'invoice_journal_ids': [(6, 0, [self.invoice_journal.id])],
            'cash_payment_journal_id': self.cash_journal.id,
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
            ],
        })
        wizard = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': sale.id,
            'journal_id': self.cash_journal.id,
        })
        wizard.amount = 250
        wizard._compute_amount()
        self.assertEqual(sale.amount_total, 150)
        self.assertEqual(wizard.amount, 250)
        self.assertEqual(wizard.amount_total, 150)
        self.assertEqual(wizard.amount_change, 100)
        wizard.action_pay()
        self.assertEqual(self.team.get_actual_total_cash(), 150)
        self.assertEqual(wizard.session_id, session)
        cash_payments = session.payment_ids.filtered(
            lambda p: p.journal_id.type == 'cash')
        self.assertEqual(cash_payments.amount, 150)
        action = session.action_close()
        self.assertEqual(
            action['res_model'], 'sale.session.wizard_cash_count')
        wizard = self.env[action['res_model']].browse(action['res_id'])
        cash_count_ids = wizard.journal_cash_count_ids
        self.assertEqual(len(cash_count_ids), 1)
        self.assertEqual(len(cash_count_ids.line_ids), 2)
        line = cash_count_ids.line_ids[0]
        line.quantity = 3
        self.assertEqual(cash_count_ids[0].amount_total, 30)
        action = wizard.action_confirm()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEqual(session.balance_start, 0)
        self.assertEqual(session.state, 'close')
        self.assertEqual(len(session.open_cash_count_ids), 0)
        close_cash_counts = session.close_cash_count_ids
        self.assertEqual(len(close_cash_counts), 1)
        self.assertEqual(len(close_cash_counts.cash_count_line_ids), 2)
        self.assertEqual(session.open_cash_count_total, 0)
        self.assertEqual(session.close_cash_count_total, 30)
        self.assertTrue(session.mismatch_close_move_ids)
        self.assertEqual(session.mismatch_close_move_ids.state, 'draft')
        session.mismatch_close_move_ids.action_post()
        self.assertEqual(session.mismatch_close_move_ids.state, 'posted')
        self.assertEqual(session.total_cash, 150)
        self.assertEqual(session.close_cash_count_mismatch, 120)
        self.assertEqual(
            sum(session.mismatch_close_move_ids.line_ids.mapped('debit')), 120)
        session.action_revert_to_open()
        self.assertFalse(session.mismatch_close_move_ids)
        self.assertEqual(session.state, 'open')
        self.assertEqual(session.total_payment_cash, 150)
        self.assertEqual(session.total_cash, 150)
        self.assertEqual(session.close_cash_count_mismatch, 120)
        session.amount_send = 10
        session.action_unlink_close_cash_counts()
        action = session.action_close()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        cash_count_ids = wizard.journal_cash_count_ids
        line = cash_count_ids.line_ids[0]
        line.quantity = 15
        self.assertEqual(cash_count_ids.amount_total, 150)
        action = wizard.action_confirm()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.amount_send = 50
        wizard.action_confirm()
        internal_move = self.env['account.move'].create({
            'journal_id': self.cash_journal.id,
            'date': fields.Date.today(),
            'line_ids': [
                (0, 0, {
                    'account_id': self.cash_journal.default_account_id.id,
                    'debit': 0,
                    'credit': 50,
                }),
                (0, 0, {
                    'account_id': self.bank_journal.default_account_id.id,
                    'debit': 50,
                    'credit': 0,
                }),
            ],
        })
        internal_move.action_post()
        self.assertEqual(session.state, 'close')
        self.team.cash_count_type = 'open-close'
        session2 = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        self.assertEqual(session2.previous_id, session)
        action = session2.action_open()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        cash_count_ids = wizard.journal_cash_count_ids
        line = cash_count_ids.line_ids[0]
        self.assertEqual(len(cash_count_ids.line_ids), 2)
        line = cash_count_ids.line_ids[0]
        line.quantity = 6
        wizard.action_confirm()
        self.assertEqual(cash_count_ids.amount_total, 60)
        self.assertEqual(session2.open_cash_count_total, 60)
        self.assertEqual(session2.open_cash_count_mismatch, -40)
        self.assertEqual(session2.state, 'open')

    def test_close_session_with_cash_count_diff_multiple_cash_journals(self):
        if not self.l10n_installed:
            self.skipTest('l10n_es module not installed')
        payment_term = self.env['account.payment.term'].create({
            'name': 'Test Payment term',
        })
        self.partner.property_payment_term_id = payment_term.id
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        self.assertEqual(self.team.get_actual_total_cash(), 0)
        cash_journals = self.env['account.journal'].search([
            ('type', '=', 'cash'),
            ('company_id', '=', self.team.company_id.id),
        ])
        self.assertEqual(len(cash_journals), 2)
        self.team.write({
            'invoice_journal_ids': [(6, 0, [self.invoice_journal.id])],
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
            ],
        })
        wizard = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': sale_1.id,
            'journal_id': cash_journals[0].id,
        })
        wizard.amount = 250
        wizard._compute_amount()
        self.assertEqual(sale_1.amount_total, 150)
        self.assertEqual(wizard.amount, 250)
        self.assertEqual(wizard.amount_total, 150)
        self.assertEqual(wizard.amount_change, 100)
        wizard.action_pay()
        self.assertEqual(self.team.get_actual_total_cash(), 150)
        self.assertEqual(wizard.session_id, session)
        cash_payments = session.payment_ids.filtered(
            lambda p: p.journal_id.type == 'cash')
        self.assertEqual(cash_payments.amount, 150)
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
            ],
        })
        wizard = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': sale_2.id,
            'journal_id': cash_journals[1].id,
        })
        wizard.amount = 100
        wizard._compute_amount()
        self.assertEqual(sale_2.amount_total, 50)
        self.assertEqual(wizard.amount, 100)
        self.assertEqual(wizard.amount_total, 50)
        self.assertEqual(wizard.amount_change, 50)
        wizard.action_pay()
        self.assertEqual(self.team.get_actual_total_cash(), 200)
        self.assertEqual(wizard.session_id, session)
        cash_payments = session.payment_ids.filtered(
            lambda p: p.journal_id.type == 'cash')
        self.assertEqual(len(cash_payments), 2)
        self.assertEqual(sum(cash_payments.mapped('amount')), 200)
        action = session.action_close()
        self.assertEqual(
            action['res_model'], 'sale.session.wizard_cash_count')
        wizard = self.env[action['res_model']].browse(action['res_id'])
        cash_count_ids = wizard.journal_cash_count_ids
        self.assertEqual(len(cash_count_ids), 2)
        self.assertEqual(
            cash_count_ids[0].journal_id, cash_journals[0])
        self.assertEqual(
            cash_count_ids[1].journal_id, cash_journals[1])
        self.assertEqual(len(cash_count_ids[0].line_ids), 2)
        line = cash_count_ids[0].line_ids[0]
        line.quantity = 3
        self.assertEqual(cash_count_ids[0].amount_total, 30)
        action = wizard.action_confirm()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEqual(session.balance_start, 0)
        self.assertEqual(session.state, 'close')
        self.assertEqual(len(session.open_cash_count_ids), 0)
        close_cash_counts = session.close_cash_count_ids
        self.assertEqual(len(close_cash_counts), 2)
        self.assertEqual(
            len(close_cash_counts.mapped('cash_count_line_ids')), 4)
        self.assertEqual(session.open_cash_count_total, 0)
        self.assertEqual(session.close_cash_count_total, 30)
        self.assertTrue(session.mismatch_close_move_ids)
        self.assertEqual(True, all(
            mv.state == 'draft' for mv in session.mismatch_close_move_ids))
        session.mismatch_close_move_ids.action_post()
        self.assertEqual(True, all(
            mv.state == 'posted' for mv in session.mismatch_close_move_ids))
        self.assertEqual(session.total_cash, 200)
        self.assertEqual(session.close_cash_count_mismatch, 170)
        self.assertEqual(
            sum(session.mismatch_close_move_ids.mapped('line_ids.debit')), 170)
        mv_close_mismatch_1 = session.mismatch_close_move_ids[0]
        mv_close_mismatch_2 = session.mismatch_close_move_ids[1]
        self.assertEqual(
            sum(mv_close_mismatch_1.line_ids.mapped('debit')), 120)
        self.assertEqual(
            sum(mv_close_mismatch_2.line_ids.mapped('debit')), 50)
        self.assertEqual(mv_close_mismatch_1.journal_id, cash_journals[0])
        self.assertEqual(mv_close_mismatch_2.journal_id, cash_journals[1])
        session.action_revert_to_open()
        self.assertFalse(session.mismatch_close_move_ids)
        self.assertEqual(session.state, 'open')
        self.assertEqual(session.total_payment_cash, 200)
        self.assertEqual(session.total_cash, 200)
        self.assertEqual(session.close_cash_count_mismatch, 170)
        session.amount_send = 10
        session.action_unlink_close_cash_counts()
        action = session.action_close()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        cash_count_ids = wizard.journal_cash_count_ids
        self.assertEqual(len(cash_count_ids), 2)
        self.assertEqual(
            cash_count_ids[0].journal_id, cash_journals[0])
        self.assertEqual(
            cash_count_ids[1].journal_id, cash_journals[1])
        self.assertEqual(len(cash_count_ids[0].line_ids), 2)
        line = cash_count_ids[0].line_ids[0]
        line.quantity = 15
        self.assertEqual(cash_count_ids[0].amount_total, 150)
        action = wizard.action_confirm()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.amount_send = 50
        wizard.action_confirm()
        internal_move = self.env['account.move'].create({
            'journal_id': self.cash_journal.id,
            'date': fields.Date.today(),
            'line_ids': [
                (0, 0, {
                    'account_id': self.cash_journal.default_account_id.id,
                    'debit': 0,
                    'credit': 50,
                }),
                (0, 0, {
                    'account_id': self.bank_journal.default_account_id.id,
                    'debit': 50,
                    'credit': 0,
                }),
            ],
        })
        internal_move.action_post()
        self.assertEqual(session.state, 'close')
        self.team.cash_count_type = 'open-close'
        session2 = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        self.assertEqual(session2.previous_id, session)
        action = session2.action_open()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        cash_count_ids = wizard.journal_cash_count_ids
        self.assertEqual(len(cash_count_ids), 2)
        self.assertEqual(
            cash_count_ids[0].journal_id, cash_journals[0])
        self.assertEqual(
            cash_count_ids[1].journal_id, cash_journals[1])
        line = cash_count_ids[0].line_ids[0]
        line.quantity = 6
        wizard.action_confirm()
        self.assertEqual(cash_count_ids[0].amount_total, 60)
        self.assertEqual(session2.open_cash_count_total, 60)
        self.assertEqual(session2.open_cash_count_mismatch, -90)
        self.assertEqual(session2.state, 'open')

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
        self.assertEqual(session3.previous_id, session2)

    def test_product_with_required_lot_action_confirm(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        self.assertEqual(session.state, 'draft')
        session.action_open()
        self.team.write({
            'invoice_journal_ids': [(6, 0, [self.invoice_journal.id])],
            'cash_payment_journal_id': self.cash_journal.id,
            'cash_money_values': '10,20',
            'cash_count_type': 'close',
        })
        self.product.tracking = 'serial'
        lot = self.env['stock.lot'].create({
            'name': 'Test lot',
            'product_id': self.product.id,
        })
        self._stock_inventory_adjust(self.product, 1, lot=lot)
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
            ],
        })
        wizard = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': sale.id,
            'journal_id': self.cash_journal.id,
        })
        wizard.amount = 150
        action = wizard.action_confirm()
        self.assertNotIn('sale.order.confirm_select_lot', action)
        self.assertEqual(action['type'], 'ir.actions.act_window_close')
        self.assertEqual(sale.picking_ids.state, 'assigned')

    def test_product_with_required_lot_action_credit(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        self.assertEqual(session.state, 'draft')
        session.action_open()
        self.team.write({
            'invoice_journal_ids': [(6, 0, [self.invoice_journal.id])],
            'cash_payment_journal_id': self.cash_journal.id,
            'cash_money_values': '10,20',
            'cash_count_type': 'close',
        })
        self._stock_inventory_adjust(self.product, 0)
        self.product.tracking = 'serial'
        lot = self.env['stock.lot'].create({
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
            ],
        })
        wizard = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': sale.id,
            'journal_id': self.cash_journal.id,
        })
        wizard.amount = 150
        self.assertEqual(wizard.step, 0)
        self.assertEqual(len(wizard.line_ids), 1)
        wizard.line_ids[0].lot_id = lot.id

        def get_product_qty_available_with_lot():
            return self.env['product.product'].with_context(
                lot_id=lot.id).browse(self.product.id).qty_available

        self.assertEqual(get_product_qty_available_with_lot(), 0)
        wizard = wizard.with_context(
            active_model='sale.order.confirm_and_pay', active_id=wizard.id)
        with self.assertRaises(UserError):
            with self.env.cr.savepoint():
                wizard.action_credit()
        self._stock_inventory_adjust(self.product, 1, lot=lot)
        self.assertEqual(self.product.qty_available, 1)
        self.assertEqual(get_product_qty_available_with_lot(), 1)
        action = wizard.action_credit()
        self.assertEqual(self.product.qty_available, 0)
        self.assertEqual(get_product_qty_available_with_lot(), 0)
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(sale.picking_ids.state, 'done')

    def test_sale_session_cancel_balance_end(self):
        if not self.l10n_installed:
            self.skipTest('l10n_es module not installed')
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        self.assertEqual(self.team.get_actual_total_cash(), 0)
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
            ],
        })
        sale.session_pay(
            amount=sale.amount_total,
            payment_journal=sale.team_id.cash_payment_journal_id)
        self.assertEqual(sale.state, 'sale')
        self.assertTrue(sale.invoice_ids)
        self.assertEqual(sale.invoice_ids.state, 'posted')
        self.assertEqual(self.team.get_actual_total_cash(), 12100)
        self.assertEqual(session.balance_end, 12100)
        invoice = sale.invoice_ids
        self.assertEqual(len(sale.invoice_ids), 1)
        self.assertEqual(sale.invoice_ids.state, 'posted')
        reversal_wizard = self.env['account.move.reversal'].with_context(
            active_model='account.move',
            active_ids=invoice.ids
        ).create({
            'refund_method': 'refund',
            'reason': 'Total refund',
            'journal_id': invoice.journal_id.id,
        })
        reversal_result = reversal_wizard.reverse_moves()
        refund_invoice = self.env['account.move'].browse(
            reversal_result['res_id'])
        refund_invoice.action_post()
        self.assertEqual(refund_invoice.state, 'posted')
        self.assertEqual(1, len(invoice.reversal_move_id))
        refund_invoice = invoice.reversal_move_id[0]
        payment_method = self.env['account.payment.method'].search([
            ('payment_type', '=', 'outbound'),
        ], limit=1)
        payment = self.env['account.payment'].create({
            'payment_type': 'outbound',
            'partner_type': 'customer',
            'partner_id': refund_invoice.partner_id.id,
            'amount': refund_invoice.amount_total,
            'date': fields.Date.today(),
            'payment_method_id': payment_method.id,
            'journal_id': journal.id,
            'sale_session_id': session.id,
            'ref': refund_invoice.name,
        })
        payment.action_post()
        partner_account = (
            refund_invoice.partner_id.property_account_receivable_id)
        lines_to_reconcile = (
            refund_invoice.line_ids + payment.line_ids).filtered(
                lambda line: line.account_id == partner_account
        )
        lines_to_reconcile.reconcile()
        self.assertEqual(session.balance_start, 0)
        self.assertEqual(session.balance_end, 0)
        self.assertEqual(session.balance_end, 0)
        for invoice in sale.invoice_ids:
            self.assertEqual(invoice.state, 'posted')

    def test_sale_confirm_user_error_without_stock(self):
        inventory = self.env['stock.quant'].search([
            ('product_id', '=', self.product.id),
        ])
        inventory.inventory_quantity = 0
        inventory.action_apply_inventory()
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        self.assertEqual(self.team.get_actual_total_cash(), 0)
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
            ],
        })
        available_qty = self.env['stock.quant']._get_available_quantity(
            self.product, self.stock_location)
        self.assertTrue(sale.order_line[0].product_uom_qty > available_qty)
        with self.assertRaises(UserError) as result:
            sale.session_pay(
                amount=sale.amount_total,
                payment_journal=sale.team_id.cash_payment_journal_id)
        self.assertEqual(
            result.exception.args[0],
            '%s units of the product %s are ordered but '
            'only %s units in stock' % (
                sale.order_line[0].product_uom_qty, self.product.name,
                available_qty))

    def test_sale_confirm_user_error_invoices_already_created(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        self.assertEqual(self.team.get_actual_total_cash(), 0)
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
                    'product_uom_qty': 100,
                }),
            ],
        })
        session_confirm_wiz = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': sale.id,
            'journal_id': self.cash_journal.id,
        })
        session_confirm_wiz.action_confirm()
        ctx = {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'sale.order',
            'active_ids': sale.ids,
            'active_id': sale.id,
        }
        wizard = self.env[
            'sale.advance.payment.inv'].with_context(ctx).create({
                'advance_payment_method': 'percentage',
                'amount': 50,
            })
        wizard.create_invoices()
        self.assertTrue(sale.invoice_ids)
        session_confirm_wiz = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': sale.id,
            'journal_id': self.cash_journal.id,
            'amount': sale.amount_total,
        })
        session_confirm_wiz._compute_amount()
        with self.assertRaises(UserError) as result:
            session_confirm_wiz.action_pay()
        self.assertIn('Invoices already exist', result.exception.args[0])

    def test_sale_confirm_user_error_return_picking(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        self.assertEqual(self.team.get_actual_total_cash(), 0)
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
                    'product_uom_qty': 100,
                }),
            ],
        })
        session_confirm_wiz = self.env['sale.order.confirm_and_pay'].create({
            'sale_id': sale.id,
            'journal_id': self.cash_journal.id,
        })
        session_confirm_wiz.action_confirm()
        picking = sale.picking_ids
        picking.action_confirm()
        picking.move_line_ids.qty_done = 100
        picking.button_validate()
        self.assertEqual(picking.state, 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_model='stock.picking', active_ids=picking.ids,
            active_id=picking.id)
        return_picking = return_picking.create({})
        return_picking._onchange_picking_id()
        return_picking.product_return_moves.quantity = 100
        return_picking.create_returns()
        picking_ret = sale.picking_ids.filtered(lambda p: p.state != 'done')
        picking_ret.action_confirm()
        picking_ret.move_line_ids.qty_done = 100
        picking_ret.button_validate()
        with self.assertRaises(UserError) as result:
            session_confirm_wiz.action_pay()
        self.assertIn(
            'deliveries already exist and are done but not all products are '
            'delivered', result.exception.args[0])

    def test_confirm_with_current_sale_session(self):
        self.team.require_sale_session = False
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 1,
                    'product_uom_qty': 100,
                }),
            ],
        })
        sale.action_confirm()
        self.assertFalse(sale.session_id)
        self.assertEqual(sale.state, 'sale')
        self.env['crm.team.member'].create({
            'crm_team_id': self.team.id,
            'user_id': self.env.user.id,
        })
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        self.team.cash_payment_journal_id = journal.id
        action = sale.confirm_current_sale_session()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.write({
            'journal_id': self.cash_journal.id,
            'amount': sale.amount_total,
        })
        wizard._compute_amount()
        wizard.action_pay()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(sale.session_id, session)
        self.assertEqual(sale.invoice_ids.state, 'posted')
        self.assertEqual(sale.picking_ids.state, 'done')

    def test_confirm_with_current_sale_session_already_delivered(self):
        self.team.require_sale_session = False
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 1,
                    'product_uom_qty': 100,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(1, len(sale.picking_ids))
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity_done = move.product_uom_qty
        picking._action_done()
        self.assertEqual(picking.state, 'done')
        self.assertFalse(sale.session_id)
        self.assertEqual(sale.state, 'sale')
        self.env['crm.team.member'].create({
            'crm_team_id': self.team.id,
            'user_id': self.env.user.id,
        })
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        journal = self.env['account.journal'].search([
            ('type', '=', 'cash'),
        ], limit=1)
        self.team.cash_payment_journal_id = journal.id
        action = sale.confirm_current_sale_session()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.write({
            'journal_id': self.cash_journal.id,
            'amount': sale.amount_total,
        })
        wizard._compute_amount()
        wizard.action_pay()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(sale.session_id, session)
        self.assertEqual(sale.invoice_ids.state, 'posted')
        self.assertEqual(1, len(sale.picking_ids))
        self.assertEqual(sale.picking_ids.state, 'done')

    def test_error_confirm_with_current_sale_session_picking_canceled(self):
        self.team.require_sale_session = False
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 1,
                    'product_uom_qty': 100,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(1, len(sale.picking_ids))
        picking = sale.picking_ids[0]
        picking.action_cancel()
        self.assertEqual(picking.state, 'cancel')
        self.assertFalse(sale.session_id)
        self.assertEqual(sale.state, 'sale')
        self.env['crm.team.member'].create({
            'crm_team_id': self.team.id,
            'user_id': self.env.user.id,
        })
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        journal = self.env['account.journal'].search([
            ('type', '=', 'cash'),
        ], limit=1)
        self.team.cash_payment_journal_id = journal.id
        with self.assertRaises(UserError) as result:
            sale.confirm_current_sale_session()
            self.assertIn(
                'Product deliveries already exist but are canceled',
                result.exception.args[0])

    def test_error_confirm_with_current_sale_session_partially_delivered(self):
        self.team.require_sale_session = False
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 2,
                    'product_uom_qty': 100,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(1, len(sale.picking_ids))
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity_done = 1
        picking._action_done()
        self.assertEqual(picking.state, 'done')
        self.assertFalse(sale.session_id)
        self.assertEqual(sale.state, 'sale')
        self.env['crm.team.member'].create({
            'crm_team_id': self.team.id,
            'user_id': self.env.user.id,
        })
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        session.action_open()
        journal = self.env['account.journal'].search([
            ('type', '=', 'cash'),
        ], limit=1)
        self.team.cash_payment_journal_id = journal.id
        with self.assertRaises(UserError) as result:
            sale.confirm_current_sale_session()
            self.assertIn(
                'Product deliveries already exist and are done but not all '
                'products are delivered',
                result.exception.args[0])
