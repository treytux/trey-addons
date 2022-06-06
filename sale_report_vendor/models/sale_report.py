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

    def _query(self, with_clause='', fields=None, groupby='', from_clause=''):
        if not fields:
            fields = {}
        fields['vendor_id'] = ', l.vendor_id as vendor_id'
        groupby += ', l.vendor_id'
        return super()._query(with_clause, fields, groupby, from_clause)
