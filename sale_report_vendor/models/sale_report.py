###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    vendor_id = fields.Many2one(
        comodel_name='res.partner',
        string='Vendor',
    )

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res['vendor_id'] = 'l.vendor_id'
        return res

    def _group_by_sale(self):
        return super()._group_by_sale() + ', l.vendor_id'
