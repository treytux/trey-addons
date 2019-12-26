# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, exceptions, _
from openerp import SUPERUSER_ID
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

    def _procure_orderpoint_confirm(
            self, cr, uid, use_new_cursor=False, company_id=False,
            context=None):
        stock_manager_group_id = self.pool.get(
            'ir.model.data').xmlid_to_res_id(
                cr, uid, 'stock.group_stock_manager')
        user = self.pool.get('res.users').browse(cr, uid, uid)
        if user.id == SUPERUSER_ID or user.company_id.id != company_id:
            user_ids = self.pool.get('res.users').search(cr, uid, [
                ('id', '!=', SUPERUSER_ID),
                ('groups_id', 'in', [stock_manager_group_id]),
                ('company_id', 'in', [company_id])], order='id asc')
            uid = user_ids and user_ids[0] or False
        if uid is False:
            raise exceptions.Warning(_(
                'No user was found in company %s that belongs to the group '
                '\'Warehouse manager\' and is not the super user.') % (
                self.pool.get('res.company').browse(cr, uid, company_id)))
        return super(ProcurementOrder, self)._procure_orderpoint_confirm(
            cr, uid, use_new_cursor, company_id, context)
