###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import datetime

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestProjectEmailCron(TransactionCase):
    def setUp(self):
        super().setUp()
        self.projects_obj = self.env['project.project']
        self.mail_obj = self.env['mail.mail']
        self.analytic_account1 = self.env['account.analytic.account'].create({
            'name': 'Test Analytic Account',
        })
        self.analytic_account2 = self.env['account.analytic.account'].create({
            'name': 'Test Analytic Account - 2',
        })
        self.partner1 = self.env.ref('base.res_partner_12')
        self.partner2 = self.env.ref('base.res_partner_2')
        uom_id = self.env.ref('uom.product_uom_hour').id
        categ_id = self.env['product.category'].search([
            ('name', '=', 'Services')], limit=1).id
        contract_template = self.env['contract.template'].create({
            'name': 'Mantenimiento',
            'contract_type': 'sale',
        })
        self.product = self.env['product.product'].create({
            'name': 'Maintenance',
            'type': 'service',
            'uom_id': uom_id,
            'uom_po_id': uom_id,
            'categ_id': categ_id,
            'is_contract': True,
            'property_contract_template_id': contract_template.id,
            'recurring_rule_type': 'monthly',
            'is_auto_renew': True,
            'auto_renew_interval': 1,
            'auto_renew_rule_type': 'monthly',
            'list_price': 20,
        })

    def create_project(self, partner, account):
        self.env['project.project'].create({
            'name': 'Test Project',
            'allow_timesheets': True,
            'partner_id': partner.id,
            'unit_balance_display': 'effective',
            'analytic_account_id': account.id,
            'date_start': datetime.date.today(),
        })

    def make_billable(self, project):
        start_date = datetime.date.today()
        end_date = start_date + datetime.timedelta(30)
        contract = self.env['contract.contract'].create({
            'name': 'Maintenance',
            'partner_id': project.partner_id.id,
            'contract_line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'quantity': 200,
                    'uom_id': self.product.uom_id.id,
                    'name': 'Test',
                    'is_auto_renew': True,
                    'recurring_interval': 1,
                    'recurring_rule_type': 'monthly',
                    'auto_renew_interval': 1,
                    'auto_renew_rule_type': 'monthly',
                    'date_start': start_date,
                    'date_end': end_date,
                })
            ]

        })
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner1.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 33.33,
                    'product_uom_qty': 200}),
            ]
        })
        project.write({
            'sale_order_id': sale_order.id,
            'sale_line_id': sale_order.order_line[0].id,
        })
        project.sale_line_id.contract_id = contract.id

    def set_params(self):
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('project_project.email_cron', 26)

    def mail_count(self):
        mails = len(self.mail_obj.search([]))
        return mails

    def test_project_maintenance_email_cron_raises(self):
        with self.assertRaises(UserError) as result:
            self.projects_obj.send_maintenance_notification_mail_alert()
        self.assertIn('General Settings', result.exception.name)
        self.set_params()
        with self.assertRaises(UserError) as result:
            self.projects_obj.send_maintenance_notification_mail_alert()
        self.assertIn('There are no projects', result.exception.name)

    def test_project_maintenance_email_cron(self):
        projects = self.projects_obj.get_projects()
        self.assertEqual(len(projects), 0)
        self.create_project(self.partner1, self.analytic_account1)
        projects = self.projects_obj.get_projects()
        self.assertEqual(len(projects), 1)
        self.set_params()
        self.assertEqual(self.mail_count(), 0)
        self.projects_obj.send_maintenance_notification_mail_alert()
        self.assertEqual(self.mail_count(), 1)
        mail = self.mail_obj.search([], limit=1)
        self.assertIn('maintenance you have with our company', mail.body_html)

    def test_project_maintenance_email_cron_contract(self):
        projects = self.projects_obj.get_projects()
        self.assertEqual(len(projects), 0)
        self.create_project(self.partner1, self.analytic_account1)
        projects = self.projects_obj.get_projects()
        self.assertEqual(len(projects), 1)
        self.make_billable(projects)
        self.set_params()
        self.assertEqual(self.mail_count(), 0)
        self.projects_obj.send_maintenance_notification_mail_alert()
        self.assertEqual(self.mail_count(), 1)
        mail = self.mail_obj.search([], limit=1)
        text = 'maintenance contract you have with our company'
        self.assertIn(text, mail.body_html)
