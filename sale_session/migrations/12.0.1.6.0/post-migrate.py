###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import SUPERUSER_ID, api

_log = logging.getLogger(__name__)


def migrate(cr, version):
    _log.info('Version: %s' % version)
    env = api.Environment(cr, SUPERUSER_ID, {})
    payments = env['account.payment'].search([
        ('invoice_ids', '!=', None),
        ('partner_id', '=', None),
        ('partner_type', '=', 'customer'),
    ])
    payments_count = len(payments)
    _log.info('Payments to update: %s' % payments_count)
    for payment in payments:
        payments_count -= 1
        partner = (payment.invoice_ids and payment.invoice_ids[0].partner_id
                   or False)
        moves = payment.mapped('move_line_ids').filtered(
            lambda l: l.full_reconcile_id)
        if not partner:
            _log.error('Not partner payment:%s' % payment.name)
            continue
        if moves:
            moves.remove_move_reconcile()
        invoices = payment.mapped('invoice_ids').filtered(
            lambda i: i.state in ('paid', 'draft', 'cancel'))
        if invoices:
            try:
                for invoice in invoices:
                    if invoice.state == 'cancel':
                        invoice.action_invoice_draft()
                        invoice.action_invoice_open()
                    elif invoice.state == 'draft':
                        invoice.action_invoice_open()
                    elif invoice.state == 'paid':
                        invoice.action_invoice_cancel()
                        invoice.action_invoice_draft()
                        invoice.action_invoice_open()
            except Exception as e:
                _log.error('Error update invoice: %s error: %s' % (
                    invoice.number, e))
                continue
        try:
            _log.info('Partner: %s process to payment: %s' % (
                partner.name, payment.name))
            payment.sudo().action_draft()
            payment.sudo().partner_id = partner
            payment.sudo().post()
            _log.info('Partner: %s assigned to payment: %s' % (
                partner.name, payment.name))
        except Exception as e:
            _log.error('Error update payment: %s error: %e' % (
                payment.name, e))
            continue
        _log.info('remaining payments to be updated: %s' % payments_count)
