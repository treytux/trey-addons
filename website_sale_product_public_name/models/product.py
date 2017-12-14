# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import api, models, fields


class product_template(models.Model):
    _inherit = "product.template"

    public_name = fields.Char(
        string=u'Public Name',
        required=False,
        translate=True,
        select=True,
        help=u"Public name for products in eCommerce"
    )

    @api.model
    def create(self, vals):
        if 'public_name' not in vals:
            vals['public_name'] = vals['name']
        return super(product_template, self).create(vals)
