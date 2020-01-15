# Copyright 2019 Vicent Cubells - Trey <http://www.trey.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.model
    def _prepare_purchase_order_line_from_seller(self, seller):
        res = super()._prepare_purchase_order_line_from_seller(seller)
        if not res:
            return res
        res.update({
            'multiple_discount': seller.multiple_discount,
        })
        return res
