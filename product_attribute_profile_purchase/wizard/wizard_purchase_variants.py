# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, fields


class PurchaseManageVariant(models.TransientModel):
    _inherit = 'purchase.manage.variant'

    profile_id = fields.Many2one(
        comodel_name='product.attribute.profile',
        string='Attribute Profile')
    attribute_ids = fields.Many2many(
        comodel_name='product.attribute',
        relation='purchase_manage_variant2product_attribute_rel',
        column1='manage_variant_id',
        column2='attribute_id')

    @api.onchange('profile_id')
    def _onchange_profile_ids(self):
        for line in self.variant_line_ids:
            val = sum([l.quantity for l in self.profile_id.line_ids
                       if line.value_x.id == l.value_id.id])
            line.product_qty = val or 0

    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id(self):
        super(PurchaseManageVariant, self)._onchange_product_tmpl_id()
        attr_ids = [l.value_x.attribute_id.id for l in self.variant_line_ids]
        self.attribute_ids = [(6, 0, attr_ids)]
