###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class FSMActivity(models.Model):
    _inherit = 'fsm.activity'

    time = fields.Float(
        string='Time spent',
        copy=False,
    )
