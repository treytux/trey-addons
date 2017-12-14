# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api
from openerp.tools.translate import _
import base64


class StockPickingDelivery(models.Model):
    _name = 'stock.picking.delivery'
    _description = 'Stock Picking Delivery'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Name',
        required=True,
        default=lambda self: self.picking_id and self.picking_id.name or '/')
    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Picking',
        domain='[("picking_type_code", "=", "outgoing")]',
        required=True)
    delivery_datetime = fields.Datetime(
        string='Delivery Datetime')
    delivery_person = fields.Char(
        string='Delivery Person',
        help='Info about person who has signed the delivery.')
    delivery_contact_id = fields.Many2one(
        comodel_name='res.partner',
        related='picking_id.partner_id',
        readonly=True,
        store=True,
        string='Delivery Contact',
        help='Picking\'s customer. Aceptation email will be sent to him.')
    company_id = fields.Many2one(
        comodel_name='res.company',
        related='picking_id.company_id',
        string='Company')
    token = fields.Char(
        string='Token',
        compute='_compute_token',
        store=True)
    state = fields.Selection(
        selection=[
            ('unanswered', _('Unanswered')),
            ('accepted', _('Accepted')),
            ('not_accepted', _('Not Accepted')),
        ],
        string='State',
        default='unanswered')

    @api.one
    def to_accepted(self):
        self.state = 'accepted'

    @api.one
    def to_not_accepted(self):
        self.state = 'not_accepted'

    @api.onchange('picking_id')
    def onchange_picking_id(self):
        if not self.picking_id:
            return
        self.name = '-'.join(['D', self.picking_id.name])

    @api.one
    @api.depends('name', 'delivery_datetime', 'picking_id')
    def _compute_token(self):
        token = base64.b64encode(
            bytes('-'.join(
                [self.name, self.delivery_datetime, str(self.picking_id.id)])))
        self.token = token

    @api.one
    def subscribe_delivery_partners(self):
        if self.delivery_contact_id not in self.message_follower_ids:
            self.message_subscribe([self.delivery_contact_id.id])
        if not self.delivery_contact_id.user_id:
            return
        if (self.delivery_contact_id.user_id.partner_id not in
                self.message_follower_ids):
            self.message_subscribe(
                [self.delivery_contact_id.user_id.partner_id.id])

    @api.model
    def create(self, values):
        res = super(StockPickingDelivery, self).create(values)
        picking = self.env['stock.picking'].browse(values['picking_id'])
        picking.delivery_id = res.id
        res.subscribe_delivery_partners()
        return res

    @api.one
    def write(self, values):
        res = super(StockPickingDelivery, self).write(values)
        if values.get('picking_id'):
            picking = self.env['stock.picking'].browse(values['picking_id'])
            picking.delivery_id = self.id
        self.subscribe_delivery_partners()
        return res

    @api.one
    def send_acceptation_email(self):
        template = self.env.ref(
            'stock_picking_delivery.'
            'stock_picking_delivery_email_template')
        template.send_mail(self.id, force_send=True)
        return True

    @api.model
    def cron_delivery_pending_email_reminder(self, days_notify):
        deliverys = self.env['stock.picking.delivery'].search([(
            'state', '=', 'unanswered')])
        template = self.env.ref(
            'stock_picking_delivery.'
            'stock_picking_delivery_email_reminder_template')
        for delivery in deliverys:
            template.send_mail(delivery.id, force_send=True)
        return True
