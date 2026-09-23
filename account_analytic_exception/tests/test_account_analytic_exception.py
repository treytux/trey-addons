###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests.common import TransactionCase


class TestAccountAnalyticException(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.account_move = self._create_move('out_invoice')
        self.analytic_account = self.env['account.analytic.account'].create({
            'name': 'Account one',
            'plan_id': self.env.ref('analytic.analytic_plan_departments').id,
        })
        self.analytic_line = self.env['account.analytic.line'].create({
            'name': 'analytic Lines Tests',
            'account_id': self.analytic_account.id,
        })

    def _create_move(self, move_type):
        return self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': self.partner.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'price_unit': 100,
                    'quantity': 1,
                }),
            ],
        })

    def test_account_move_with_activity(self):
        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'account.move'),
            ('res_id', '=', self.account_move.id),
        ])
        self.assertEqual(len(activities), 0)
        self.account_move.action_post()
        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'account.move'),
            ('res_id', '=', self.account_move.id),
        ])
        self.assertEqual(len(activities), 1)

    def test_account_move_without_activity(self):
        self.account_move.invoice_line_ids.write({
            'analytic_line_ids': [(4, self.analytic_line.id)],
        })
        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'account.move'),
            ('res_id', '=', self.account_move.id),
        ])
        self.assertEqual(len(activities), 0)
        self.assertTrue(self.account_move.invoice_line_ids.analytic_line_ids)
        self.account_move.action_post()
        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'account.move'),
            ('res_id', '=', self.account_move.id),
        ])
        self.assertEqual(len(activities), 0)

    def test_account_move_type_entry(self):
        account = self.env.ref('l10n_generic_coa.1_current_assets')
        move = self.env['account.move'].create({
            'move_type': 'entry',
            'partner_id': self.partner.id,
            'invoice_line_ids': [
                (0, 0, {
                    'account_id': account.id,
                    'name': self.product.name,
                    'debit': 100,
                }),
                (0, 0, {
                    'account_id': account.id,
                    'name': self.product.name,
                    'credit': 100,
                }),
            ],
        })
        self.account_move.action_post()
        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'account.move'),
            ('res_id', '=', move.id),
        ])
        self.assertEqual(len(activities), 0)

    def test_block_missing_analytic_enabled(self):
        self.account_move.action_post()
        self.assertEqual(self.account_move.state, 'posted')
        move = self.account_move.copy()
        self.env['ir.config_parameter'].sudo().set_param(
            'account_analytic_exception.block_missing_analytic', 'True'
        )
        with self.assertRaises(exceptions.UserError):
            move.action_post()
        bill = self._create_move('in_invoice')
        with self.assertRaises(exceptions.UserError):
            bill.action_post()
