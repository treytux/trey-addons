###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models


class FSMLocation(models.Model):
    _inherit = 'fsm.location'

    sale_order_ids = fields.One2many(
        comodel_name='sale.order',
        inverse_name='fsm_location_id',
        string='Sale orders',
    )
    sale_order_count = fields.Integer(
        compute='_compute_sale_order_ids',
    )

    def _compute_sale_order_ids(self):
        for location in self:
            location.sale_order_count = len(self.sale_order_ids)

    def action_view_sale_order_link(self):
        sale_order_ids = self.sale_order_ids
        form_view = self.env.ref('sale.view_order_form')
        tree_view = self.env.ref('sale.view_order_tree')
        search_view = self.env.ref('sale.view_sales_order_filter')
        action = {
            'name': _('Sale orders'),
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'res_id': sale_order_ids and sale_order_ids[0].id or False,
            'context': {
                'default_partner_id': self.owner_id.id,
                'default_partner_invoice_id': self.owner_id.id,
                'default_partner_shipping_id': self.shipping_address_id.id,
                'default_fsm_location_id': self.id,
            }
        }
        if len(sale_order_ids) != 1:
            action.update({
                'domain': [('id', 'in', sale_order_ids.ids)],
                'view_mode': 'tree, form',
                'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
                'res_id': False,
            })
        return action
