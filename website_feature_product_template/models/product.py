# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    feature_line_ids = fields.One2many(
        comodel_name='product.feature.line',
        relation='product_tmpl_id',
        string=u'Product features'
    )
