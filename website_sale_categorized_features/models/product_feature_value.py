###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models


class ProductFeatureValue(models.Model):
    _name = 'product.feature.value'
    _description = 'Product Feature Values'
    _order = 'sequence'

    def name_get(self):
        if not self.env.context.get('show_attribute', True):
            return super().name_get()
        res = []
        for value in self:
            res.append([
                value.id, "%s: %s" % (value.feature_id.name, value.name)])
        return res

    sequence = fields.Integer(
        string='Sequence',
        help='Determine the display order',
    )
    name = fields.Char(
        string='Value',
        translate=True,
        required=True,
    )
    feature_id = fields.Many2one(
        comodel_name='product.feature',
        string='Feature',
        required=True,
        ondelete='cascade',
    )
    category_ids = fields.Many2many(
        comodel_name='product.public.category',
        relation='category_feature_value_rel',
        column1='feature_id',
        column2='category_id',
        string='Public Category Features',
        readonly=True,
    )

    _sql_constraints = [
        ('value_company_uniq', 'unique (name,feature_id)',
         _('This attribute value already exists !'))
    ]
