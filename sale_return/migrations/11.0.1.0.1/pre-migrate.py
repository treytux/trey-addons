###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################


def migrate(cr, version):
    cr.execute('''
        ALTER TABLE sale_order_line RENAME COLUMN qty_to_change
        TO qty_change''')
