###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        lines = env['sale.order.line'].search([('product_id', '!=', False)])
        for line in lines:
            line.vendor_id = (
                line.product_id.seller_ids
                and line.product_id.seller_ids[0].name.id or False)
    return
