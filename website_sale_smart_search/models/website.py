# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class Website(models.Model):
    _inherit = 'website'

    expiry_time = fields.Integer(
        string='Expiry time',
        help='Time in hours to keep cached search results. Set 0 to disable.',
        default=0)
    query_length = fields.Integer(
        string='Query length',
        help='Only strings greater or equal than this number of characters '
             'will produce results.',
        default=3)
    results_limit = fields.Integer(
        string='Results limit',
        help='Number of results to display per search. Set 0 to unlimited.',
        default=0)
