###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    block_missing_analytic_invoices = fields.Boolean(
        string='Block invoices validation without analytic',
        config_parameter='account_analytic_exception.block_missing_analytic',
        help='If enabled, invoices with lines without analytic '
             'account/distribution cannot be validated.'
    )
