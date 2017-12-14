# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
import logging
from openerp.osv import osv, fields
from openerp.addons.decimal_precision import decimal_precision as dp

_logger = logging.getLogger(__name__)


class account_analytic_account(osv.osv):
    _inherit = "account.analytic.account"

    def _analysis_all(self, cr, uid, ids, fields, arg, context=None):
        dp = 2
        res = dict([(i, {}) for i in ids])
        # We don't want consolidation for each of these fields because those
        # complex computation is resource-greedy.
        parent_ids = tuple(ids)
        accounts = self.browse(cr, uid, ids, context=context)

        for f in fields:
            if f == 'user_ids':
                cr.execute('SELECT MAX(id) FROM res_users')
                max_user = cr.fetchone()[0]
                if parent_ids:
                    cr.execute(
                        'SELECT DISTINCT("user") FROM '
                        'account_analytic_analysis_summary_user '
                        'WHERE account_id IN %s AND unit_amount <> 0.0',
                        (parent_ids,))
                    result = cr.fetchall()
                else:
                    result = []
                for id in ids:
                    res[id][f] = [int((id * max_user) + x[0]) for x in result]
            elif f == 'month_ids':
                if parent_ids:
                    cr.execute(
                        'SELECT DISTINCT(month_id) FROM '
                        'account_analytic_analysis_summary_month '
                        'WHERE account_id IN %s AND unit_amount <> 0.0',
                        (parent_ids,))
                    result = cr.fetchall()
                else:
                    result = []
                for id in ids:
                    res[id][f] = [
                        int(id * 1000000 + int(x[0])) for x in result]
            elif f == 'last_worked_invoiced_date':
                for id in ids:
                    res[id][f] = False
                if parent_ids:
                    cr.execute(
                        "SELECT account_analytic_line.account_id, MAX(date) "
                        "   FROM account_analytic_line "
                        "   WHERE account_id IN %s "
                        "         AND invoice_id IS NOT NULL "
                        "   GROUP BY account_analytic_line.account_id;",
                        (parent_ids,))
                    for account_id, sum in cr.fetchall():
                        if account_id not in res:
                            res[account_id] = {}
                        res[account_id][f] = sum
            elif f == 'ca_to_invoice':
                for id in ids:
                    res[id][f] = 0.0
                res2 = {}
                for account in accounts:
                    cr.execute("""
                        SELECT product_id, sum(amount), user_id, to_invoice,
                        sum(unit_amount), product_uom_id, line.name
                        FROM account_analytic_line line
                            LEFT JOIN account_analytic_journal journal ON
                            (journal.id = line.journal_id)
                        WHERE account_id = %s
                            AND journal.type != 'purchase'
                            AND invoice_id IS NULL
                            AND to_invoice IS NOT NULL
                        GROUP BY product_id, user_id, to_invoice,
                            product_uom_id, line.name""", (account.id,))

                    res[account.id][f] = 0.0
                    for (product_id, price, user_id, factor_id, qty,
                         uom, line_name) in cr.fetchall():
                        price = -price
                        if product_id:
                            price = self.pool.get(
                                'account.analytic.line')._get_invoice_price(
                                cr, uid, account, product_id, user_id,
                                qty, context)
                        factor = self.pool.get(
                            'hr_timesheet_invoice.factor').browse(
                            cr, uid, factor_id, context=context)
                        res[account.id][f] += (price * qty * (
                            100 - factor.factor or 0.0) / 100.0)

                # sum both result on account_id
                for id in ids:
                    res[id][f] = (round(res.get(id, {}).get(f, 0.0), dp) +
                                  round(res2.get(id, 0.0), 2))
            elif f == 'last_invoice_date':
                for id in ids:
                    res[id][f] = False
                if parent_ids:
                    cr.execute(
                        """SELECT account_analytic_line.account_id,
                            DATE(MAX(account_invoice.date_invoice))
                        FROM account_analytic_line
                        JOIN account_invoice ON
                          account_analytic_line.invoice_id = account_invoice.id
                        WHERE account_analytic_line.account_id IN %s
                            AND account_analytic_line.invoice_id IS NOT NULL
                        GROUP BY account_analytic_line.account_id""",
                        (parent_ids,))
                    for account_id, lid in cr.fetchall():
                        res[account_id][f] = lid
            elif f == 'last_worked_date':
                for id in ids:
                    res[id][f] = False
                if parent_ids:
                    cr.execute(
                        """SELECT account_analytic_line.account_id, MAX(date)
                            FROM account_analytic_line
                            WHERE account_id IN %s
                                AND invoice_id IS NULL
                            GROUP BY account_analytic_line.account_id""",
                        (parent_ids,))
                    for account_id, lwd in cr.fetchall():
                        if account_id not in res:
                            res[account_id] = {}
                        res[account_id][f] = lwd
            elif f == 'hours_qtt_non_invoiced':
                for id in ids:
                    res[id][f] = 0.0
                if parent_ids:
                    cr.execute(
                        """SELECT account_analytic_line.account_id,
                            COALESCE(SUM(unit_amount), 0.0)
                            FROM account_analytic_line
                            JOIN account_analytic_journal ON
                                account_analytic_line.journal_id =
                                    account_analytic_journal.id
                            WHERE account_analytic_line.account_id IN %s
                                AND account_analytic_journal.type='general'
                                AND invoice_id IS NULL
                                AND to_invoice IS NOT NULL
                            GROUP BY account_analytic_line.account_id;""",
                        (parent_ids,))
                    for account_id, sua in cr.fetchall():
                        if account_id not in res:
                            res[account_id] = {}
                        res[account_id][f] = round(sua, dp)
                for id in ids:
                    res[id][f] = round(res[id][f], dp)
            elif f == 'hours_quantity':
                for id in ids:
                    res[id][f] = 0.0
                if parent_ids:
                    cr.execute(
                        """SELECT account_analytic_line.account_id,
                            COALESCE(SUM(unit_amount), 0.0)
                        FROM account_analytic_line
                        JOIN account_analytic_journal
                            ON account_analytic_line.journal_id =
                                account_analytic_journal.id
                        WHERE account_analytic_line.account_id IN %s
                            AND account_analytic_journal.type='general'
                        GROUP BY account_analytic_line.account_id""",
                        (parent_ids,))
                    ff = cr.fetchall()
                    for account_id, hq in ff:
                        if account_id not in res:
                            res[account_id] = {}
                        res[account_id][f] = round(hq, dp)
                for id in ids:
                    res[id][f] = round(res[id][f], dp)
            elif f == 'ca_theorical':
                # TODO Take care of pricelist and purchase !
                for id in ids:
                    res[id][f] = 0.0
                # Warning
                # This computation doesn't take care of pricelist !
                # Just consider list_price
                if parent_ids:
                    cr.execute(
                        """SELECT account_analytic_line.account_id AS
                            account_id,
                            COALESCE(SUM(
                                (account_analytic_line.unit_amount *
                                ip.value_float)
                            - (account_analytic_line.unit_amount *
                            ip.value_float * hr.factor)), 0.0) AS somm
                            FROM account_analytic_line
                            LEFT JOIN account_analytic_journal
                                ON (account_analytic_line.journal_id =
                                    account_analytic_journal.id)
                            JOIN product_product pp
                                ON (account_analytic_line.product_id = pp.id)
                            JOIN product_template pt
                                ON (pp.product_tmpl_id = pt.id)
                            JOIN ir_property ip
                            ON (ip.company_id =
                                account_analytic_journal.company_id AND
                                res_id='product.template,' || pt.id)
                            JOIN account_analytic_account a
                                ON (a.id=account_analytic_line.account_id)
                            JOIN hr_timesheet_invoice_factor hr
                                ON (hr.id=a.to_invoice)
                            WHERE account_analytic_line.account_id
                            IN %s
                            AND a.to_invoice IS NOT NULL
                            AND account_analytic_journal.type IN
                                ('purchase', 'general')
                            GROUP BY
                            account_analytic_line.account_id """,
                        (parent_ids,))
                    for account_id, sum in cr.fetchall():
                        res[account_id][f] = round(sum, dp)
        return res

    _columns = {
        'ca_to_invoice': fields.function(
            _analysis_all,
            multi='analytic_analysis',
            type='float',
            string='Uninvoiced Amount',
            help="If invoice from analytic account, the remaining amount you "
                 "can invoice to the customer based on the total costs.",
            digits_compute=dp.get_precision('Account')),
        'ca_theorical': fields.function(
            _analysis_all,
            multi='analytic_analysis',
            type='float',
            string='Theoretical Revenue',
            help="Based on the costs you had on the project, what would have "
                 "been the revenue if all these costs have been invoiced at "
                 "the normal sale price provided by the pricelist.",
            digits_compute=dp.get_precision('Account')),
        'hours_quantity': fields.function(
            _analysis_all,
            multi='analytic_analysis',
            type='float',
            string='Total Worked Time',
            help="Number of time you spent on the analytic account (from "
                 "timesheet). It computes quantities on all journal of type "
                 "'general'."),
        'last_invoice_date': fields.function(
            _analysis_all,
            multi='analytic_analysis',
            type='date',
            string='Last Invoice Date',
            help="If invoice from the costs, this is the date of the "
                 "latest invoiced."),
        'last_worked_invoiced_date': fields.function(
            _analysis_all,
            multi='analytic_analysis',
            type='date',
            string='Date of Last Invoiced Cost',
            help="If invoice from the costs, this is the date of the latest "
                 "work or cost that have been invoiced."),
        'last_worked_date': fields.function(
            _analysis_all,
            multi='analytic_analysis',
            type='date',
            string='Date of Last Cost/Work',
            help="Date of the latest work done on this account."),
        'hours_qtt_non_invoiced': fields.function(
            _analysis_all,
            multi='analytic_analysis',
            type='float',
            string='Uninvoiced Time',
            help="Number of time (hours/days) (from journal of type "
                 "'general') that can be invoiced if you invoice based on "
                 "analytic account."),
        'month_ids': fields.function(
            _analysis_all,
            multi='analytic_analysis',
            type='many2many',
            relation='account_analytic_analysis.summary.month',
            string='Month'),
        'user_ids': fields.function(
            _analysis_all,
            multi='analytic_analysis',
            type="many2many",
            relation='account_analytic_analysis.summary.user',
            string='User'),
    }
