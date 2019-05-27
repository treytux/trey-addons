# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, exceptions, _


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.one
    @api.constrains('vat')
    def _check_vat(self):
        if not self.vat:
            return
        if self.company_id and not self.company_id.partners_vat_unique:
            return
        company = self.env.user.company_id
        if not self.company_id and not company.partners_vat_unique:
            return
        ignore_ids = [self.id]
        if self.parent_id:
            child_ids = [ch.id for ch in self.parent_id.child_ids]
            ignore_ids = list(set(
                child_ids + [self.parent_id.id] + ignore_ids))
        partners = self.search([
            ('id', 'not in', ignore_ids),
            ('vat', '=', self.vat),
            '|',
            ('company_id', '=', False),
            ('company_id', '=', self.env.user.company_id.id)])
        if partners:
            raise exceptions.Warning(
                _('Error! The VAT %s already exists' % self.vat))
