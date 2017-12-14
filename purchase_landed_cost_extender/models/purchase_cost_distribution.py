# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.##

from openerp import models, fields, api
import logging

_log = logging.getLogger(__name__)


class PurchaseCostDistribution(models.Model):
    _inherit = "purchase.cost.distribution"

    cost_update_type = fields.Selection(
        selection_add=[('stock', 'Upgrade with Stock')])

    @api.multi
    def action_done(self):
        for distribution in self:
            for line in distribution.cost_lines:
                if distribution.cost_update_type == 'direct':
                    line.product_id.product_tmpl_id.standard_price = \
                        line.standard_price_new
                elif distribution.cost_update_type == 'stock':
                    line.product_id.product_tmpl_id.standard_price = \
                        line.standard_price_new
            distribution.state = 'done'
        return True

    class PurchaseCostDistributionLine(models.Model):
        _inherit = "purchase.cost.distribution.line"

        @api.one
        @api.depends('standard_price_old', 'cost_ratio')
        def _compute_standard_price_new(self):
            if self.distribution.cost_update_type == 'direct':
                if self.product_id.standard_price != 0:
                    self.standard_price_new = self.standard_price_old +\
                        self.cost_ratio
                else:
                    self.standard_price_new = self.product_price_unit +\
                        self.cost_ratio
            elif self.distribution.cost_update_type == 'stock':
                # Stock actual - cantidad de pedido para el calculo
                old_price = self.product_id.standard_price
                old_qty = self.product_id.qty_available
                new_price = self.standard_price_old + self.cost_ratio
                new_qty = self.product_qty
                if old_price != 0 and (old_qty - new_qty) > 0 and old_qty > 0:
                    real_qty = old_qty - new_qty
                    middle_price = (old_price*real_qty)+(new_price*new_qty)
                    middle_price = middle_price / (real_qty+new_qty)
                else:
                    middle_price = self.product_price_unit + self.cost_ratio
                self.standard_price_new = middle_price
