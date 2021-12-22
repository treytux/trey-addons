###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    is_stock_rotation = fields.Boolean(
        string='Calculate stock rotation',
    )
    rotation_init_date = fields.Date(
        string='Rotation init date',
        required=True,
        default=fields.Date.today(),
    )
    rotation_last_run = fields.Date(
        string='Rotation last run',
    )
