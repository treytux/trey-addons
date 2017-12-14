# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, _
import logging
_log = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def open_wizard_credit_limit(self):
        self.ensure_one()
        data = self.get_credit_limit_info()
        wiz = self.env['wiz.compute.credit_limit'].create({
            'partner_id': self.id,
            'picking_pending': data['picking_pending'],
            'work_pending': data['work_pending'],
            'credit': self.credit,
            'debit': self.debit})
        for picking in data['pickings']:
            wiz.picking_ids.create({
                'wizard_id': wiz.id,
                'picking_id': picking.id})
        for work in data['works']:
            wiz.work_ids.create({
                'wizard_id': wiz.id,
                'work_id': work.id})
        view = self.env.ref('sale_credit_limit.wiz_compute_credit_limit')
        return {
            'name': _('Credit limit details'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [view.id],
            'res_model': 'wiz.compute.credit_limit',
            'res_id': wiz.id,
            'type': 'ir.actions.act_window',
            'target': 'new'}

    @api.multi
    def get_credit_limit_info(self, amount=0):
        self.ensure_one()
        pickings = self.env['stock.picking'].search([
            ('partner_id', '=', self.id),
            ('invoice_state', '=', '2binvoiced'),
            ('state', 'in', ['done'])])
        multiply = {'incoming': -1, 'outgoing': 1, 'internal': 0}
        picking_pending = sum([
            multiply[p.picking_type_id.code] * p.invoice_total
            for p in pickings])
        works = self.env['account.analytic.line'].search([
            ('partner_id', '=', self.id),
            ('invoice_id', '=', False)])
        for w in works:
            price = w._get_invoice_price(
                w.account_id, w.product_id.id, self.env.user.id, w.unit_amount)
            w.amount = price
        work_pending = sum([w.amount for w in works])
        balance = self.credit + picking_pending + work_pending + amount
        return {
            'balance': balance,
            'allow': bool(
                self.credit_limit != 0 and self.credit_limit < balance),
            'pickings': pickings,
            'picking_pending': picking_pending,
            'works': works,
            'work_pending': work_pending}
