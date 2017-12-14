# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api, _


class ProjectTask(models.Model):
    _inherit = 'project.task'

    invoice_line_ids = fields.One2many(
        comodel_name='account.invoice.line',
        inverse_name='task_id',
        string='Invoices Lines')
    invoice_ids = fields.One2many(
        comodel_name='account.invoice',
        compute='_compute_invoice',
        string='Invoices')
    invoice_count = fields.Integer(
        string='Invoice count',
        compute='_compute_invoice')

    @api.one
    @api.depends('invoice_line_ids')
    def _compute_invoice(self):
        invoices = list(set([l.invoice_id.id for l in self.invoice_line_ids]))
        self.invoice_ids = [(6, 0, invoices)]
        self.invoice_count = len(self.invoice_ids)

    @api.multi
    def invoice_tree_view(self):
        context = {
            'default_res_model': self._name,
            'default_res_id': self.id}
        return {
            'name': _('Invoices'),
            'domain': [('id', 'in', self.invoice_ids.ids)],
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': context.__str__()}

    @api.multi
    def action_create_invoice(self):
        pass
