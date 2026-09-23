###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ProjectCreateSaleOrderLine(models.TransientModel):
    _inherit = 'project.create.sale.order.line'

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.product_id = self.employee_id.product_id.id
