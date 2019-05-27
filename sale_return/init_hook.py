###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging
_log = logging.getLogger(__name__)


def pre_init_hook(cr):
    refactor_qty_to_change_field(cr)


def refactor_qty_to_change_field(cr):
    cr.execute('''
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name='sale_order_line' AND
        column_name='qty_to_change' ''')
    if not cr.fetchone():
        return
    _log.info('Move values from qty_to_change to qty_change')
    cr.execute('''
        UPDATE sale_order_line sl
        SET qty_change = qty_to_change''')
