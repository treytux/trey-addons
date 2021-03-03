###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.tools.float_utils import float_round


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    contract_quantity = fields.Float(
        string='Quantity',
    )
    contract_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit of Measure',
    )

    def _prepare_contract_line_values(self, contract,
                                      predecessor_contract_line_id=False):
        res = super()._prepare_contract_line_values(
            contract,
            predecessor_contract_line_id=predecessor_contract_line_id)
        uom = self.contract_uom_id or self.product_uom
        res.update({
            'quantity': self.contract_quantity,
            'uom_id': uom.id,
        })
        if uom != self.product_uom:
            qty = self.contract_uom_id._compute_quantity(
                self.contract_quantity, self.product_uom)
            precision = self.env['decimal.precision'].precision_get(
                'Product Price')
            amount = float_round(self.price_unit * qty, precision)
            res['price_unit'] = amount
        return res

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        res = super().product_id_change()
        self.contract_quantity = self.product_uom_qty
        self.contract_uom_id = self.product_uom.id
        return res

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        res = super().product_uom_change()
        self.contract_quantity = self.product_uom_qty
        self.contract_uom_id = self.product_uom.id
        return res
