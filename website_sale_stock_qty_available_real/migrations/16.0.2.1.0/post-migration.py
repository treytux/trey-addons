###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################


def migrate(cr, version):
    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'website'
            AND column_name = 'website_sale_stock_use_qty_available_real'
    """)
    if not cr.fetchone():
        return
    cr.execute("""
        UPDATE website
        SET website_sale_stock_qty_mode = CASE
            WHEN website_sale_stock_use_qty_available_real THEN 'real'
            ELSE 'available'
        END
        WHERE website_sale_stock_use_qty_available_real
            OR website_sale_stock_qty_mode IS NULL
    """)
