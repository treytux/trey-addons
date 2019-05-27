# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_lines_massive_edit(self):
        self.ensure_one()
        wiz = self.env['wiz.sale_order_line_edit'].create({
            'picking_id': (self.picking_ids and
                           self.picking_ids.ids[0] or None)})
        for line in self[0].order_line:
            self.env['wiz.sale_order_line_edit.lines'].create({
                'wizard_id': wiz.id,
                'line_id': line.id,
                'product_id': line.product_id.id,
                'name': line.name,
                'line_name_origin': line.name,
                'quantity': line.product_uom_qty,
                'price_unit': line.price_unit,
                'discount': line.discount})
        view = self.env.ref(
            'sale_order_line_massive_edit.wiz_sale_order_line_edit')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wiz.sale_order_line_edit',
            'res_id': wiz.id,
            'view_id': view.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new'}
