# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, exceptions, _
from datetime import datetime


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    def run_scheduler(
            self, cr, uid, use_new_cursor=False, company_id=False,
            context=None):
        if context is None:
            context = {}
        today = datetime.today()
        fiscalyear_ids = self.pool.get('account.fiscalyear').search(
            cr, uid, [
                ('date_start', '<=', today),
                ('date_stop', '>=', today),
                ('company_id', '=', company_id)])
        if not fiscalyear_ids:
            raise exceptions.Warning(_(
                'There is no defined fiscal year for the current date, you '
                'must create it.'))
        context['fiscalyear_id'] = fiscalyear_ids[0]
        context['current_company_id'] = company_id
        super(ProcurementOrder, self).run_scheduler(
            cr, uid, use_new_cursor, company_id, context)
