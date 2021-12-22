###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_print_options_sale(self):
        wiz = self.env['print.options.sale'].create({})
        return {
            'name': _('Print'),
            'type': 'ir.actions.act_window',
            'res_model': 'print.options.sale',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': wiz.id,
            'target': 'new',
        }
