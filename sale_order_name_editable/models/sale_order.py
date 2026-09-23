###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.constrains('name')
    def _check_name_unique(self):
        sales_count = self.search_count([
            ('id', '!=', self.id),
            ('name', '=', self.name),
        ])
        if sales_count:
            raise ValidationError(_(
                'There is already another sales order with the same name, it '
                'must be unique.'))
