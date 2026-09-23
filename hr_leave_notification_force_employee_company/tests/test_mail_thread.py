###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import TransactionCase


class TestMailThread(TransactionCase):

    def setUp(self):
        super().setUp()
        self.employee_company = self.env['res.company'].create({
            'name': 'Employee Company',
        })
        self.forced_company = self.env['res.company'].create({
            'name': 'Forced Company',
        })
        self.employee = self.env['hr.employee'].create({
            'name': 'Employee Company Leave',
            'company_id': self.employee_company.id,
        })
        self.leave_type = self.env['hr.leave.type'].create({
            'name': 'Notification Leave Type',
            'leave_validation_type': 'hr',
            'requires_allocation': 'no',
            'time_type': 'leave',
        })
        self.leave = self.env['hr.leave'].with_context(
            mail_create_nolog=True, mail_notrack=True, tracking_disable=True
        ).create({
            'employee_id': self.employee.id,
            'holiday_status_id': self.leave_type.id,
            'name': 'Notification Leave',
            'request_date_from': '2026-06-16',
            'request_date_to': '2026-06-16',
        })
        self.message = self.env['mail.message'].create({
            'body': 'Notification body',
            'message_type': 'comment',
            'model': self.leave._name,
            'record_name': self.leave.display_name,
            'res_id': self.leave.id,
            'subtype_id': self.env.ref('mail.mt_comment').id,
        })

    def _get_rendering_context(self, record, force_email_company=False):
        msg_vals = {
            'email_add_signature': False,
            'model': record._name,
            'record_name': record.display_name,
            'subtype_id': self.env.ref('mail.mt_comment').id,
            'tracking_value_ids': [],
        }
        return record._notify_by_email_prepare_rendering_context(
            message=self.message, msg_vals=msg_vals,
            force_email_company=force_email_company)

    def test_hr_leave_uses_employee_company(self):
        rendering_context = self._get_rendering_context(self.leave)
        self.assertEqual(rendering_context['company'], self.employee_company)

    def test_hr_leave_keeps_explicit_force_email_company(self):
        rendering_context = self._get_rendering_context(
            self.leave, force_email_company=self.forced_company)
        self.assertEqual(rendering_context['company'], self.forced_company)
