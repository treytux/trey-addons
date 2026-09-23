###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import date

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestAcademyInvoiceActivitiesWizard(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'property_account_payable_id': self.env['account.account'].search([
                ('account_type', '=', 'liability_payable'),
            ], limit=1).id,
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'service',
            'lst_price': 1.0,
            'taxes_id': [
                (6, 0, self.env['account.tax'].search([], limit=1).ids)],
            'property_account_income_id': self.env['account.account'].search([
                ('account_type', '=', 'income'),
            ], limit=1).id,
        })
        self.training_plan = self.env['academy.training.plan'].create({
            'name': 'Plan',
            'start_date': date.today(),
            'end_date': date.today(),
            'user_id': self.env.ref('base.user_admin').id,
        })
        self.activity = self.env['academy.activity'].create({
            'name': 'Activity',
            'training_plan_id': self.training_plan.id,
            'user_id': self.env.ref('base.user_admin').id,
            'start_date': date.today(),
            'end_date': date.today(),
            'product_id': self.product.id,
            'invoice_tutors': True,
            'activity_price_reduced': 150,
            'activity_price': 220,
        })
        self.enrollment = self.env['academy.enrollment'].create({
            'training_plan_id': self.training_plan.id,
            'activity_id': self.activity.id,
            'student_id': self.partner.id,
            'start_date': date.today(),
            'end_date': date.today(),
        })

    def test_wizard_creates_invoice_ok(self):
        wizard = self.env['academy.invoice.activities.wizard'].create({
            'name': 'Test Month',
            'date': date.today(),
        })
        self.enrollment.state = 'active'
        wizard = wizard.with_context(
            active_model='academy.activity',
            active_ids=[self.activity.id]
        )
        action = wizard.create_invoices()
        self.assertIn('domain', action)
        invoice = self.env['account.move'].search(action['domain'])
        self.assertEqual(len(invoice), 1)
        self.assertEqual(invoice[0].invoice_date, wizard.date)
        self.assertEqual(
            invoice.amount_untaxed, self.activity.activity_price)
        self.assertEqual(invoice.partner_id, self.partner)
        taxes = self.product.taxes_id
        self.assertEqual(len(invoice.invoice_line_ids.tax_ids), len(taxes))
        for tax in taxes:
            self.assertIn(tax, invoice.invoice_line_ids.tax_ids)

    def test_wizard_skip_no_active_enrollments(self):
        wizard = self.env['academy.invoice.activities.wizard'].create({
            'name': 'Test Month',
            'date': date.today(),
        })
        wizard = wizard.with_context(
            active_model='academy.activity',
            active_ids=[self.activity.id]
        )
        action = wizard.create_invoices()
        self.assertIn('type', action)
        self.assertEqual(action['type'], 'ir.actions.act_window_close')

    def test_wizard_raises_if_no_product(self):
        self.activity.product_id = False
        wizard = self.env['academy.invoice.activities.wizard'].create({
            'name': 'Test Month',
            'date': date.today(),
        })
        self.enrollment.state = 'active'
        wizard = wizard.with_context(
            active_model='academy.activity',
            active_ids=[self.activity.id]
        )
        with self.assertRaises(ValidationError):
            wizard.create_invoices()

    def test_wizard_raises_if_date_out_of_activity_range(self):
        wizard = self.env['academy.invoice.activities.wizard'].create({
            'name': 'Test Month',
            'date': date.today().replace(year=date.today().year + 1),
        })
        self.enrollment.state = 'active'
        wizard = wizard.with_context(
            active_model='academy.activity',
            active_ids=[self.activity.id]
        )
        with self.assertRaises(ValidationError):
            wizard.create_invoices()

    def test_wizard_raises_if_invoices_already_created(self):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_date': date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': 'Test line',
                'quantity': 1.0,
                'price_unit': 1.0,
                'account_id': self.product.property_account_income_id.id,
                'product_id': self.product.id,
                'tax_ids': [(6, 0, self.product.taxes_id.ids)],
            })],
        })
        invoice.action_post()
        self.activity.invoice_ids = [(4, invoice.id)]
        wizard = self.env['academy.invoice.activities.wizard'].create({
            'name': 'Test Month',
            'date': date.today(),
        })
        self.enrollment.state = 'active'
        wizard = wizard.with_context(
            active_model='academy.activity',
            active_ids=[self.activity.id]
        )
        with self.assertRaises(ValidationError):
            wizard.create_invoices()
