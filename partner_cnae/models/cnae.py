# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api


class CnaeRisk(models.Model):
    _name = 'partner_cnae.cnae_risk'

    name = fields.Char(string='Empty')
    cnae_id = fields.Many2one(
        comodel_name='partner_cnae.cnae',
        string='Cnae')
    year = fields.Char(string='Year')
    coef_it = fields.Float(string='IT')
    coef_ims = fields.Float(string='IMS')
    coef_total = fields.Float(string='Total')


class Cnae(models.Model):
    _name = 'partner_cnae.cnae'
    _order = 'code'

    code = fields.Char(
        string='Code',
        help='Four character code',
        required=True
    )
    name = fields.Char(
        string='Name',
        help='Name of cnae',
        required=True
    )
    parent_id = fields.Many2one(
        comodel_name='partner_cnae.cnae',
        string='Partner cnae')
    child_ids = fields.One2many(
        comodel_name='partner_cnae.cnae',
        inverse_name='parent_id',
        string='Cnae childs')
    cnae_risk_ids = fields.One2many(
        comodel_name='partner_cnae.cnae_risk',
        inverse_name='cnae_id',
        string='Cnae risk')

    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for cnae in self:
            result.append((cnae.id, '{} {}'.format(
                cnae.code.encode('utf-8'), cnae.name.encode('utf-8'))))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []

        if name:
            name = name.split(' ')

            if name[0].isdigit():
                args = [('code', operator, name[0])] + args
            else:
                args = [('name', operator, ' '.join(name))] + args

        cnaes = self.search(args, limit=limit)
        return cnaes.name_get()
