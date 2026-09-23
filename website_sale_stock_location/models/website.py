###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    product_stock_info = fields.Selection(
        selection=[
            ('portal', 'Show for portal users'),
            ('employee', 'Show for employee users'),
            ('both', 'Show for portal and employee users'),
        ],
        string='Product stock info',
        default='employee',
    )
    product_stock_location = fields.Selection(
        selection=[
            ('portal', 'Show for portal users'),
            ('employee', 'Show for employee users'),
            ('both', 'Show for portal and employee users'),
        ],
        string='Product stock location',
        default='employee',
    )

    def get_product_stock_info(self):
        return self.product_stock_info

    def show_product_stock_info(self, user):
        if (
            user.has_group('base.group_user')
                and self.product_stock_info in ['both', 'employee']):
            return True
        if (
            user.has_group('base.group_portal')
                and self.product_stock_info in ['both', 'portal']):
            return True
        return False

    def get_product_stock_location(self):
        return self.product_stock_location

    def show_product_stock_location(self, user):
        if (
            user.has_group('base.group_user')
                and self.product_stock_location in ['both', 'employee']):
            return True
        if (
            user.has_group('base.group_portal')
                and self.product_stock_location in ['both', 'portal']):
            return True
        return False
