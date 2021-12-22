###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################


def migrate(cr, version):
    cr.execute('''
        ALTER TABLE product_template RENAME COLUMN margin TO margin_2remove''')
