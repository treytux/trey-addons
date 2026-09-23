###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    sale_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Salesperson',
        compute='_compute_sale_user_id',
        store=True,
    )

    @api.depends('account_id')
    def _compute_sale_user_id(self):
        SaleOrder = self.env['sale.order']
        for line in self:
            if not line.account_id:
                line.sale_user_id = False
                continue
            sale_order = SaleOrder.search([
                ('analytic_account_id', '=', line.account_id.id),
            ], limit=1)
            line.sale_user_id = sale_order.user_id if sale_order else False
