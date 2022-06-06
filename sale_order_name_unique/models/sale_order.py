###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.constrains('name', 'company_id')
    def _check_name_unique(self):
        for order in self:
            sales_count = self.env['sale.order'].search_count([
                ('name', '=', order.name),
                ('id', '!=', order.id),
                '|',
                ('company_id', '=', False),
                ('company_id', '=', order.company_id.id),
            ])
            if sales_count:
                raise ValidationError(_(
                    'The order with reference %s already exists') % order.name)
