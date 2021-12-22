###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    purchase_service_group_type = fields.Selection(
        string='Purchase service group type',
        selection=[
            ('ungrouped', 'Ungrouped'),
            ('group_by_date', 'Group by date'),
        ],
        help='Standard: If there is an open purchase requisition for that '
             'supplier and product service, it will add a new line.\n'
             'No grouping: It will create a new purchase order for each line '
             'of the service type sales order.\n'
             'Grouped by date: If there is an open purchase requisition that '
             'meets the date criteria, it will be added to the order, '
             'otherwise a new order will be created.'
    )
    purchase_group_day = fields.Integer(
        string='Group day',
    )
    purchase_group_overdue_days = fields.Char(
        string='Group overdue days',
    )
