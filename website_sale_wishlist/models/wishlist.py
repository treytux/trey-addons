# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class WishlistLine(models.Model):
    _name = 'wishlist.line'

    wishlist_id = fields.Many2one(
        comodel_name='wishlist',
        string='Wishlist'
    )
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product template'
    )
    added_date = fields.Datetime(
        string='Added date',
        default=lambda this: fields.Datetime.now()
    )


class Wishlist(models.Model):
    _name = 'wishlist'

    website_id = fields.Many2one(
        comodel_name='website',
        string='Website'
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User'
    )
    line_ids = fields.One2many(
        comodel_name='wishlist.line',
        inverse_name='wishlist_id',
        string='Lines'
    )
