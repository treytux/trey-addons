# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    def _default_journal(self, cr, uid, context=None):
        order_obj = self.pool.get('pos.order')
        journal_ids = None
        if context.get('active_id', None):
            order = order_obj.browse(cr, uid, context['active_id'])
            journal_ids = [s.journal_id.id
                           for s in order.session_id.statement_ids]
            if order.session_id.config_id.default_journal_id:
                dj_id = order.session_id.config_id.default_journal_id.id
                if dj_id in journal_ids:
                    return dj_id
        return journal_ids and journal_ids[0] or None

    def _default_order(self):
        journal_ids = []
        if self.env.context.get('active_id', None):
            order = self.env['pos.order'].browse(self.env.context['active_id'])
            journal_ids = [s.journal_id.id
                           for s in order.session_id.statement_ids]
        return journal_ids

    domain_journal_ids = fields.Many2many(
        comodel_name='account.journal',
        relation='pos_make_payment2account_journal_rel',
        default=_default_order,
        readonly=True,
        column1='payment_id',
        column2='journal_id')

    _defaults = {
        'journal_id': _default_journal,
    }
