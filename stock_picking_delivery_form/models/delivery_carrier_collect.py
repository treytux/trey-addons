# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _


class StockPickingDelivery(models.Model):
    _name = 'delivery.carrier.collect'
    _description = 'Delivery Carrier Collect'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Code',
        default=lambda s: s.env['ir.sequence'].get('carrier.collect'),
        required=True)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('done', 'Done')],
        string='State',
        default='draft',
        readonly=True,
        track_visibility='onchange')
    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Carrier')
    date_collect = fields.Datetime(
        string='Date Collect')
    picking_ids = fields.One2many(
        comodel_name='stock.picking',
        inverse_name='collect_id',
        string='Pickings')
    packages_total = fields.Float(
        compute='_compute_packages_total',
        string='Total packages')

    @api.one
    @api.depends('picking_ids')
    def _compute_packages_total(self):
        self.packages_total = sum([
            p.number_of_packages for p in self.picking_ids])

    @api.multi
    def name_get(self):
        def name(collect):
            return '[%s] %s' % (collect.name, collect.carrier_id.name or '')

        return [(r.id, name(r)) for r in self]

    @api.one
    def action_refresh(self):
        self.picking_ids = [(6, 0, [])]
        pickings = self.env['stock.picking'].search([
            ('collect_id', '=', False),
            ('carrier_id', '=', self.carrier_id.id)])
        self.picking_ids = [(6, 0, pickings.ids)]

    @api.one
    def action_done(self):
        if not self.picking_ids:
            raise exceptions.Warning(
                _('Error'), _('You must asign one or more pickings'))
        self.date_collect = fields.Datetime.now()
        self.state = 'done'
        return self.action_print()

    @api.one
    def action_to_draft(self):
        self.date_collect = None
        self.state = 'draft'

    @api.multi
    def action_print(self):
        report_name = 'stock_picking_delivery_form.carrier_collect'
        return {
            'type': 'ir.actions.report.xml',
            'report_name': report_name,
            'datas': dict(ids=self.ids)}
