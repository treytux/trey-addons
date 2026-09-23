###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import calendar
import datetime

from odoo import _, models
from odoo.exceptions import UserError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    def get_default_email(self):
        config_parameter = self.env['ir.config_parameter']
        email_id = config_parameter.get_param('project_project.email_cron')
        email = self.env['res.partner'].browse(int(email_id)).email
        return email

    def get_email_template(self):
        return self.env.ref(
            'project_maintenance_email_cron.maintenance_notification_pdf')

    def get_rendered_email(self, name, value):
        template = self.get_email_template()
        values = {
            f'{name}': value
        }
        rendered = template.render(values)
        return rendered

    def get_email_values(self):
        subject = 'Maintenance Notification'
        mail_from = self.env.user.email
        return subject, mail_from

    def send_mail(self, mail_to, body_html):
        subject, mail_from = self.get_email_values()
        mail = self.env['mail.mail'].create({
            'subject': subject,
            'body_html': body_html,
            'email_to': mail_to,
            'email_from': mail_from,
        })
        self.env['mail.mail'].browse(mail.id).send()

    def get_projects(self):
        domain = [
            ('allow_timesheets', '=', True),
            ('unit_balance_display', '!=', 'hidden'),
            ('unit_balance_display', '!=', False),
        ]
        projects = self.env['project.project'].search(domain)
        return projects

    def get_contract_lines(self):
        if self.sale_line_id.contract_id:
            return self.sale_line_id.contract_id.contract_line_ids[0]
        return False

    def get_unit_balance(self):
        return self.analytic_account_id.unit_balance

    def get_monthly_hours(self):
        month = datetime.date.today().month
        year = datetime.date.today().year
        end_month = calendar.monthrange(year, month)[1]
        start_date = datetime.date(year, month, 1)
        end_date = datetime.date(year, month, end_month)
        domain = [
            ('account_id', '=', self.analytic_account_id.id),
            ('date', '>', start_date),
            ('date', '<', end_date),
            ('unit_balance', '<', 0),
        ]
        lines = self.analytic_account_id.line_ids.search(domain)
        return sum([
            abs(line.unit_balance)
            if line.unit_balance < 0 else 0 for line in lines
        ])

    def get_contract_name(self):
        contract_lines = self.get_contract_lines()
        return contract_lines.name if contract_lines else _('No contract')

    def get_renew_interval(self):
        contract_lines = self.get_contract_lines()
        if contract_lines:
            if contract_lines.is_auto_renew:
                renew_interval_type = contract_lines.auto_renew_rule_type
                renew_interval = contract_lines.auto_renew_interval
                if (renew_interval_type == 'daily'):
                    if (renew_interval == 1):
                        return _('1 Day')
                    else:
                        interval = _('Days')
                        renew_interval = f'{renew_interval} {interval}'
                        return renew_interval
                elif (renew_interval_type == 'weekly'):
                    if (renew_interval == 1):
                        return _('1 Week')
                    else:
                        interval = _('Weeks')
                        renew_interval = f'{renew_interval} {interval}'
                        return renew_interval
                elif (renew_interval_type == 'monthly'):
                    if (renew_interval == 1):
                        return _('1 Month')
                    else:
                        interval = _('Months')
                        renew_interval = f'{renew_interval} {interval}'
                        return renew_interval
                elif (renew_interval_type == 'yearly'):
                    if (renew_interval == 1):
                        return _('1 Year')
                    else:
                        interval = _('Years')
                        renew_interval = f'{renew_interval} {interval}'
                        return renew_interval
                else:
                    return _('Unknown')
            else:
                return _('Not auto renew')
        return _('No contract')

    def get_renew_date(self):
        contract_lines = self.get_contract_lines()
        if contract_lines:
            if not contract_lines.last_date_invoiced:
                return _('Unknown')
            return contract_lines.last_date_invoiced
        return _('No contract')

    def send_maintenance_notification_mail_alert(self):
        email = self.get_default_email()
        if not email:
            text = _('You must to configure an email in the General Settings')
            raise UserError(text)
        projects = self.get_projects()
        if not projects:
            text = _('There are no projects')
            raise UserError(text)
        body_html = self.get_rendered_email('projects', projects)
        self.send_mail(email, body_html)
