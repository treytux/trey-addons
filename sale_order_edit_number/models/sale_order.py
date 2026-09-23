# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, fields, _
from openerp.exceptions import Warning


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    force_number = fields.Char(
        string='Force number',
    )

    def _force_number(self, vals):
        if 'name' in vals:
            return
        if vals.get('force_number'):
            sales = self.search([('name', '=', vals['force_number'])])
            if sales:
                raise Warning(
                    _('Sale order number %s already exist!')
                    % vals['force_number']
                )
            vals['name'] = vals['force_number']

    @api.model
    def create(self, vals):
        self._force_number(vals)
        return super(SaleOrder, self).create(vals)

    @api.multi
    def write(self, vals):
        self._force_number(vals)
        return super(SaleOrder, self).write(vals)
