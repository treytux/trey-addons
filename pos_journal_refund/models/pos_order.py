# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, exceptions, _
import logging
_log = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.multi
    def action_invoice(self):
        inv_ids = []
        inv_type = ''
        for order in self:
            session = order.session_id
            if not session.config_id.refund_journal_id or \
               order.amount_total >= 0:
                re = super(PosOrder, order).action_invoice()
                inv_type = 'out_invoice'
                inv_ids += [re['res_id']]
                continue
            inv_ids += order.action_invoice_refund()
            inv_type = 'out_refund'

        res = self.env['ir.model.data'].get_object_reference(
            'account', 'invoice_form')
        res_id = res and res[1] or False
        return {
            'name': _('Customer Invoice'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'account.invoice',
            'context': '{"type": "%s"}' % inv_type,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': inv_ids and inv_ids[0] or False}

    @api.multi
    def action_invoice_refund(self):
        self.ensure_one()
        order = self[0]
        inv_ref = self.env['account.invoice']
        inv_line_ref = self.env['account.invoice.line']
        product_obj = self.env['product.product']

        if order.invoice_id:
            return [order.invoice_id.id]
        if not order.partner_id:
            raise exceptions.Warning(
                _('Error!'),
                _('Please provide a partner for the sale.'))
        session = order.session_id
        inv_journal = (
            session.config_id.refund_journal_id and
            session.config_id.refund_journal_id.id or
            order.sale_journal.id)
        acc = order.partner_id.property_account_receivable.id
        data = {
            'name': order.name,
            'origin': order.name,
            'account_id': acc,
            'journal_id': inv_journal or None,
            'type': 'out_refund',
            'reference': order.name,
            'partner_id': order.partner_id.id,
            'comment': order.note or '',
            # considering partner's sale pricelist's currency
            'currency_id': order.pricelist_id.currency_id.id}
        data.update(inv_ref.onchange_partner_id(
            'out_invoice', order.partner_id.id)['value'])
        # FORWARDPORT TO SAAS-6 ONLY!
        data.update({'fiscal_position': False})
        if not data.get('account_id', None):
            data['account_id'] = acc
        inv = inv_ref.create(data)
        order.write({'invoice_id': inv.id, 'state': 'invoiced'})
        for line in order.lines:
            inv_line = {
                'invoice_id': inv.id,
                'product_id': line.product_id.id,
                'quantity': line.qty * -1}
            product = product_obj.browse(line.product_id.id)
            inv_name = product.name_get()[0][1]
            inv_line.update(inv_line_ref.product_id_change(
                line.product_id.id,
                line.product_id.uom_id.id,
                line.qty, partner_id=order.partner_id.id)['value'])
            if not inv_line.get('account_analytic_id', False):
                inv_line['account_analytic_id'] = \
                    self._prepare_analytic_account(line)
            inv_line['price_unit'] = line.price_unit
            inv_line['discount'] = line.discount
            inv_line['name'] = inv_name
            inv_line['invoice_line_tax_id'] = [
                (6, 0, inv_line['invoice_line_tax_id'])]
            inv_line_ref.create(inv_line)
        inv.button_reset_taxes()
        order.signal_workflow('invoice')
        inv.signal_workflow('validate')
        return [inv.id]
