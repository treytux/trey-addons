# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api
from functools import partial


class ProductLabelReport(models.AbstractModel):
    _inherit = 'report.print_formats_product_label.label'

    @api.model
    def get_variant_name(self, product):
        return '%s %s' % (
            product.name,
            '-'.join([v.name for v in product.attribute_value_ids]))

    @api.multi
    def render_product_sale_label(self, docargs, data):
        docargs.update({
            'docs': self.ids,
            'doc_model': 'sale.order.line',
            'tmpl_name':
                'print_formats_product_label_sale.label_sale_document',
            'show_origin': self.env.context.get('show_origin', False),
            'get_variant_name': partial(self.get_variant_name)})
        return docargs
