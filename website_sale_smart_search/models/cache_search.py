# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class CacheSearch(models.Model):
    _name = 'cache.search'

    name = fields.Char(
        string='Query',
        help='Typed text on search',
        translate=True)
    result_product_ids = fields.Many2many(
        comodel_name='product.template',
        relation='product_template_cache_rel',
        column1='product_tmpl_id',
        column2='cache_search_id',
        help='Products')
    custom_results = fields.Boolean(
        string='Custom results',
        help='Check this field if you want to customize the results.')
    searches = fields.Integer(
        string='No. of searches',
        help='Number of times this query has been searched.')
    clicks = fields.Integer(
        string='Clicks',
        help='Number of times one result has been clicked.')
    last_cache_update = fields.Datetime(
        string='Last cache update',
        help='Last date that cache has been generated.')
