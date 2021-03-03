# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import _, api, models


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
            'debit': self.debit,
            'diff_credit': data['diff_credit'],
        })
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
            '|',
            ('partner_id', '=', self.id),
            ('partner_id', 'in', self.child_ids.ids),
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
            'work_pending': work_pending,
            'diff_credit': self.credit_limit - balance,
        }

    @api.multi
    def is_blocking(self, amount):
        self.ensure_one()
        has_allow_group = self.env.user.has_group(
            'sale_credit_limit.group_view_allow_sell_credit_limit')
        info = self.get_credit_limit_info(amount)
        if not has_allow_group and info['allow']:
            ntype = self.env.user.company_id.credit_limit_type
            if ntype == 'blocking':
                return True
        return False

    def get_info_balance(self, info):
        return '%.2f' % info.get('diff_credit', 0.0)

    @api.multi
    def fill_credit_note_msgs(self, order):
        self.ensure_one()
        has_allow_group = self.env.user.has_group(
            'sale_credit_limit.group_view_allow_sell_credit_limit')
        info = self.get_credit_limit_info(order.amount_total)
        info_balance = self.get_info_balance(info)
        msg = []
        if info['allow']:
            ntype = self.env.user.company_id.credit_limit_type
            msg.append(_(
                'Partner \'%s\' has exceeded the credit limit.') % self.name)
            msg.append(_(
                'The balance is greater than credit limit: %s > %s') % (
                    info['balance'], self.credit_limit))
            if ntype == 'blocking' and not has_allow_group:
                msg.append(_('You are not authorized to confirm the order.'))
        return (
            self.credit_limit - info.get('balance', 0.0), info_balance,
            '%s' % '\n'.join(msg))

    @api.multi
    def check_warning_credit_limit(self, order):
        self.ensure_one()
        info = self.get_credit_limit_info(order and order.amount_total or 0.0)
        if info.get('diff_credit') < 0 and self.credit_limit:
            msg = _('Credit limit exceeded for partner \'%s\'!') % self.name
            return {
                'warning': {
                    'title': _('Warning'),
                    'message': msg,
                }
            }
        return {}
