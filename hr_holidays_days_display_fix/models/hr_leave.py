###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models
from odoo.addons.resource.models.resource import HOURS_PER_DAY


class HolidaysRequest(models.Model):
    _inherit = 'hr.leave'

    def _get_number_of_days(self, date_from, date_to, employee_id):
        days = super()._get_number_of_days(
            date_from=date_from, date_to=date_to, employee_id=employee_id)
        if not employee_id:
            resource_calendar_id = self.env.user.company_id.resource_calendar_id
            hours = resource_calendar_id.get_work_hours_count(
                date_from, date_to) / (
                resource_calendar_id.hours_per_day or HOURS_PER_DAY)
            days = hours if not self.request_unit_half else hours * 0.5
        return days
