###############################################################################
# For copyright and license notices, see __manifest__.py file
###############################################################################
from odoo import models


class HrHolidaysPublic(models.Model):
    _inherit = "hr.holidays.public"

    def _get_partner_deprecated_employee(self, partner_id, employee_id):
        if partner_id:
            return super()._get_partner_deprecated_employee(partner_id, None)
        return super()._get_partner_deprecated_employee(None, employee_id)
