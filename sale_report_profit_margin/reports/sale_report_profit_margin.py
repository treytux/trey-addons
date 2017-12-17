# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields


class SaleReport(models.Model):
    _inherit = 'sale.report'
    _auto = False

    margin = fields.Float(
        'Margin', readonly=True
    )
    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='Partner state',
        readonly=True
    )

    def _select(self):
        select_str = super(SaleReport, self)._select()
        return '%s %s' % (
            select_str,
            ',l.margin as margin'
            ',rp.state_id as state_id')

    def _from(self):
        from_str = super(SaleReport, self)._from()
        return '%s %s' % (
            from_str,
            'left join res_partner rp on (rp.id=s.partner_id)')

    def _group_by(self):
        group_by_str = super(SaleReport, self)._group_by()
        return '%s ,l.margin ,rp.state_id' % group_by_str
