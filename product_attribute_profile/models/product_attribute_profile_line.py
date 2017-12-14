# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, _, exceptions, api


class ProductAttributeProfileLine(models.Model):
    _name = 'product.attribute.profile.line'
    _description = 'Product Attribute Profile Line'

    profile_id = fields.Many2one(
        comodel_name='product.attribute.profile',
        string='Profile')
    value_id = fields.Many2one(
        comodel_name='product.attribute.value',
        string='Value',
        required=True)
    quantity = fields.Float(
        string='Quantity')

    @api.one
    @api.constrains('profile_id', 'value_id')
    def _check_same_attribute(self):
        if self.profile_id.attribute_id != self.value_id.attribute_id:
            raise exceptions.Warning(
                _('All lines must be attribute "%s", the value %s no have '
                  'the same attrribute') % (
                    self.profile_id.attribute_id.name, self.value_id.name))
