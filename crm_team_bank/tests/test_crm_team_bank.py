###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestCrmTeamBank(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.company_partner = self.company.partner_id
        self.customer = self.env['res.partner'].create({
            'name': 'Test Customer',
            'customer_rank': 1,
        })
        self.other_partner = self.env['res.partner'].create({
            'name': 'Other Partner',
        })
        self.bank_01 = self.env['res.bank'].create({
            'name': 'Test Bank 01',
            'bic': 'TESTESMMXXX',
        })
        self.bank_02 = self.env['res.bank'].create({
            'name': 'Test Bank 02',
            'bic': 'TESTESBBXXX',
        })
        acc_01 = self._make_unique_iban(1)
        acc_02 = self._make_unique_iban(2)
        acc_03 = self._make_unique_iban(3)
        self.company_bank_01 = self.env['res.partner.bank'].create({
            'partner_id': self.company_partner.id,
            'bank_id': self.bank_01.id,
            'acc_number': acc_01,
        })
        self.company_bank_02 = self.env['res.partner.bank'].create({
            'partner_id': self.company_partner.id,
            'bank_id': self.bank_02.id,
            'acc_number': acc_02,
        })
        self.other_bank_01 = self.env['res.partner.bank'].create({
            'partner_id': self.other_partner.id,
            'bank_id': self.bank_01.id,
            'acc_number': acc_03,
        })
        self.team_multi = self.env['crm.team'].create({
            'name': 'Test Sales Team Multi',
            'company_id': self.company.id,
            'user_id': self.env.ref('base.user_admin').id,
            'bank_account_ids': [
                (6, 0, [self.company_bank_01.id, self.company_bank_02.id]),
            ],
        })
        self.team_single = self.env['crm.team'].create({
            'name': 'Test Sales Team Single',
            'company_id': self.company.id,
            'user_id': self.env.ref('base.user_admin').id,
            'bank_account_ids': [(6, 0, [self.company_bank_01.id])],
        })
        self.team_empty = self.env['crm.team'].create({
            'name': 'Test Sales Team Empty',
            'company_id': self.company.id,
            'user_id': self.env.ref('base.user_admin').id,
        })
        self.pricelist = self.env.ref('product.list0')
        self.customer.property_product_pricelist = self.pricelist

    def _make_unique_iban(self, inc):
        seed = int(datetime.now().timestamp() * 1000000)
        num = (seed + inc) % (10**20)
        return 'TEST%020d' % num

    def _sale_order_vals(self, **overrides):
        vals = {
            'partner_id': self.customer.id,
            'company_id': self.company.id,
            'pricelist_id': self.pricelist.id,
            'team_id': self.team_multi.id,
        }
        vals.update(overrides)
        return vals

    def _get_sale_journal(self):
        return self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', self.company.id),
        ], limit=1)

    def test_crm_team_constraint_bank_accounts_must_belong_to_company_partner(
        self
    ):
        with self.assertRaises(ValidationError):
            self.env['crm.team'].create({
                'name': 'Invalid Team',
                'company_id': self.company.id,
                'user_id': self.env.ref('base.user_admin').id,
                'bank_account_ids': [(6, 0, [self.other_bank_01.id])],
            })

    def test_sale_order_onchange_hides_invalid_and_autoselects_single_account(
        self
    ):
        order = self.env['sale.order'].new(
            self._sale_order_vals(team_id=self.team_multi.id)
        )
        order.partner_bank_id = self.company_bank_02
        order.team_id = self.team_single
        order._onchange_team_id_partner_bank()
        self.assertEqual(
            order.partner_bank_id._origin.id,
            self.company_bank_01.id,
        )
        order.team_id = self.team_empty
        order._onchange_team_id_partner_bank()
        self.assertFalse(order.partner_bank_id)

    def test_sale_order_constraint_team_bank_must_be_allowed(self):
        with self.assertRaises(ValidationError):
            self.env['sale.order'].create(self._sale_order_vals(
                team_id=self.team_single.id,
                partner_bank_id=self.company_bank_02.id,
            ))

    def test_sale_order_prepare_invoice_propagates_partner_bank_id(self):
        order = self.env['sale.order'].create(self._sale_order_vals(
            team_id=self.team_single.id,
            partner_bank_id=self.company_bank_01.id,
        ))
        vals = order._prepare_invoice()
        self.assertEqual(vals.get('partner_bank_id'), self.company_bank_01.id)

    def test_account_move_onchange_autoselects_first_account(self):
        Move = self.env['account.move']
        if 'team_id' not in Move._fields:
            self.skipTest('team_id field not found on account.move')
        move = Move.new({
            'move_type': 'out_invoice',
            'company_id': self.company.id,
            'team_id': self.team_multi.id,
        })
        move._onchange_team_id_partner_bank_domain()
        self.assertIn(
            move.partner_bank_id._origin.id,
            [self.company_bank_01.id, self.company_bank_02.id],
        )
        move.team_id = self.team_single
        move._onchange_team_id_partner_bank_domain()
        self.assertEqual(
            move.partner_bank_id._origin.id,
            self.company_bank_01.id,
        )

    def test_account_move_constraint_team_bank_must_be_allowed(self):
        Move = self.env['account.move']
        if 'team_id' not in Move._fields:
            self.skipTest('team_id field not found on account.move')
        journal = self._get_sale_journal()
        if not journal:
            self.skipTest('No sale journal found for the company')
        with self.assertRaises(ValidationError):
            Move.create({
                'move_type': 'out_invoice',
                'company_id': self.company.id,
                'partner_id': self.customer.id,
                'journal_id': journal.id,
                'team_id': self.team_single.id,
                'partner_bank_id': self.company_bank_02.id,
            })
