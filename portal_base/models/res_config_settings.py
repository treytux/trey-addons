###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    edit_portal_details = fields.Boolean(
        string='Edit Portal Details',
        config_parameter='portal_base.edit_portal_details',
    )
