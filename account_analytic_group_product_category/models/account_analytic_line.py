###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            product = self._product_from_vals(vals)
            group = self._group_from_product(product)
            if group:
                vals['group_id'] = group.id
        return super().create(vals_list)

    @api.model
    def _product_from_vals(self, vals):
        if vals.get('product_id'):
            return self.env['product.product'].browse(vals['product_id'])
        if 'stock_move_id' in self._fields and vals.get('stock_move_id'):
            move = self.env['stock.move'].browse(vals['stock_move_id'])
            return move.product_id
        return False

    @api.model
    def _group_from_product(self, product):
        if not product:
            return False
        categ = product.categ_id
        while categ:
            if categ.analytic_group_id:
                return categ.analytic_group_id
            categ = categ.parent_id
        return False

    def write(self, vals):
        res = super().write(vals)
        assign_group = any([
            'product_id' in vals,
            ('stock_move_id' in self._fields and 'stock_move_id' in vals),
        ])
        if assign_group:
            self._assign_group_from_product_category()
        return res

    def _assign_group_from_product_category(self):
        for line in self:
            group = line._get_group_from_product_category()
            if group and line.group_id != group:
                line.group_id = group

    def _product_for_analytic_group(self):
        self.ensure_one()
        if self.product_id:
            return self.product_id
        if 'stock_move_id' in self._fields and self.stock_move_id:
            return self.stock_move_id.product_id
        return False

    def _get_group_from_product_category(self):
        self.ensure_one()
        return self._group_from_product(self._product_for_analytic_group())
