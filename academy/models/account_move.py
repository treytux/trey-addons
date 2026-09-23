###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    activity_id = fields.Many2one(
        comodel_name='academy.activity',
        string='Activity',
    )
    enrollment_id = fields.Many2one(
        comodel_name='academy.enrollment',
        string='Enrollment',
    )
