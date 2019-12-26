# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, fields, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    quotation_sales_count = fields.Integer(
        string='# Quotation sales',
        compute='_compute_quotation_sales_count')

    def _get_quotation_sales_domain(self):
        return [('product_id', '=', self.id), ('state', '=', 'draft')]

    @api.one
    def _compute_quotation_sales_count(self):
        self.quotation_sales_count = sum([
            line.product_uom_qty
            for line in self.env['sale.order.line'].search(
                self._get_quotation_sales_domain())])

    @api.multi
    def action_view_quotation_sales(self):
        tree_view = self.env.ref('sale.view_order_line_tree')
        form_view = self.env.ref('sale.view_order_line_form2')
        search_view = self.env.ref('sale.view_sales_order_line_filter')
        return {
            'name': _('Quotation sale order line'),
            'domain': self._get_quotation_sales_domain(),
            'res_model': 'sale.order.line',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree, form',
            'search_view_id': search_view.id,
            'view_type': 'form'}
