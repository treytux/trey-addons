###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_print_options_sale(self):
        wiz = self.env['wiz.print.options.sale'].create({})
        return {
            'name': _('Print'),
            'type': 'ir.actions.act_window',
            'res_model': 'wiz.print.options.sale',
            'view_mode': 'form',
            'res_id': wiz.id,
            'target': 'new',
        }
