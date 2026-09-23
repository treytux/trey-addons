###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################


def migrate(cr, version):
    if not version:
        return
    cr.execute('''
        ALTER TABLE product_team_pricelist
        RENAME COLUMN commission TO market_commission_percent
    ''')
