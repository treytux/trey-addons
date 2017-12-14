# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class SaleCostApplyPricelist(models.TransientModel):
    _name = 'sale.cost.apply_pricelist'
    _description = 'Wizard for apply pricelist'

    simulator_id = fields.Many2one(
        comodel_name='sale.cost.simulator',
        string='Simulator')
    parent_id = fields.Many2one(
        comodel_name='sale.cost.line',
        string='Parent')
    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        domain=[('type', '=', 'sale')],
        string='Pricelist')
    line_ids = fields.Many2many(
        comodel_name='sale.cost.line',
        relation='sale_cost_line2apply_pricelist_rel',
        column1='apply_pricelist_id',
        column2='line_id',
        domain='[("parent_id", "=", parent_id)]')
    apply_childs = fields.Boolean(
        string='Apply childs',
        default=True)

    @api.model
    def default_get(self, fields):
        res = super(SaleCostApplyPricelist, self).default_get(fields)
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
        def apply_childs(line):
            line.compute_pricelist(self.pricelist_id.id)
            if not self.apply_childs:
                return
            for child in line.child_ids:
                apply_childs(child)

        for line in self.line_ids:
            apply_childs(line)
        self.simulator_id.compute_total()
        return {'type': 'ir.actions.act_window_close'}
