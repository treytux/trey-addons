# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api, _, exceptions
import logging
_log = logging.getLogger(__name__)


class ProjectTaskCreateInvoice(models.TransientModel):
    _name = 'project.task.create_invoice'
    _description = 'Create Invoice'

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
        default=lambda s: s.env.user)
    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project')
    partner_id = fields.Many2one(
        related='project_id.partner_id',
        string='Project')
    work_ids = fields.One2many(
        comodel_name='project.task.create_invoice.work',
        inverse_name='wizard_id',
        string='Work Lines')
    picking_ids = fields.One2many(
        comodel_name='project.task.create_invoice.picking',
        inverse_name='wizard_id',
        string='Pickings')
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        domain=[('type', '=', 'sale')],
        required=1,
        string='Journal')

    @api.onchange('user_id')
    def onchange_user_id(self):
        task_ids = self.env.context.get('active_ids', [])
        if not task_ids:
            raise exceptions.Warning(_('Select Task for invoice'))
        tasks = self.env['project.task'].browse(task_ids)
        if not([True for t in tasks if t.project_id == tasks[0].project_id]):
            raise exceptions.Warning(
                _('Only can invoice tasks for same project'))
        if not([True for t in tasks if t.partner_id == tasks[0].partner_id]):
            raise exceptions.Warning(
                _('Only can invoice tasks for same partner'))
        self.project_id = tasks[0].project_id.id

        # Pickings
        pickings = list(set([p for t in tasks for p in t.picking_ids]))
        self.picking_ids = (
            [(6, 0, [])] + [
                (0, 0, {'picking_id': p.id})
                for p in pickings
                if p.state == 'done' and p.invoice_state == '2binvoiced'])

        # Works
        work_ids = list(set([w for t in tasks for w in t.work_ids]))
        self.work_ids = (
            [(6, 0, [])] + [
                (0, 0, {
                    'work_id': w.id,
                    'name': '%s [%s]' % (w.task_id.name, w.name)})
                for w in work_ids
                if not w.hr_analytic_timesheet_id.invoice_id])

    @api.model
    def create_invoice_line_task(self, line, invoice, product, partner):
        return line

    @api.multi
    def button_accept(self):
        task_ids = self.env.context.get('active_ids', [])
        assert task_ids, _('No task id in active_ids for accept operation')
        tasks = self.env['project.task'].browse(task_ids)
        self.project_id = tasks[0].project_id.id
        picking_ids = [p.picking_id.id for p in self.picking_ids]
        company_id = self.env.user.company_id.id
        analytic_account_obj = self.env['account.analytic.line']
        invoice = None
        if picking_ids:
            assert all([p.picking_id.task_id for p in self.picking_ids])
            ishipping = self.env['stock.invoice.onshipping'].with_context(
                active_ids=picking_ids).create({
                    'journal_type': 'sale',
                    'journal_id': self.journal_id.id,
                    'join_incoming_and_outgoing': True,
                    'group': True,
                    'force_user_id': self.env.user.id})
            inv_ids = ishipping.create_invoice()
            if len(inv_ids) > 1:
                raise exceptions.Warning(
                    _('The picking create more that one invoice, please '
                      'revise it'))
            invoice = self.env['account.invoice'].browse(inv_ids[0])
            # Reassign journal wizard (because has been overwritting by
            # '_create_invoice_from_picking' function of sale_order_type
            # module; it assigns sale journal project).
            invoice.write({'journal_id': self.journal_id.id})
            for line in invoice.invoice_line:
                if line.move_line_ids:
                    line.task_id = line.move_line_ids[0].task_id.id
        if not invoice and self.work_ids:
            account = self.project_id.analytic_account_id
            data = analytic_account_obj._prepare_cost_invoice(
                partner=self.partner_id,
                company_id=company_id,
                currency_id=account.pricelist_id.currency_id.id,
                analytic_lines=[l.work_id.hr_analytic_timesheet_id
                                for l in self.work_ids])
            data['type'] = 'out_invoice'
            invoice = self.env['account.invoice'].create(data)
        for line in self.work_ids:
            analytic = line.work_id.hr_analytic_timesheet_id
            data = analytic_account_obj.with_context(
                lang=self.partner_id.lang,
                force_company=company_id,
                company_id=company_id)._prepare_cost_invoice_line(
                    invoice_id=invoice.id,
                    product_id=analytic.product_id.id,
                    uom=analytic.product_uom_id.id,
                    user_id=analytic.user_id.id,
                    factor_id=analytic.to_invoice.id,
                    account=analytic.account_id,
                    analytic_lines=[analytic],
                    journal_type=self.journal_id.type,
                    data={'product': line.product_id.id})
            analytic.invoice_id = invoice.id
            data['name'] = line.name
            data['task_id'] = line.task_id.id
            data = self.create_invoice_line_task(
                data, invoice, analytic.product_id, self.partner_id)
            self.env['account.invoice.line'].create(data)
        return self.action_end(invoice)

    @api.multi
    def action_end(self, invoice):
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        action['domain'] = '[("id", "in", [%s])]' % invoice.id
        return action


class ProjectTaskCreateInvoiceWork(models.TransientModel):
    _name = 'project.task.create_invoice.work'
    _description = 'Create Invoice Work Line'

    wizard_id = fields.Many2one(
        comodel_name='project.task.create_invoice',
        string='Wizard')
    work_id = fields.Many2one(
        comodel_name='project.task.work',
        string='Work')
    name = fields.Char(
        string='Description',
        required=True)
    task_id = fields.Many2one(
        related='work_id.task_id',
        string='Task')
    product_id = fields.Many2one(
        related='work_id.product_id',
        string='Product')
    hours = fields.Float(
        string='Hours',
        realated='work_id.hours')
    date = fields.Datetime(
        string='Date',
        realated='work_id.date')
    user_id = fields.Many2one(
        comodel_name='res.users',
        realated='work_id.user_id',
        string='User')


class ProjectTaskCreatePicking(models.TransientModel):
    _name = 'project.task.create_invoice.picking'
    _description = 'Create Invoice Picking Line'

    wizard_id = fields.Many2one(
        comodel_name='project.task.create_invoice',
        string='Wizard')
    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Picking')
    name = fields.Char(
        string='Description',
        related='picking_id.name')
    sale_type_id = fields.Many2one(
        string='Description',
        related='picking_id.sale_type_id')
    origin = fields.Char(
        string='Origin',
        related='picking_id.origin')
