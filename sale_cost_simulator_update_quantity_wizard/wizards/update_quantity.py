###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleCostUpdateQuantity(models.TransientModel):
    _name = 'sale.cost.update_quantity'
    _description = 'Wizard for update quantity'

    simulator_id = fields.Many2one(
        comodel_name='sale.cost.simulator',
        string='Simulator',
    )
    parent_id = fields.Many2one(
        comodel_name='sale.cost.line',
        string='Parent',
    )
    line_ids = fields.Many2many(
        comodel_name='sale.cost.line',
        relation='sale_cost_line2update_quantity_rel',
        column1='apply_pricelist_id',
        column2='line_id',
        domain='[("parent_id", "=", parent_id)]',
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        obj = self.env[self.env.context['active_model']].browse(
            self.env.context['active_id'])
        if obj and self.env.context['active_model'] == 'sale.cost.line':
            ids = obj.child_ids and obj.child_ids.ids or []
        else:
            ids = obj.line_ids and obj.line_ids.ids or []
        res['line_ids'] = [(6, 0, ids)]
        return res

    @api.multi
    def button_accept(self):
        return {'type': 'ir.actions.act_window_close'}
