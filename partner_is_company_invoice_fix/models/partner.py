# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        '''Inherit function so that if the partner is a company, it is marked
        as type 'invoice'.'''
        if 'is_company' in vals and vals['is_company'] is True:
            vals['type'] = 'invoice'
        if ('is_company' in vals and vals['is_company'] is False and
                'type' in vals and vals['type'] == 'invoice'):
            vals['type'] = 'contact'
        return super(ResPartner, self).create(vals)

    @api.multi
    def write(self, vals):
        '''Inherit function so that if the partner is a company, it is marked
        as type 'invoice'.'''
        if 'is_company' in vals and vals['is_company'] is True:
            vals['type'] = 'invoice'
        if ('is_company' in vals and vals['is_company'] is False and
                self.type == 'invoice'):
            vals['type'] = 'contact'
        return super(ResPartner, self).write(vals)
