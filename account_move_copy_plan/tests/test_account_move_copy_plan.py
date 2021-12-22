###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo.tests.common import SavepointCase


class TestAccountMoveCopyPlan(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestAccountMoveCopyPlan, cls).setUpClass()
        cls.env.user.groups_id |= cls.env.ref('account.group_account_manager')
        type_revenue = cls.env.ref('account.data_account_type_revenue')
        type_receivable = cls.env.ref('account.data_account_type_receivable')
        cls.account_sale = cls.env['account.account'].create({
            'name': 'Sale',
            'code': 'XX_700',
            'user_type_id': type_revenue.id,
            'reconcile': True,
        })
        cls.account_customer = cls.env['account.account'].create({
            'name': 'Customer',
            'code': 'XX_430',
            'user_type_id': type_receivable.id,
            'reconcile': True,
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Partner test',
            'customer': True,
            'property_account_receivable_id': cls.account_customer.id,
        })
        cls.journal_sale = cls.env['account.journal'].create({
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TSALE',
            'default_debit_account_id': cls.account_sale.id,
            'default_credit_account_id': cls.account_sale.id,
        })
        cls.move = cls.env['account.move'].create({
            'date': fields.Date.today(),
            'type': 'other',
            'journal_id': cls.journal_sale.id,
            'ref': 'TEST account_move_copy_plan addon',
            'line_ids': [
                (0, 0, {
                    'account_id': cls.account_sale.id,
                    'partner_id': cls.partner.id,
                    'credit': 50,
                }),
                (0, 0, {
                    'account_id': cls.account_customer.id,
                    'partner_id': cls.partner.id,
                    'debit': 50,
                }),
            ],
        })
        cls.env.user.lang = False

    def test_moves(self):
        wizard = self.env['account.move.copy_plan'].create({
            'period': 'month',
            'quantity': 12,
        })
        wizard = wizard.with_context(active_ids=[self.move.id])
        moves = wizard.create_moves()
        self.assertEquals(len(moves), 12)
        today = fields.Date.today()
        self.assertEquals(moves[0].date, today + relativedelta(months=1))
