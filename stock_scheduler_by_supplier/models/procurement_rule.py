###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, api


class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    @api.model
    def _make_po_select_supplier(self, values, suppliers):
        if suppliers in self.env.context:
            suppliers.filtered(
                lambda s: s.name in self.env.context['suppliers'])
        return super()._make_po_select_supplier(
            values=values, suppliers=suppliers)
