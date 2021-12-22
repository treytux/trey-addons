###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class FSMLocation(models.Model):
    _inherit = 'fsm.location'

    def action_view_sale_order_link(self):
        sale_order_ids = self.sale_order_ids
        form_view = self.env.ref('sale.view_order_form')
        tree_view = self.env.ref('sale.view_order_tree')
        search_view = self.env.ref('sale.view_sales_order_filter')
        if len(sale_order_ids) != 1:
            return {
                'name': _('Sale orders'),
                'res_model': 'sale.order',
                'type': 'ir.actions.act_window',
                'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
                'view_mode': 'tree, form',
                'search_view_id': search_view.id,
                'view_type': 'form',
                'domain': [('id', 'in', sale_order_ids.ids)],
            }
        return {
            'name': _('Sale orders'),
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'res_id': sale_order_ids[0].id,
        }
