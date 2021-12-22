###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class Product(models.Model):
    _inherit = 'product.product'

    def action_change_quantity_on_hand(self):
        wiz = self.env['stock.change.product.qty'].create(
            {'product_id': self.id})
        return {
            'name': _('Update quantity on hand'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'stock.change.product.qty',
            'target': 'new',
            'res_id': wiz.id,
            'context': {
                'default_product_id': self.id,
            },
        }
