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
        company = self.company_id
        if self.vat and company and company.partners_vat_unique:
            if self.parent_id:
                child_ids = [ch.id for ch in self.parent_id.child_ids]
                partner_discart_ids = child_ids + [self.parent_id.id] + \
                    [self.id]
                partner_discart_ids = list(set(partner_discart_ids))
                partners = self.search([
                    ('id', 'not in', partner_discart_ids),
                    ('company_id', '=', self.env.user.company_id.id),
                    ('vat', '=', self.vat)], limit=1)
            else:
                partners = self.search([
                    ('id', '!=', self.id),
                    ('company_id', '=', self.env.user.company_id.id),
                    ('vat', '=', self.vat)], limit=1)
            if partners:
                raise exceptions.Warning(_("Error! The VAT %s already exists"
                                         % self.vat))
