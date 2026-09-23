###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################


def migrate(cr, version):
    cr.execute('''
        UPDATE crm_team SET
        cash_payment_journal_id = default_payment_journal_id,
        cash_min_for_open_session = cash_money_balance_start
        ;
    ''')
