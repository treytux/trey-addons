# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields


class ProductFeatureLine(models.Model):
    _name = "product.feature.line"

    name = fields.Char(
        u'Empty', translate=True
    )
    product_tmpl_id = fields.Many2one(
        comodelname='product.template',
        string=u'Template product'
    )
    feature_id = fields.Many2one(
        comodel_name='product.template.feature',
        string=u'Feature'
    )
    value_ids = fields.Many2many(
        comodel_name='product.template.feature.value',
        relation='product_template_feature_value_rel',
        column1='line_id',
        column2='val_id'
    )


class ProductTemplateFeature(models.Model):
    _name = "product.template.feature"

    name = fields.Char(
        string=u'Name',
        required=False,
        translate=True,
        select=True,
        help=u'Feature name'
    )
    parent_id = fields.Many2one(
        comodel_name='product.template.feature',
        string=u'Parent'
    )
    value_ids = fields.One2many(
        comodel_name='product.template.feature.value',
        relation='feature_id',
        string=u'Valores')


class ProductTemplateFeatureValue(models.Model):
    _name = "product.template.feature.value"

    name = fields.Char(
        string=u'Name',
        required=False,
        translate=True,
        select=True,
        help=u'Feature value name'
    )
    feature_id = fields.Many2one(
        comodel_name='product.template.feature',
        string=u'Feature'
    )
