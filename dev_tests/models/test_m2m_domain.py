# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class TestM2mDomain(models.Model):
    _name = 'test.m2m_domain'
    _description = 'Test M2m domains'

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Manager',
        domain="[('id', 'in', allow_user_ids[0][2])] ")
    user_ids = fields.Many2many(
        comodel_name='res.users',
        domain="[('id', 'in', allow_user_ids[0][2])] ")
    allow_user_ids = fields.Many2many(
        comodel_name='res.users', string='Allow Users')
