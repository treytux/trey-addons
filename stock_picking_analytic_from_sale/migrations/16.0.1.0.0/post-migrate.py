###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    orders = env['sale.order'].search([
        ('state', 'in', ('sale', 'done')),
        ('analytic_account_id', '!=', False),
    ])
    for order in orders:
        order._propagate_analytic_to_pickings()
