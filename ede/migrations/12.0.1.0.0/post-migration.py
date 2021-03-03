###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import odoo


def migrate(cr, version):
    registry = odoo.registry(cr.dbname)
    from odoo.addons.ede.models.purchase_order import migrate_sale_order_id
    migrate_sale_order_id(cr, registry)
