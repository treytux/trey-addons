# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class Partner(models.Model):
    _inherit = 'res.partner'

    is_center = fields.Boolean(
        string='Is a Center')
    child_ids = fields.One2many(
        comodel_name='res.partner',
        inverse_name='parent_id',
        string='Contacts',
        domain=[
            ('active', '=', True),
            ('is_company', '=', False),
            ('is_center', '=', False)])
    center_ids = fields.One2many(
        comodel_name='res.partner',
        inverse_name='parent_id',
        string='Center',
        copy=False,
        domain=[('is_center', '=', True)])
