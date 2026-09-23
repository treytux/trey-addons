###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_add_bom(self):
        self.ensure_one()
        return {
            'name': _('Add BoM'),
            'type': 'ir.actions.act_window',
            'res_model': 'wiz.sale_import_bom',
            'view_mode': 'form',
            'context': {'default_order_id': self.id},
            'target': 'new',
        }
