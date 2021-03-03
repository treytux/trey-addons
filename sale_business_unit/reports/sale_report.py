###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    unit_id = fields.Many2one(
        comodel_name='product.business.unit',
        string='Business unit',
    )
    area_id = fields.Many2one(
        comodel_name='product.business.area',
        string='Area',
    )

    def _query(self, with_clause='', fields=None, groupby='', from_clause=''):
        if not fields:
            fields = {}
        fields['unit_id'] = ', t.unit_id as unit_id'
        fields['area_id'] = ', t.area_id as area_id'
        groupby += ', t.unit_id, t.area_id'
        return super(SaleReport, self)._query(
            with_clause, fields, groupby, from_clause)
