###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _prepare_contract_value(self, contract_template):
        res = super()._prepare_contract_value(contract_template)
        if contract_template.unit_id:
            res['company_id'] = contract_template.unit_id.company_id.id
        if contract_template.area_id:
            res['area_id'] = contract_template.area_id.id
        return res
