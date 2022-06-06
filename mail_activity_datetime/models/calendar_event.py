###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if len(res.activity_ids) > 0:
            res.activity_ids[0].activity_date = res.start_datetime
            res.activity_ids[0].activity_duration = res.duration
        return res
