###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def action_print_options_stock_picking(self):
        wiz = self.env['print.options.stock.picking'].create({})
        return {
            'name': _('Print'),
            'type': 'ir.actions.act_window',
            'res_model': 'print.options.stock.picking',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': wiz.id,
            'target': 'new',
        }
