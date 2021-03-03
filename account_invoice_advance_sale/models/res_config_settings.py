###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    account_invoice_advance_sale_method = fields.Selection(
        related='company_id.account_invoice_advance_sale_method',
        string='Invoice advance method',
        readonly=False,
        config_parameter='sale.account_invoice_advance_sale_method',
    )
