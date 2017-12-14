# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, fields, _


class ProductFeature(models.Model):
    _name = 'product.feature'
    _description = "Product Features"
    _order = 'sequence'

    @api.multi
    def get_name(self):
        return self.public_name if self.public_name else self.name

    sequence = fields.Integer(
        string='Sequence',
        help="Determine the display order")
    name = fields.Char(
        string='Name',
        translate=True,
        required=True)
    value_ids = fields.One2many(
        comodel_name='product.feature.value',
        inverse_name='feature_id',
        string='Features',
        copy=True)
    description = fields.Char(
        string="Description",
        required=False)
    public_name = fields.Char(
        string="Public Name",
        required=False)


class ProductFeatureValue(models.Model):
    _name = 'product.feature.value'
    _order = 'sequence'

    @api.multi
    def name_get(self):
        if not self.env.context.get('show_attribute', True):
            return super(ProductFeatureValue, self).name_get()
        res = []
        for value in self:
            res.append([value.id, "%s: %s" % (value.feature_id.name,
                                              value.name)])
        return res

    sequence = fields.Integer(
        string='Sequence',
        help="Determine the display order")
    name = fields.Char(
        string='Value',
        translate=True,
        required=True)
    feature_id = fields.Many2one(
        comodel_name='product.feature',
        string='Feature',
        required=True,
        ondelete='cascade')
    category_ids = fields.Many2many(
        comodel_name='product.public.category',
        relation='category_feature_value_rel',
        column1='feature_id',
        column2='category_id',
        string='Public Category Features',
        readonly=True)

    _sql_constraints = [
        ('value_company_uniq', 'unique (name,feature_id)',
         _('This attribute value already exists !'))
    ]


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    feature_ids = fields.Many2many(
        comodel_name='product.feature',
        relation='product_category_feature_value_rel',
        column1='category_id',
        column2='feature_id',
        string='Features')


class ProductFeatureLine(models.Model):
    _name = 'product.template.feature.line'
    _rec_name = 'feature_id'

    template_id = fields.Many2one(
        comodel_name='product.template',
        string='Product',
        required=True,
        ondelete='cascade')
    feature_id = fields.Many2one(
        comodel_name='product.feature',
        string='Feature',
        required=True,
        ondelete='restrict')
    value_ids = fields.Many2many(
        comodel_name='product.feature.value',
        relation='product_template_feature_line_feature_value_rel',
        column1='line_id',
        column2='value_id',
        string='Values')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    feature_line_ids = fields.One2many(
        comodel_name='product.template.feature.line',
        inverse_name='template_id',
        string="Feature Line",
        required=False)
