# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api


class ComputeCreditLimit(models.TransientModel):
    _name = 'wiz.compute.credit_limit'
    _description = 'Compute Credit Limit'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Project')
    picking_ids = fields.One2many(
        comodel_name='wiz.compute.credit_limit.picking',
        inverse_name='wizard_id',
        string='Pickings')
    picking_pending = fields.Float(
        string='Picking pending',
        readonly=1)
    work_ids = fields.One2many(
        comodel_name='wiz.compute.credit_limit.work',
        inverse_name='wizard_id',
        string='Works')
    work_pending = fields.Float(
        string='Work pending',
        readonly=1)
    credit = fields.Float(
        string='Credit',
        readonly=1)
    debit = fields.Float(
        string='Debit',
        readonly=1)
    balance = fields.Float(
        string='Balance',
        compute='_compute')

    @api.depends('credit', 'debit')
    def _compute(self):
        self.balance = self.debit - (
            self.credit + self.picking_pending + self.work_pending)

    @api.multi
    def button_accept(self):
        pass


class ComputeCreditLimitPicking(models.TransientModel):
    _name = 'wiz.compute.credit_limit.picking'
    _description = 'Credit limit picking'

    wizard_id = fields.Many2one(
        comodel_name='wiz.compute.credit_limit',
        string='Wizard')
    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Picking')


class ComputeCreditLimitWork(models.TransientModel):
    _name = 'wiz.compute.credit_limit.work'
    _description = 'Credit limit work'

    wizard_id = fields.Many2one(
        comodel_name='wiz.compute.credit_limit',
        string='Wizard')
    work_id = fields.Many2one(
        comodel_name='account.analytic.line',
        string='Work')
    amount = fields.Float(
        related='work_id.amount',
        string='To invoiced')
    amount_to_invoiced = fields.Float(
        related='work_id.amount_to_invoiced',
        string='To invoiced')
