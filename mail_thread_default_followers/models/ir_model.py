###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class IrModel(models.Model):
    _inherit = 'ir.model'

    followers_setting = fields.Selection(
        selection=[
            ('default', 'Default'),
            ('none', 'None'),
            ('owner', 'Owner'),
            ('owner_writers', 'Owner and writers'),
            ('owner_partner', 'Owner and partner'),
        ],
        string='Followers settings',
        default='default',
    )
