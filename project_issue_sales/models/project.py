# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api, exceptions, _
import logging
_log = logging.getLogger(__name__)


class ProjectIssue(models.Model):
    _inherit = 'project.issue'

    @api.model
    def _get_number(self):
        return self.env['ir.sequence'].get('project.issue')

    number = fields.Char(
        string='Number',
        size=32,
        copy=False,
        default=_get_number)
    create_date = fields.Datetime(
        string='Creation Date',
        readonly=True)
    target_date = fields.Datetime(
        string='Target Resolution Date',
        track_visibility='onchange')
    line_ids = fields.One2many(
        comodel_name="project.issue.line",
        inverse_name="issue_id",
        string="Product Line",
        required=False)
    sale_id = fields.Many2one(
        comodel_name="sale.order",
        string="Sale Order",
        copy=False,
        required=False)
    order_ids = fields.One2many(
        comodel_name='sale.order',
        inverse_name='issue_id',
        string='Sale Orders')
    order_count = fields.Integer(
        string='Order count',
        compute='_compute_order_count')

    @api.one
    @api.depends('order_ids')
    def _compute_order_count(self):
        self.order_count = len(self.order_ids)

    @api.multi
    def sale_tree_view(self):
        return {
            'name': _('Sale Orders'),
            'domain': [('issue_id', '=', self.id)],
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': "{'default_res_model': '%s', "
                       "'default_res_id': %d, "
                       "'search_default_partner_id': %d, "
                       "'default_issue_id': %d, "
                       "'default_project_id': %d}" % (
                self._name,
                self.id,
                self.project_id.partner_id.id,
                self.id, self.project_id.analytic_account_id.id)}

    @api.multi
    def create_sale_order(self):
        if self.line_ids and not self.sale_id and self.partner_id:
            if not self.company_id.issue_sale_type_id:
                raise exceptions.Warning(
                    _('Error'),
                    _('Please select Sales Type for this company'))

            # Si esta instado el modulo warning, capturar el mensaje...
            order = self.env['sale.order'].search([], limit=1)
            res = order.onchange_partner_id(self.partner_id.id)
            if 'warning' in res:
                raise exceptions.Warning(
                    res['warning']['title'],
                    res['warning']['message'])

            sale_id = self.env['sale.order'].with_context(
                order_type=self.company_id.issue_sale_type_id.id).create({
                    'partner_id': self.partner_id.id or None,
                    'origin': '[%s]%s' % (self.number, self.name),
                    'type_id': self.company_id.issue_sale_type_id.id,
                    'company_id': self.company_id.id,
                    'client_order_ref': '[%s]%s' % (self.number, self.name),
                    'issue_id': self.id,
                    'project_id': self.project_id.analytic_account_id.id})
            for line in self.line_ids:
                data = self.env['sale.order.line'].product_id_change(
                    sale_id.pricelist_id.id, line.product_id.id,
                    qty=line.quantity, uom=False, qty_uos=0, uos=False,
                    name=line.product_id.name_template,
                    partner_id=sale_id.partner_id.id, lang=False,
                    update_tax=True, date_order=False, packaging=False,
                    fiscal_position=False, flag=False)['value']
                tax_ids = 'tax_id' in data and [(6, 0, data['tax_id'])] or []
                # dto = data.get('discount', 0.0)
                # if dto and 'decrease_dto_issue' in self.partner_id._fields:
                #     dto -= self.partner_id.decrease_dto_issue
                data.update({
                    'order_id': sale_id.id,
                    'issue_id': self.id,
                    'issue_line_id': line.id,
                    'name': line.product_id.name_template,
                    'tax_id': tax_ids,
                    # 'discount': dto > 0 and dto or 0.0,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity})
                self.env['sale.order.line'].with_context(
                    order_type=self.company_id.issue_sale_type_id.id).create(
                    data)
            self.sale_id = sale_id

    @api.multi
    def name_get(self):
        if isinstance(self.ids, (list, tuple)) and not len(self.ids):
            return []
        result = []
        for issue in self:
            name = "[%s]%s" % (issue.number, issue.name or '')
            result.append((issue.id, "%s" % (name or '')))
        return result

    @api.multi
    def write(self, values):
        if 'stage_id' in values:
            stage = self.env['project.task.type'].browse(
                values.get('stage_id'))
        else:
            stage = None
        if stage and stage.closed and self.line_ids and not self.sale_id:
            raise exceptions.Warning(
                _('Error!'),
                _('Please create sale order with products'))
        res = super(ProjectIssue, self).write(values)
        return res


class ProjectIssueLine(models.Model):
    _name = 'project.issue.line'
    _description = 'Issue Product Line'
    _order = 'sequence,id'

    sequence = fields.Integer(
        string="Sequence",
        required=False)
    issue_id = fields.Many2one(
        comodel_name="project.issue",
        string="Issue",
        required=True,
        ondelete='cascade')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        domain=[('sale_ok', '=', True)],
        change_default=True)
    lot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        string='Lot')
    quantity = fields.Float(
        string="Quantity",
        required=True,
        default=1)
