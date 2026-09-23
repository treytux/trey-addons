###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import SUPERUSER_ID, api

_log = logging.getLogger(__name__)


def migrate(cr, version):
    _log.info('Version: %s' % version)
    env = api.Environment(cr, SUPERUSER_ID, {})
    sale_session_with_close = env['sale.session'].search([
        ('close_cash_count_ids', '!=', False),
    ])
    # Migrate close cash count lines
    for sale_session in sale_session_with_close:
        old_cash_counts = sale_session.close_cash_count_ids
        cash_count_new = env['sale.session.cash_count'].create({
            'session_id': sale_session.id,
            'journal_id': sale_session.team_id.cash_payment_journal_id.id,
            'type': 'close',
        })
        for cash_count in old_cash_counts:
            query = '''SELECT value_2remove, quantity_2remove
                FROM sale_session_cash_count WHERE id = %s'''
            cr.execute(query, (cash_count.id, ))
            res = cr.fetchall()[0]
            env['sale.session.cash_count_line'].create({
                'cash_count_id': cash_count_new.id,
                'value': res[0],
                'quantity': res[1],
            })
            cash_count.unlink()
    # Migrate open cash count lines
    sale_session_with_open = env['sale.session'].search([
        ('open_cash_count_ids', '!=', False),
    ])
    for sale_session in sale_session_with_open:
        old_cash_counts = sale_session.open_cash_count_ids
        cash_count_new = env['sale.session.cash_count'].create({
            'session_id': sale_session.id,
            'journal_id': sale_session.team_id.cash_payment_journal_id.id,
            'type': 'open',
        })
        for cash_count in old_cash_counts:
            query = '''SELECT value_2remove, quantity_2remove
                FROM sale_session_cash_count WHERE id = %s'''
            cr.execute(query, (cash_count.id, ))
            res = cr.fetchall()[0]
            env['sale.session.cash_count_line'].create({
                'cash_count_id': cash_count_new.id,
                'value': res[0],
                'quantity': res[1],
            })
            cash_count.unlink()
    cr.execute('''
        ALTER TABLE sale_session_cash_count DROP COLUMN value_2remove;
        ALTER TABLE sale_session_cash_count DROP COLUMN quantity_2remove;
    ''')
