# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
import logging
_log = logging.getLogger(__name__)


class BookingInvoiceSummaryLine(models.Model):
    _name = 'booking.invoice.summary.line'
    _description = 'Booking Invoice Summary Line'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _rec_name = 'partner_id'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
    )
    invoice_ids = fields.Many2many(
        comodel_name='account.invoice',
        relation='booking_invoice_summary_account_invoice_rel',
        column1='invoice_id',
        column2='line_id',
        string='Invoices',
    )
    summary_id = fields.Many2one(
        comodel_name='booking.invoice.summary',
        string='Summary',
        required=True,
        ondelete='cascade',
    )
    amount_untaxed = fields.Float(
        string='Subtotal',
        digits=dp.get_precision('Account'),
        store=True,
        compute='_compute_amount',
    )
    amount_tax = fields.Float(
        string='Tax',
        digits=dp.get_precision('Account'),
        store=True,
        compute='_compute_amount'
    )
    amount_total = fields.Float(
        string='Total',
        digits=dp.get_precision('Account'),
        store=True,
        compute='_compute_amount'
    )
    is_send_email = fields.Boolean(
        string='Send Email',
        default=True,
    )
    attachment_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        string='Attachment',
        domain=[('res_model', '=', 'booking.invoice.summary.line')],
    )
    sent = fields.Boolean(
        readonly=True,
        default=False,
        copy=False,
    )
    state = fields.Selection(
        related='summary_id.state',
    )

    @api.multi
    @api.depends('attachment_ids')
    def _compute_is_excel(self):
        if len(self.attachment_ids) > 0:
            return True
        return False

    @api.multi
    @api.depends('invoice_ids')
    def _compute_amount(self):
        for line in self:
            out_invoices = line.mapped('invoice_ids').filtered(
                lambda i: i.type == 'out_invoice')
            out_refund = line.mapped('invoice_ids').filtered(
                lambda i: i.type == 'out_refund')
            line.amount_untaxed = sum(
                i.amount_untaxed for i in out_invoices) - sum(
                i.amount_untaxed for i in out_refund)
            line.amount_tax = sum(
                i.amount_tax for i in out_invoices) - sum(
                i.amount_tax for i in out_refund)
            line.amount_total = sum(
                i.amount_total for i in out_invoices) - sum(
                i.amount_total for i in out_refund)

    @api.multi
    def action_send_email_compose(self):
        self.ensure_one()
        if not self.is_send_email:
            return
        template = self.env.ref(
            'booking_invoice_summary.email_invoice_summary', False)
        if self.attachment_ids:
            template.attachment_ids = [(6, 0, [self.attachment_ids[0].id])]
        compose_form = self.env.ref(
            'mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='booking.invoice.summary.line',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            mark_line_as_sent=True,
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def action_send_email_background(self):
        self.ensure_one()
        template = self.env.ref(
            'booking_invoice_summary.email_invoice_summary', False)
        if self.attachment_ids:
            template.attachment_ids = [(6, 0, [self.attachment_ids[0].id])]
        template.send_mail(self.partner_id.id, force_send=True)
        _log.info(_('Send Invoice Summary to Customer: %s Line: %s' % (
            self.partner_id.name, self.id)))
        return
