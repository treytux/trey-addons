###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################


def migrate(cr, version):
    cr.execute('''
        ALTER TABLE sale_session_cash_count ADD value_2remove float;
        UPDATE sale_session_cash_count SET value_2remove = value;
        ALTER TABLE sale_session_cash_count ADD quantity_2remove float;
        UPDATE sale_session_cash_count SET quantity_2remove = quantity;
    ''')
