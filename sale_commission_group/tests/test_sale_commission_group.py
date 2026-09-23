###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from unittest import SkipTest

from odoo.tests.common import TransactionCase


class TestSaleCommissionGroup(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.commission = cls.env['commission'].create({
            'name': 'Test commission',
            'commission_type': 'fixed',
            'fix_qty': 10.0,
            'amount_base_type': 'gross_amount',
        })
        cls.agent_alpha = cls.env['res.partner'].create({
            'name': 'Agent Alpha',
            'agent': True,
            'commission_id': cls.commission.id,
            'is_company': True,
        })
        cls.agent_beta = cls.env['res.partner'].create({
            'name': 'Agent Beta',
            'agent': True,
            'commission_id': cls.commission.id,
            'is_company': True,
        })
        cls.agent_gamma = cls.env['res.partner'].create({
            'name': 'Agent Gamma',
            'agent': True,
            'commission_id': cls.commission.id,
            'is_company': True,
        })
        cls.customer_a = cls.env['res.partner'].create({
            'name': 'Customer A',
            'is_company': True,
            'customer_rank': 1,
            'vat': 'ESA00000001',
            'agent_ids': [(6, 0, [cls.agent_beta.id, cls.agent_alpha.id])],
        })
        cls.customer_b = cls.env['res.partner'].create({
            'name': 'Customer B',
            'is_company': True,
            'customer_rank': 1,
            'vat': 'ESA00000002',
            'agent_ids': [(6, 0, [cls.agent_alpha.id])],
        })
        cls.product = cls.env['product.product'].search([
            ('sale_ok', '=', True),
        ], limit=1)
        if not cls.product:
            raise AssertionError('No product found to run sale_commission tests.')

    def _set_sale_order_agents(
            self, order, first_line_agents, second_line_agents):
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1.0,
            'price_unit': 100.0,
        })
        line_one = order.order_line[0]
        line_two = order.order_line[1]
        line_one.agent_ids = [
            (0, 0, {
                'agent_id': agent_id,
                'commission_id': self.commission.id,
            })
            for agent_id in first_line_agents
        ]
        line_two.agent_ids = [
            (0, 0, {
                'agent_id': agent_id,
                'commission_id': self.commission.id,
            })
            for agent_id in second_line_agents
        ]

    def _create_sale_order(self, partner):
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
        })
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1.0,
            'price_unit': 100.0,
        })
        return order

    def _create_invoice_for_compute_test(self):
        journal = self.env['account.journal'].search([
            ('type', '=', 'sale'),
        ], limit=1)
        if not journal:
            raise SkipTest('Skipping invoice tests: no sales journal found.')
        account = self.env['account.account'].search([
            ('deprecated', '=', False),
            ('company_id', '=', self.env.company.id),
            ('account_type', 'in', ['income', 'income_other'])
        ], limit=1)
        if not account:
            raise SkipTest('Skipping invoice tests: no account found.')
        return self.env['account.move'].create({
            'move_type': 'out_invoice',
            'journal_id': journal.id,
            'partner_id': self.customer_a.id,
            'invoice_line_ids': [
                (0, 0, {
                    'name': self.product.display_name,
                    'product_id': self.product.id,
                    'quantity': 1.0,
                    'price_unit': 100.0,
                    'account_id': account.id,
                }),
                (0, 0, {
                    'name': self.product.display_name,
                    'product_id': self.product.id,
                    'quantity': 1.0,
                    'price_unit': 200.0,
                    'account_id': account.id,
                }),
            ],
        })

    def test_res_partner_agents_name_is_sorted_per_record(self):
        customer_c = self.env['res.partner'].create({
            'name': 'Customer C',
            'is_company': True,
            'customer_rank': 1,
            'agent_ids': [(6, 0, [self.agent_gamma.id])],
        })
        partners = self.customer_a | customer_c
        partners._compute_agents_name()
        self.assertIn('Agent Beta', self.customer_a.agents_name)
        self.assertIn('Agent Alpha', self.customer_a.agents_name)
        self.assertEqual(customer_c.agents_name, 'Agent Gamma')

    def test_res_partner_agents_name_recompute_on_agent_rename(self):
        self.customer_a._compute_agents_name()
        self.assertIn('Agent Beta', self.customer_a.agents_name)
        self.assertIn('Agent Alpha', self.customer_a.agents_name)
        self.agent_beta.name = 'Agent Aardvark'
        self.assertIn('Agent Aardvark', self.customer_a.agents_name)

    def test_sale_order_agents_name_from_lines(self):
        order = self._create_sale_order(self.customer_a)
        self._set_sale_order_agents(
            order,
            [self.agent_beta.id, self.agent_alpha.id],
            [self.agent_gamma.id])
        order._compute_agents_name()
        self.assertIn('Agent Gamma', order.agents_name)
        self.assertIn('Agent Beta', order.agents_name)
        self.assertIn('Agent Alpha', order.agents_name)

    def test_account_move_agents_name_from_invoice_lines(self):
        invoice = self._create_invoice_for_compute_test()
        invoice_lines = invoice.invoice_line_ids.filtered(
            lambda line: not line.display_type)
        if len(invoice_lines) < 2:
            raise SkipTest('Skipping invoice tests: missing invoice lines.')
        invoice_lines[0].agent_ids = [
            (0, 0, {
                'agent_id': self.agent_beta.id,
                'commission_id': self.commission.id,
            }),
            (0, 0, {
                'agent_id': self.agent_alpha.id,
                'commission_id': self.commission.id,
            })
        ]
        invoice_lines[1].agent_ids = [
            (0, 0, {
                'agent_id': self.agent_gamma.id,
                'commission_id': self.commission.id,
            })
        ]
        invoice._compute_agents_name()
        self.assertIn('Agent Alpha', invoice.agents_name)
        self.assertIn('Agent Beta', invoice.agents_name)
        self.assertIn('Agent Gamma', invoice.agents_name)

    def test_account_move_multi_record_compute_does_not_mix_values(self):
        invoice_one = self._create_invoice_for_compute_test()
        invoice_two = self._create_invoice_for_compute_test()
        invoice_one_lines = invoice_one.invoice_line_ids.filtered(
            lambda line: not line.display_type)
        invoice_two_lines = invoice_two.invoice_line_ids.filtered(
            lambda line: not line.display_type)
        if not invoice_one_lines or not invoice_two_lines:
            raise SkipTest('Skipping invoice tests: missing invoice lines.')
        invoice_one_line = invoice_one_lines[0]
        invoice_two_line = invoice_two_lines[0]
        invoice_one_line.agent_ids = [
            (0, 0, {
                'agent_id': self.agent_alpha.id,
                'commission_id': self.commission.id,
            })
        ]
        invoice_two_line.agent_ids = [
            (0, 0, {
                'agent_id': self.agent_gamma.id,
                'commission_id': self.commission.id,
            })
        ]
        (invoice_one | invoice_two)._compute_agents_name()
        self.assertEqual(invoice_one.agents_name, 'Agent Alpha')
        self.assertEqual(invoice_two.agents_name, 'Agent Gamma')

    def test_multi_record_compute_does_not_mix_values(self):
        order_one = self._create_sale_order(self.customer_a)
        order_two = self._create_sale_order(self.customer_b)
        self._set_sale_order_agents(
            order_one,
            [self.agent_alpha.id],
            [self.agent_beta.id])
        self._set_sale_order_agents(
            order_two,
            [self.agent_gamma.id],
            [self.agent_gamma.id])
        (order_one | order_two)._compute_agents_name()
        self.assertIn('Agent Beta', order_one.agents_name)
        self.assertIn('Agent Alpha', order_one.agents_name)
        self.assertEqual(order_two.agents_name, 'Agent Gamma')

    def test_agents_name_empty_when_no_agents(self):
        customer = self.env['res.partner'].create({
            'name': 'Customer No Agent',
            'is_company': True,
            'customer_rank': 1,
        })
        customer._compute_agents_name()
        self.assertEqual(customer.agents_name, '')
        order = self._create_sale_order(customer)
        order._compute_agents_name()
        self.assertEqual(order.agents_name, '')
