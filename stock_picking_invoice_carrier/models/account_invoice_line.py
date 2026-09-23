###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Picking',
    )

    def action_view_picking(self):
        self.ensure_one()
        form_view = self.env.ref('stock.view_move_form')
        tree_view = self.env.ref('stock.view_move_tree')
        search_view = self.env.ref('stock.view_move_search')
        action_vals = {
            'name': _('Stock picking'),
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree, form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'domain': [('id', 'in', [])],
        }
        if self.picking_id:
            del action_vals['views']
            action_vals.update({
                'view_mode': 'form',
                'res_id': self.picking_id.id,
            })
        return action_vals
