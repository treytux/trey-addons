###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    is_return = fields.Boolean(
        string='Is return',
    )

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res['is_return'] = 's.is_return'
        return res

    def _group_by_sale(self):
        group_by = super()._group_by_sale()
        group_by = f'''
            {group_by},
            s.is_return'''
        return group_by
