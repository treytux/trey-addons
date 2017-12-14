# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import api, models, fields
import logging

_log = logging.getLogger(__name__)


class WorkOrder(models.Model):
    _name = 'repair.workorder'
    _description = 'Work order'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    def _get_user(self):
        return self.env.uid

    def _get_number(self):
        return self.env['ir.sequence'].get('repair.workorder') or '*'

    name = fields.Char(
        string=u'Code',
        readonly=True,
        default=_get_number
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Engineer',
        default=_get_user
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner'
    )
    line_ids = fields.One2many(
        comodel_name='repair.workorder.line',
        inverse_name='workorder_id',
        string='Products delivered'
    )
    consumed_ids = fields.One2many(
        comodel_name='repair.workorder.consumed',
        inverse_name='workorder_id',
        string='Product & Services consumed'
    )
    order_date = fields.Datetime(
        string='Order date',
        default=fields.Datetime.now
    )
    planned_start_date = fields.Datetime(
        string='Planned start date'
    )
    planned_end_date = fields.Datetime(
        string='Planned end date'
    )
    diagnostic = fields.Text(
        string='Diagnostic'
    )
    causes = fields.Text(
        string='Causes'
    )
    actions = fields.Text(
        string='Actions'
    )
    state = fields.Selection([
        ('draft', 'Pending'),
        ('in_progress', 'In progress'),
        ('warranty', 'Warranty'),
        ('done', 'Done'),
        ('canceled', 'Canceled')],
        string='State',
        default='draft'
    )

    @api.one
    def onchange_partner_id(self, partner_id):
        _log.info('-'*100)
        _log.info(partner_id)

    @api.one
    def button_draft(self):
        self.state = 'draft'

    @api.one
    def button_in_progress(self):
        self.state = 'in_progress'

    @api.one
    def button_in_progress_back(self):
        self.state = 'draft'

    @api.one
    def button_warranty(self):
        self.state = 'warranty'

    @api.one
    def button_warranty_back(self):
        self.state = 'draft'

    @api.one
    def button_done(self):
        self.state = 'done'

    @api.one
    def button_done_back(self):
        self.state = 'in_progress'

    @api.one
    def button_cancel(self):
        self.state = 'canceled'


class WorkOrderLine(models.Model):
    _name = 'repair.workorder.line'
    _description = 'Product to repair'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    workorder_id = fields.Many2one(
        comodel_name='repair.workorder',
        string='Work order')
    description = fields.Char(string='Description')
    quantity = fields.Float(string='Quantity', default=1.0)


class WorkOrderConsumed(models.Model):
    _name = 'repair.workorder.consumed'
    _description = 'Services for repair'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    workorder_id = fields.Many2one(
        comodel_name='repair.workorder',
        string='Work order'
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product'
    )
    type = fields.Selection([
        ('service', 'Service'),
        ('product', 'Product')],
        string='Type',
        required=True,
        default='service'
    )
    description = fields.Char(
        string='Description',
        required=True
    )
    quantity = fields.Float(
        string='Quantity',
        default=1
    )
    price_unit = fields.Float(
        string='Price unit'
    )
    subtotal = fields.Float(
        string='Subtotal',
        compute='compute_subtotal'
    )

    @api.one
    @api.depends('quantity', 'price_unit')
    def compute_subtotal(self):
        self.subtotal = self.quantity * self.price_unit

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.description = self.product_id.name
            self.type = 'service' if self.product_id.type == 'service' \
                else 'product'

            # @ TODO impuestos??
            # Obtener el precio del producto a partir de la tarifa del cliente
            self.price_unit = self.product_id.list_price
