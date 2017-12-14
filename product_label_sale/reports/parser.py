# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class ProductLabelReport(models.AbstractModel):
    _inherit = 'report.product_label.label'

    @api.multi
    def render_product_sale_label(self, docargs, data):
        docargs.update({
            'docs': self.ids,
            'doc_model': 'sale.order.line',
            'tmpl_name': 'product_label_sale.label_sale_document',
            'show_origin': self.env.context.get('show_origin', False)
        })
        return docargs
