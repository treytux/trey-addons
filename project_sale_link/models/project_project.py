###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models
from odoo.addons.web.controllers.main import clean_action


class ProjectProject(models.Model):
    _inherit = 'project.project'

    sale_count = fields.Integer(
        compute='_compute_sale_count',
        string='Sales',
    )

    def _get_sales(self):
        self.ensure_one()
        return (
            self.mapped('sale_line_id.order_id')
            | self.mapped('tasks.sale_order_id')
        )

    def _compute_sale_count(self):
        for project in self:
            sales = project._get_sales()
            project.sale_count = len(sales)

    def action_view_sales(self):
        self.ensure_one()
        sales = self._get_sales()
        action = clean_action(self.env.ref('sale.action_orders').read()[0])
        action['domain'] = [('id', 'in', sales.ids)]
        return action
