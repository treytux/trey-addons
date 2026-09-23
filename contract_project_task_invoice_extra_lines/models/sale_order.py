###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super().action_confirm()
        for sale in self:
            project = sale.order_line.project_id
            contract = sale.order_line.contract_id
            if not project and not contract:
                return res
            sale.order_line.project_id.contract_id = (
                sale.order_line.contract_id.id)
        return res
