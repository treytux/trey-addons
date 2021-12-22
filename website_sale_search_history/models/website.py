###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    search_history_term_length = fields.Integer(
        string='Search term length',
        default=3,
    )
    search_history_store = fields.Selection(
        selection=[
            ('all', 'All'),
            ('empty', 'Empty'),
        ],
        string='Store searches',
        default='all',
    )
