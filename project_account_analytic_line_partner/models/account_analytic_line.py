# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        compute='_compute_partner_id',
        store=True)

    @api.one
    @api.depends('account_id')
    def _compute_partner_id(self):
        if self.account_id:
            self.partner_id = self.account_id.partner_id
