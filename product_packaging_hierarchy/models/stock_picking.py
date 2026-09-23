###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def put_in_pack_hierarchy(self):
        form_view = self.env.ref(
            'product_packaging_hierarchy.stock_quant_package_hierarchy_view')
        return {
            'name': _('Package hierarchy'),
            'res_model': 'stock.quant.package.hierarchy',
            'type': 'ir.actions.act_window',
            'views': [(form_view.id, 'form')],
            'view_mode': 'form',
            'target': 'new',
        }
