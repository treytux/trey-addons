###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase

_log = logging.getLogger(__name__)


class TestSaleTeamCashCount(TransactionCase):

    def setUp(self):
        super().setUp()
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
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        invoice_journal = self.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1)
        cash_journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        self.team = self.env['crm.team'].create({
            'name': 'Test Sale Team',
            'invoice_journal_ids': [(6, 0, [invoice_journal.id])],
            'default_payment_journal_id': cash_journal.id,
            'require_sale_session': True,
        })

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

    def test_sale_session(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        self.assertTrue(session.name)
        self.assertIn('SS', session.name)
        self.assertEquals(session.open_date.date(), fields.Date.today())
        self.assertEquals(session.close_date, False)
        self.assertEquals(session.validation_date, False)
        session.action_open()
        self.assertEquals(
            session.get_current_sale_session(self.team.id), session)
        with self.assertRaises(ValidationError):
            self.env['sale.session'].create({
                'team_id': self.team.id
            })
        with self.assertRaises(ValidationError):
            session.copy()

    def test_without_sale_session(self):
        invoice_journal = self.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1)
        cash_journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        self.env.user.write({
            'groups_id': [(6, 0, [self.env.ref(
                'sale_session.group_without_sale_session').id])],
        })
        team = self.env['crm.team'].create({
            'name': 'Without sale session',
            'invoice_journal_ids': [(6, 0, [invoice_journal.id])],
            'default_payment_journal_id': cash_journal.id,
            'member_ids': [(6, 0, [self.env.user.id])],
        })
        session = self.env['sale.session'].create({
            'team_id': team.id,
        })
        session.action_open()
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': team.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })
        self.assertFalse(sale.session_id)

    def test_session_with_sales(self):
        with self.assertRaises(UserError):
            sale = self.env['sale.order'].create({
                'partner_id': self.partner.id,
                'team_id': self.team.id,
                'session_id': False,
                'order_line': [
                    (0, 0, {
                        'product_id': self.product.id,
                        'price_unit': 100,
                        'product_uom_qty': 1}),
                ]
            })
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
        self.assertEquals(sale.session_id, session)
        self.assertEquals(session.balance_end, 0)
        sale.action_confirm()
        self.assertEquals(session.balance_end, sale.amount_total)
        self.assertEquals(session.amount_diff, sale.amount_total)
        sale.action_invoice_create()
        sale = sale.copy()
        sale.action_confirm()
        self.assertEquals(session.balance_end, sale.amount_total * 2)
        wizard = self.env['sale.session.close'].create({
            'session_id': session.id,
        })
        wizard.action_confirm()
        self.assertEquals(session.state, 'close')
        self.assertEquals(session.close_date.date(), fields.Date.today())
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
            'balance_start': 100,
        })
        journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        session.action_open()
        sale = sale.copy({'session_id': session.id})
        wizard = self.env['sale.order.payment'].create({
            'sale_id': sale.id,
            'journal_id': journal.id,
            'amount': sale.amount_total,
        })
        wizard.action_confirm()
        self.assertEquals(session.balance_start, 100)
        self.assertEquals(session.balance_end, sale.amount_total + 100)
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.invoice_ids), 1)
        self.assertEquals(sale.invoice_ids.state, 'paid')
        with self.assertRaises(UserError):
            wizard.action_confirm()
        session.state = 'close'
        session.action_validate()
        self.assertEquals(session.validation_date.date(), fields.Date.today())
        new_session = session.copy()
        self.assertEquals(new_session.balance_start, session.balance_end)

    def test_session_payment(self):
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        self.assertTrue(journal)
        payment = session.register_payment(self.partner, journal, 100)
        self.assertEquals(payment.state, 'posted')
        self.assertEquals(len(session.payment_ids), 1)
        self.assertEquals(session.balance_start, 0)
        self.assertEquals(session.balance_end, 100)
        wizard = self.env['sale.session.payment'].create({
            'session_id': session.id,
            'partner_id': self.partner.id,
            'journal_id': journal.id,
            'amount': 50,
        })
        wizard.action_confirm()
        self.assertEquals(len(session.payment_ids), 2)
        self.assertEquals(session.balance_start, 0)
        self.assertEquals(session.balance_end, 150)

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
            lambda l: l.journal_id == bank_journal)
        self.assertEquals(bank_line.amount_total, sale.amount_total)
        session.action_validate()
        self.assertEquals(session.validation_date.date(), fields.Date.today())

    def test_session_open_cash_count(self):
        self.team.cash_money_values = (
            '0.01,0.05,0.10,0.20,0.50,1,2,5,10,20,50,100,200,500')
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        wizard = self.env['sale.session.wizard_cash_count'].create({
            'session_id': session.id,
            'journal_id': journal.id,
            'type': 'open',
        })
        self.assertEquals(wizard.team_id, session.team_id)
        self.assertEquals(len(wizard.line_ids), 14)
        line = wizard.line_ids[0]
        line.quantity = 3
        self.assertEquals(wizard.amount_total, line.value * 3)
        wizard.action_confirm()
        self.assertEquals(len(session.open_cash_count_ids), 14)
        self.assertEquals(len(session.close_cash_count_ids), 0)
        self.assertEquals(session.open_cash_count_total, line.value * 3)
        self.assertEquals(session.close_cash_count_total, 0)

    def test_session_close_wizard(self):
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
        self.assertEquals(wizard.amount_next_session, wizard.balance_end)
        session.team_id.cash_money_balance_start = 10
        wizard = wizard_obj.with_context(new_env=True).create({
            'session_id': session.id,
        })
        self.assertEquals(session.team_id.cash_money_balance_start, 10)
        self.assertEquals(wizard.amount_next_session, 10)
        self.assertEquals(wizard.amount_send, 90)
        wizard.action_confirm()
        self.assertEquals(session.close_date.date(), fields.Date.today())
        session.action_validate()
        self.assertEquals(session.validation_date.date(), fields.Date.today())

    def test_action_confirm_and_pay(self):
        payment_term = self.env['account.payment.term'].create({
            'name': 'Test Payment term',
        })
        self.partner.property_payment_term_id = payment_term.id
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        invoice_journal = self.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1)
        cash_journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        self.team.write({
            'invoice_journal_ids': [(6, 0, [invoice_journal.id])],
            'default_payment_journal_id': cash_journal.id,
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
        sale.session_pay(
            sale.amount_total, sale.team_id.default_payment_journal_id)
        self.assertEquals(sale.picking_ids.state, 'done')
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(sale.invoice_ids.state, 'paid')
        self.assertEquals(len(sale.picking_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertFalse(invoice.payment_term_id)
        self.assertEquals(invoice.payment_ids[0].amount, sale.amount_total)

    def test_action_confirm_and_pay_with_wirzard(self):
        payment_term = self.env['account.payment.term'].create({
            'name': 'Test Payment term',
        })
        self.partner.property_payment_term_id = payment_term.id
        session = self.env['sale.session'].create({
            'team_id': self.team.id
        })
        invoice_journal = self.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1)
        cash_journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        self.team.write({
            'invoice_journal_ids': [(6, 0, [invoice_journal.id])],
            'default_payment_journal_id': cash_journal.id,
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

    def test_action_confirm_and_pay_without_stock(self):
        location = self.env.ref('stock.stock_location_stock')
        inventory = self.env['stock.inventory'].create({
            'name': 'add products for tests',
            'filter': 'product',
            'location_id': location.id,
            'product_id': self.product.id,
            'exhausted': True,
        })
        inventory.action_start()
        inventory.line_ids.write({
            'product_qty': 0,
            'location_id': location.id,
        })
        inventory._action_done()
        session = self.env['sale.session'].create({
            'team_id': self.team.id,
        })
        journal = self.env['account.journal'].search(
            [('type', '=', 'cash')], limit=1)
        self.team.default_payment_journal_id = journal.id
        session.action_open()
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
        sale.session_pay(
            sale.amount_total, sale.team_id.default_payment_journal_id)
        self.assertEquals(sale.picking_ids.state, 'done')
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(sale.invoice_ids.state, 'paid')
        self.assertEquals(len(sale.picking_ids), 1)
