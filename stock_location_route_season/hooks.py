# Copyright 2018 David Vidal <david.vidal@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry, vals=None):
    env = api.Environment(cr, SUPERUSER_ID, {})
    route_mto = env.ref('stock.route_warehouse0_mto').copy()
    route_mto.write({
        'name': 'Make to Order Season',
        'is_season': True,
    })
