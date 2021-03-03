###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_simulator = fields.Boolean(
        string='Access Simulator',
        compute='_compute_is_simulator',
        store=True,
    )
    is_ede_danger = fields.Boolean(
        string='EDE Danger',
    )

    @api.depends('product_id')
    def _compute_is_simulator(self):
        supplier = self.env.user.company_id.ede_supplier_id
        for line in self:
            if not line.product_id:
                line.is_simulator = False
            supplier_infos = line.product_id.product_tmpl_id.mapped(
                'seller_ids').filtered(lambda l: l.name == supplier)
            line.is_simulator = bool(supplier_infos)

    def _check_routing(self):
        res = super()._check_routing()
        if self.route_id.is_ede_customer:
            return True
        return res
