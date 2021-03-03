# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, fields, _
from openerp.exceptions import Warning


class CrmClaim(models.Model):
    _inherit = 'crm.claim'

    force_number = fields.Char(
        string='Force number',
    )

    def _force_number(self, vals):
        if 'code' in vals:
            return
        if vals.get('force_number'):
            claims = self.search([('code', '=', vals['force_number'])])
            if claims:
                raise Warning(
                    _('Claim number %s already exist!') % vals['force_number']
                )
            vals['code'] = vals['force_number']

    @api.model
    def create(self, vals):
        self._force_number(vals)
        return super(CrmClaim, self).create(vals)

    @api.multi
    def write(self, vals):
        self._force_number(vals)
        return super(CrmClaim, self).write(vals)
