###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, api


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    @api.model
    def _get_orderpoint_domain(self, company_id=False):
        domain = super()._get_orderpoint_domain(company_id=company_id)
        if self.env.context.get('orderpoint_ids'):
            domain += [('id', 'in', self.env.context.get('orderpoint_ids'))]
        return domain
