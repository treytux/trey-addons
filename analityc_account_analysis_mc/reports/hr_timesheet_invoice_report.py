# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import osv
from openerp.tools.sql import drop_view_if_exists


class report_timesheet_invoice(osv.osv):
    _inherit = 'report_timesheet.invoice'

    def init(self, cr):
        drop_view_if_exists(cr, 'report_timesheet_invoice')
        cr.execute("""
            create or replace view report_timesheet_invoice as (
                select
                    min(l.id) as id,
                    l.user_id as user_id,
                    l.account_id as account_id,
                    a.user_id as manager_id,
                    sum(l.unit_amount) as quantity,
                    sum(l.unit_amount * ip.value_float) as amount_invoice
                from account_analytic_line l
                    left join hr_timesheet_invoice_factor f on
                        (l.to_invoice=f.id)
                    left join account_analytic_account a on (l.account_id=a.id)
                    left join product_product p on (l.to_invoice=f.id)
                    left join product_template t on (l.to_invoice=f.id)
                    left join ir_property ip on (
                    ip.company_id=a.company_id AND res_id='product.template,
                    ' || t.id)
                where
                    l.to_invoice is not null and
                    l.invoice_id is null
                group by
                    l.user_id,
                    l.account_id,
                    a.user_id
            )
        """)
