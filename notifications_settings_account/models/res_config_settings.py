###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    notify_invoice_open = fields.Boolean(
        string='Notify open invoice',
        related='website_id.notify_invoice_open',
        readonly=False,
    )
    notify_invoice_paid = fields.Boolean(
        string='Notify paid invoice',
        related='website_id.notify_invoice_paid',
        readonly=False,
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        config_parameter = self.env['ir.config_parameter'].sudo()
        opened = config_parameter.get_param('website.notify_invoice_open')
        paid = config_parameter.get_param('website.notify_invoice_paid')
        res.update(
            notify_invoice_open=opened,
            notify_invoice_paid=paid,
        )
        return res

    def set_values(self):
        super().set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('website.notify_invoice_open', self.notify_invoice_open)
        set_param('website.notify_invoice_paid', self.notify_invoice_paid)
