# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api, exceptions, _
import logging
_log = logging.getLogger(__name__)


class StockInvoiceOnShipping(models.TransientModel):
    _inherit = 'stock.invoice.onshipping'

    @api.model
    def _get_usages(self, picking_ids):
        res = {}
        pickings = [p for p in self.env['stock.picking'].browse(picking_ids)
                    if p.invoice_state == '2binvoiced']
        partner = {}
        for pick in pickings:
            if not pick.partner_id:
                continue
            partner.setdefault(pick.partner_id.id, []).append(pick)
            ptype = pick.picking_type_id.code
            usage = (ptype == 'incoming' and
                     pick.move_lines[0].location_id.usage or
                     pick.move_lines[0].location_dest_id.usage)
            res[pick.id] = (ptype, usage)
        return res

    @api.model
    def _get_journal_type(self):
        picking_ids = self.env.context.get('active_ids', [])
        usages = self._get_usages(picking_ids)
        usage = list(set([u[1] for u in usages.values()]))
        if self.join_incoming_and_outgoing and len(usage) == 1 and \
           usage[0] == 'customer':
                return 'sale'
        return super(StockInvoiceOnShipping, self)._get_journal_type()

    @api.model
    def _check_picking(self):
        picking_ids = self.env.context.get('active_ids', [])
        if len(picking_ids) > 1:
            return True
        else:
            return False

    @api.model
    def _get_journal(self):
        journal_type = self._get_journal_type()
        journals = self.env['account.journal'].search(
            [('type', '=', journal_type)])
        return journals and journals[0] or False

    journal_type = fields.Selection(
        default=_get_journal_type)
    journal_id = fields.Many2one(
        domain="[('type', 'in', journal_type)]",
        default=_get_journal)
    join_incoming_and_outgoing = fields.Boolean(
        string='Join incoming and outgoing picking in the same out invoice',
        default=_check_picking)
    force_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Force Salesman')

    @api.multi
    def onchange_journal_id(self, journal_id):
        if self.journal_type != 'sale':
            return super(StockInvoiceOnShipping, self).onchange_journal_id(
                journal_id)
        return {}

    @api.multi
    def create_invoice(self):
        force_user_id = self.force_user_id and self.force_user_id.id or False
        invoice_ids = super(StockInvoiceOnShipping, self.with_context(
            force_user_id=force_user_id)).create_invoice()
        if not invoice_ids or not self.join_incoming_and_outgoing or \
           self.journal_type != 'sale':
            return invoice_ids
        invoices = self.env['account.invoice'].browse(invoice_ids)
        lines = [l for i in invoices for l in i.invoice_line]
        for line in lines:
            move = line.move_line_ids and line.move_line_ids[0] or None
            if not move:
                continue
            picking = (move and move.picking_id) and move.picking_id or None
            if not picking:
                continue
            if picking.picking_type_id.code == 'incoming':
                line.price_unit *= -1
        raise_tax = _(
            'The invoice for partner "%s" and origin "%s" generate a tax '
            'amount negative.')
        raise_total = _(
            'The invoice for partner "%s" and origin "%s" generate a total '
            'amount negative.')
        for invoice in invoices:
            if invoice.amount_tax < 0:
                raise exceptions.Warning(raise_tax % (
                    invoice.partner_id.name, invoice.origin))
            if invoice.amount_total < 0:
                raise exceptions.Warning(raise_total % (
                    invoice.partner_id.name, invoice.origin))
            invoice.button_reset_taxes()
        return invoice_ids
