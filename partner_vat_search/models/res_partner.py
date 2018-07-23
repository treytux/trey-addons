# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        results = super(ResPartner, self).name_search(
            name, args=args, operator=operator, limit=limit)
        if not name:
            return results
        args = args and args or []
        args += [('vat', 'ilike', name)]
        partners = self.env['res.partner'].search(args, limit=limit)
        results += [p.name_get()[0] for p in partners]
        return results
