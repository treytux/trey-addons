# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class SaleReport(models.Model):
    _inherit = 'sale.report'

    agents_name = fields.Char(
        string='Agents')

    def _select(self):
        sql_str = super(SaleReport, self)._select()
        sql_str += ', s.agents_name as agents_name'
        return sql_str

    def _group_by(self):
        sql_str = super(SaleReport, self)._group_by()
        sql_str += ', s.agents_name'
        return sql_str
