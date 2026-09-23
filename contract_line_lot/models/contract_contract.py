###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class ContractContract(models.Model):
    _inherit = 'contract.contract'

    def action_get_contract_line_lot(self):
        lot_ids = self.contract_line_ids.mapped('lot_ids').ids
        form_view = self.env.ref('stock.view_production_lot_form')
        tree_view = self.env.ref('stock.view_production_lot_tree')
        search_view = self.env.ref('stock.search_product_lot_filter')
        action_vals = {
            'name': _('Lots'),
            'res_model': 'stock.lot',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree, form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'domain': [('id', 'in', lot_ids)],
        }
        if len(lot_ids) == 1:
            del action_vals['views']
            action_vals.update({
                'view_mode': 'form',
                'res_id': lot_ids[0],
            })
        return action_vals
