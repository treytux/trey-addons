###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, _


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    def action_show_details(self):
        self.ensure_one()
        view = self.env.ref('product.product_pricelist_item_form_view')
        return {
            'name': _('Detailed Operations'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.pricelist.item',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': dict(
                self.env.context,
                show_pricelist_id=True)}
