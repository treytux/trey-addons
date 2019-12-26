# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_id')
    @api.multi
    def _is_simulator(self):
        supplier = self[0].order_id.company_id.ede_supplier_id
        for line in self:
            supplier_infos = line.product_id.product_tmpl_id.mapped(
                'seller_ids').filtered(lambda l: l.name.id == supplier.id)
            line.is_simulator = True if supplier_infos else False

    is_simulator = fields.Boolean(
        string='Access Simulator',
        compute=_is_simulator,
        store=True
    )
    is_ede_danger = fields.Boolean(
        string='EDE Danger',
    )
