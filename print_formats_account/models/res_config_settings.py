###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    invoice_report_group_by = fields.Selection(
        related='company_id.invoice_report_group_by',
        string='Invoice Report Group By',
        readonly=False,
    )
