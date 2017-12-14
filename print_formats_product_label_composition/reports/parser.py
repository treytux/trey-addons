# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class PrintFormatsProductLabelComposition(models.TransientModel):
    _name = 'report.print_formats_product_label_composition.composition_label'

    @api.multi
    def render_html(self, data=None):
        renders = {
            'render_product_sale_label': 'sale.order.line',
            'render_product_picking_label': 'stock.move',
            'render_product_purchase_label': 'purchase.order.line'}
        render_func = self.env.context.get('render_func')
        product_ids = self.ids
        if render_func in renders:
            model_obj = self.env[renders[render_func]]
            product_ids = [
                l.product_id.id for l in model_obj.browse(self.ids)
                if l.product_id]
        report_obj = self.env['report']
        template = 'print_formats_product_label_composition.composition_label'
        report = report_obj.browse(self.ids[0])
        return report.render(template, {
            'doc_ids': product_ids,
            'doc_model': report_obj._get_report_from_name(template).model,
            'docs': self.env['product.product'].browse(product_ids)})
