###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models
from odoo.http import request


class Website(models.Model):
    _inherit = 'website'

    default_pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Default website pricelist',
        default=lambda self: self.env.ref('product.list0').id,
        required=True,
    )

    def get_current_pricelist(self):
        res = super().get_current_pricelist()
        available_pricelists = self.get_pricelist_available()
        if res != available_pricelists[0] or res == self.default_pricelist_id:
            return res
        pl = None
        partner = self.env.user.partner_id
        if request and request.session.get('website_sale_current_pl'):
            pl = self.env['product.pricelist'].browse(
                request.session['website_sale_current_pl'])
            if pl not in available_pricelists:
                pl = None
                request.session.pop('website_sale_current_pl')
        if not pl:
            pl = (
                partner.last_website_so_id.pricelist_id
                or partner.property_product_pricelist)
            if available_pricelists and pl not in available_pricelists:
                pl = self.default_pricelist_id
        return pl or res
