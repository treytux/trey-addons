# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        copy=False,
        string='Analytic Account')
    timesheet_ids = fields.One2many(
        comodel_name='hr.analytic.timesheet',
        inverse_name='production_id',
        copy=False,
        string='Timesheets')

    @api.model
    def create(self, vals):
        res = super(MrpProduction, self).create(vals)
        if 'analytic_account_id' in vals:
            return res
        account_id = self.env['account.analytic.account'].create({
            'name': res.name,
            'type': 'normal',
            'parent_id': (self.env.user.company_id.analytic_mrp_root_id and
                          self.env.user.company_id.analytic_mrp_root_id.id or
                          None)})
        res.analytic_account_id = account_id.id
        return res

    @api.one
    def write(self, vals, **kwargs):
        res = super(MrpProduction, self).write(vals, **kwargs)
        if 'name' in vals:
            self.analytic_account_id.name = vals['name']
        return res
