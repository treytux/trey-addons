###############################################################################
# For copyright and license notices, see __manifest__.py file
###############################################################################
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('project_id')
    def _onchange_project_sale_order_type(self):
        self.type_id = self.project_id.sale_order_type_id or False
