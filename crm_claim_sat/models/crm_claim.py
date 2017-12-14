# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class CrmClaim(models.Model):
    _inherit = 'crm.claim'

    partner_sat_id = fields.Many2one(
        comodel_name='res.partner',
        domain=[('sat', '=', True)],
        string='SAT')
    access_date = fields.Datetime(
        string='Access date',
        readonly=True)
    print_date = fields.Datetime(
        string='Print date',
        readonly=True)
    sat_observations = fields.Text(
        string='SAT Observations')
