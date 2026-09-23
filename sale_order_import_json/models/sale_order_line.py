###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_agents_vals(self, vals=None):
        if 'agents' not in self._fields:
            return []
        company = self.env.user.company_id
        if company.skip_commission_agents_zero_value_lines:
            discount = (vals or {}).get('discount', self.discount)
            price_unit = (vals or {}).get('price_unit', self.price_unit)
            if discount == 100 or not price_unit:
                return []
        return super()._prepare_agents_vals(vals=vals)
