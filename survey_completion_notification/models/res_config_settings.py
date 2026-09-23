###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    survey_notify = fields.Boolean(
        string="Notify Survey Completion",
        help="""
            If checked, an email notification will be
            sent to followers when a survey is completed.
        """,
        config_parameter='survey_completion_notification.survey_notify',
    )
