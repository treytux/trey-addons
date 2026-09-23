###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class IrModelLog(models.Model):
    _inherit = 'ir.model.log'

    website_id = fields.Many2one(
        comodel_name='website',
        string='Website',
    )
