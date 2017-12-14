# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api, _
from logging import getLogger
_log = getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'

    route_id = fields.Many2one(
        string='Route',
        comodel_name='route')
    route_sequence = fields.Integer(
        string='Route sequence')
    last_visit = fields.Datetime(
        string='Last visit',
        readonly=True,
        compute='_compute_last_visit')
    last_visit_ago = fields.Char(
        string='Last visit',
        readonly=True,
        compute='_compute_last_visit_ago')
    pending_order = fields.Boolean(
        string='Pending Order',
        store=True,
        compute='_compute_pending_order')
    visits_count = fields.Integer(
        string='Visits',
        compute='_compute_visits_count')

    @api.one
    def _compute_last_visit(self):
        visit = self.env['partner.visit'].search(
            [('partner_id', '=', self.id)], order='date DESC', limit=1)
        if visit:
            self.last_visit = visit.date

    @api.one
    @api.depends('last_visit')
    def _compute_last_visit_ago(self):
        try:
            from ago import human
        except ImportError:
            _log.error('Module python "ago" is not installed, please install '
                       'with "pip install ago"')

        if self.last_visit:
            self.last_visit_ago = human(
                fields.Datetime.from_string(self.last_visit),
                past_tense=_('{0} ago'),
                future_tense=_('{0} from now'))
        else:
            self.last_visit_ago = _('Never')

    @api.one
    @api.depends('sale_order_ids')
    def _compute_pending_order(self):
        order_draft_ids = [
            o.id for o in self.sale_order_ids if o.state == 'draft']
        if len(order_draft_ids):
            self.pending_order = True
        else:
            self.pending_order = False

    @api.one
    def _compute_visits_count(self):
        count = self.env['partner.visit'].search(
            [('partner_id', '=', self.id)])
        self.visits_count = len(count)
