###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SearchHistory(models.Model):
    _name = 'search.history'
    _description = 'Search history'

    name = fields.Char(
        string='Name',
        help='Website searches',
        required=True,
        translate=True,
    )
    sanitized_search = fields.Char(
        string='Sanitized search',
        translate=True,
    )
    last_update = fields.Date(
        string='Last update',
    )
    products_found = fields.Boolean(
        string='Products found',
    )
    searches_count = fields.Integer(
        string='Searches count',
        default=0,
    )
    _sql_constraints = [
        ('uniq_name', 'unique(name)',
         'The name of this search history must be unique!'),
    ]
