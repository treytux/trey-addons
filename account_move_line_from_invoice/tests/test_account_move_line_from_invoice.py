###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from lxml import etree
from odoo.tests import common
from odoo.tools.safe_eval import safe_eval


@common.tagged('post_install', '-at_install')
class TestAccountMoveLineFromInvoice(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
        })
        self.income_account = self.env['account.account'].search([
            ('deprecated', '=', False),
            ('company_id', '=', self.env.company.id),
            ('internal_group', '=', 'income'),
        ], limit=1)
        self.customer_invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Test line',
                'account_id': self.income_account.id,
                'quantity': 1,
                'price_unit': 100.0,
            })],
        })

    def test_invoice_line_count(self):
        self.assertEqual(
            self.customer_invoice.invoice_line_count,
            len(self.customer_invoice.invoice_line_ids))

    def test_action_context_defaults_move(self):
        action = self.env.ref(
            'account_move_line_from_invoice.action_account_move_line')
        context = safe_eval(
            action.context, {'active_id': self.customer_invoice.id})
        self.assertEqual(
            context['default_move_id'], self.customer_invoice.id)

    def test_action_domain_matches_invoice_lines(self):
        action = self.env.ref(
            'account_move_line_from_invoice.action_account_move_line')
        domain = safe_eval(
            action.domain, {'active_id': self.customer_invoice.id})
        lines = self.env['account.move.line'].search(domain)
        self.assertEqual(lines, self.customer_invoice.invoice_line_ids)
        self.assertGreater(
            len(self.customer_invoice.line_ids),
            len(self.customer_invoice.invoice_line_ids))

    def test_create_injects_default_move_id_on_import(self):
        line = self.env['account.move.line'].with_context(
            default_move_id=self.customer_invoice.id).create({
                'name': 'Imported line',
                'account_id': self.income_account.id,
            })
        self.assertEqual(line.move_id, self.customer_invoice)

    def test_shared_journal_items_view_stays_readonly(self):
        readonly_view = self.env.ref('account.view_move_line_tree')
        fields_view = self.env['account.move.line'].get_view(
            readonly_view.id, 'tree')
        arch = etree.fromstring(fields_view['arch'])
        self.assertEqual(arch.get('create'), 'false')
