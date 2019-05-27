# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, exceptions, _
from datetime import datetime


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    @api.cr_uid_ids_context
    def _next(self, cr, uid, seq_ids, context=None):
        if context is None:
            context = {}
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        sequences = self.browse(cr, uid, seq_ids, context=context)
        if 'fiscalyear_id' not in context:
            today = datetime.today()
            fiscalyear_ids = self.pool.get('account.fiscalyear').search(
                cr, uid, [
                    ('date_start', '<=', today),
                    ('date_stop', '>=', today),
                    ('company_id', '=', user.company_id.id)])
            if not fiscalyear_ids:
                raise exceptions.Warning(_(
                    'There is no defined fiscal year for the current date, '
                    'you must create it.'))
            context = context.copy()
            context['fiscalyear_id'] = fiscalyear_ids[0]
        company_id = (
            'current_company_id' in context and
            context['current_company_id'] or user.company_id.id)
        context = context.copy()
        context['force_company'] = company_id
        new_seqs = sequences.filtered(lambda s: s.company_id.id == company_id)
        return super(IrSequence, self)._next(cr, uid, new_seqs.ids, context)
