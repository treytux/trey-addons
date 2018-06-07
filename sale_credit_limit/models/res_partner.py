# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, _


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
        def _delete_free_work_from_works_list(work, work_lines):
            index = None
            for i, move in enumerate(work_lines):
                if (work.id == move.id):
                    index = i
            work_lines.pop(index)
            return work_lines

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
            ('invoice_id', '=', False),
            ('to_invoice', '!=', False)])

        work_pending = 0
        work_lines = list(works)
        for w in works:
            work_pending += w.amount_to_invoiced
            if w.amount_to_invoiced == 0.0:
                work_lines = _delete_free_work_from_works_list(w, work_lines)

        balance = self.credit + picking_pending + work_pending + amount
        return {
            'balance': balance,
            'allow': bool(
                self.credit_limit != 0 and self.credit_limit < balance),
            'pickings': pickings,
            'picking_pending': picking_pending,
            'works': work_lines,
            'work_pending': work_pending}
