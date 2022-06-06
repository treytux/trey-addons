###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def get_stock_moves_ids(self):
        return self.env['stock.move'].search([
            ('product_tmpl_id', '=', self.id),
        ]).ids

    def action_view_product_template_stock_move(self):
        stock_moves_ids = self.get_stock_moves_ids()
        form_view = self.env.ref('stock.view_move_form')
        tree_view = self.env.ref('stock.view_move_tree')
        search_view = self.env.ref('stock.view_move_search')
        actions_vals = {
            'name': _('Stock moves'),
            'res_model': 'stock.move',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree, form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'domain': [('id', 'in', stock_moves_ids)],
        }
        if len(stock_moves_ids) == 0:
            actions_vals.update({
                'help': _("<p class='o_view_nocontent_smiling_face'>"
                          "There's no stock move</p>"),
            })
        if len(stock_moves_ids) == 1:
            del actions_vals['views']
            actions_vals.update({
                'view_mode': 'form',
                'res_id': stock_moves_ids[0],
            })
        return actions_vals
