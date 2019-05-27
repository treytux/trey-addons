###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, tools


class Website(models.Model):
    _inherit = 'website'

    @tools.ormcache(
        'self.env.uid', 'country_code', 'show_visible', 'website_pl',
        'current_pl', 'all_pl', 'partner_pl', 'order_pl')
    def _get_pl_partner_order(
        self, country_code, show_visible, website_pl, current_pl, all_pl,
        partner_pl=False, order_pl=False
    ):
        res = super(Website, self)._get_pl_partner_order(
            country_code=country_code, show_visible=show_visible,
            website_pl=website_pl, current_pl=current_pl, all_pl=all_pl,
            partner_pl=partner_pl, order_pl=order_pl)
        res += self.env.user.partner_id.website_pricelist_ids.ids
        return list(set(res))
