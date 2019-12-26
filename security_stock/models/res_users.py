###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    warehouse_ids = fields.Many2many(
        string='Warehouses',
        comodel_name='stock.warehouse',
        relation='user_warehouse_rel',
        column1='user_id',
        column2='warehouse_id',
        help='Warehouses allowed for this user.',
    )
    location_ids = fields.Many2many(
        string='Locations',
        comodel_name='stock.location',
        relation='user_location_rel',
        column1='user_id',
        column2='location_id',
        help='Locations allowed for this user.',
    )
