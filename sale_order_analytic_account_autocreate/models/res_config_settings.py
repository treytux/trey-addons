###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    autocreate_sale_analytic_account = fields.Boolean(
        related='company_id.autocreate_sale_analytic_account',
        readonly=False,
    )
