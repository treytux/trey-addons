# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields


class ProductComparisonLine(models.Model):
    _name = 'product.comparison.line'

    comparison_id = fields.Many2one(
        comodel_name='product.comparison',
        string='Comparison',
        ondelete='cascade',
    )
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product template'
    )
    added_date = fields.Datetime(
        string='Added date',
        default=lambda this: fields.Datetime.now()
    )


class ProductComparison(models.Model):
    _name = 'product.comparison'

    website_id = fields.Many2one(
        comodel_name='website',
        string='Website'
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User'
    )
    line_ids = fields.One2many(
        comodel_name='product.comparison.line',
        inverse_name='comparison_id',
        string='Lines'
    )
