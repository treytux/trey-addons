###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import api, fields, models

_log = logging.getLogger(__name__)


class AccountInvoiceEdeLog(models.Model):
    _name = 'account.invoice.ede.log'
    _description = 'Ede invoice process log'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _rec_name = 'datetime'
    _order = 'datetime desc'

    datetime = fields.Datetime(
        string='Date',
        required=True,
        default=fields.Datetime.now,
    )
    log_line_ids = fields.One2many(
        comodel_name='account.invoice.ede.log.line',
        inverse_name='log_id',
        string='Log line',
    )
    state = fields.Selection(
        string='State',
        selection=[
            ('fail', 'Fail'),
            ('done_fail', 'Done with fail'),
            ('done', 'Done'),
        ],
        compute='_compute_line_counts',
        default='done',
        required=True,
    )
    line_fail_count = fields.Integer(
        string='Fail count',
        compute='_compute_line_counts',
    )
    line_done_count = fields.Integer(
        string='Done count',
        compute='_compute_line_counts',
    )

    @api.multi
    @api.depends('log_line_ids')
    def _compute_line_counts(self):
        for log in self:
            log.line_fail_count = len(self.mapped('log_line_ids').filtered(
                lambda l: l.state == 'fail'))
            log.line_done_count = len(self.mapped('log_line_ids').filtered(
                lambda l: l.state == 'done'))
            if log.line_fail_count != 0 and log.line_done_count != 0:
                log.state = 'done_fail'
            elif log.line_fail_count > 0:
                log.state = 'fail'
            log.state = 'done'
