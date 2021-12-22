###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    invoice_report_group_by = fields.Selection(
        related='company_id.invoice_report_group_by',
        string='Invoice Report Group By',
        readonly=False,
    )

    invoice_report_hide_qty_column = fields.Boolean(
        string='Hide report quantity column',
        related='company_id.invoice_report_hide_qty_column',
        readonly=False,
        help='When this setting is set, hides quantity column in report '
             'invoice when every line quantity is equal to 1',
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        param_obj = self.env['ir.config_parameter']
        invoice_report_hide_qty_column = param_obj.get_param(
            'print_formats_account.invoice_report_hide_qty_column')
        res.update(
            invoice_report_hide_qty_column=invoice_report_hide_qty_column)
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param(
            'print_formats_account.invoice_report_hide_qty_column',
            self.invoice_report_hide_qty_column or '')
