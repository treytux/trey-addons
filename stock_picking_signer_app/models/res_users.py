###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    signed_device = fields.Many2one(
        comodel_name='iot.device',
        string='Signature device',
    )
