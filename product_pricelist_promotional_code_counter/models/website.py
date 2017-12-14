# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api
from openerp.addons.web.http import request


class Website(models.Model):
    _inherit = 'website'

    @api.model
    def get_coupon_with_limit_applicable(self, code):
        pricelists = request.env['product.pricelist'].search([
            ('code', '=', code),
            ('code_counter', '>', 0),
            ('code_unique_partner', '=', False)])
        if pricelists:
            return pricelists and pricelists[0] or False

    @api.model
    def get_coupon_unique_partner_applicable(self, code):
        pricelists = request.env['product.pricelist'].search([
            ('code', '=', code),
            ('code_unique_partner', '=', True)])
        if not pricelists:
            return False
        if not request.session.uid:
            return False
        user = self.env['res.users'].browse(request.session.uid)
        coupons_number = pricelists[0].compute_coupons_number(user.partner_id)
        if coupons_number[0] > 0:
            return False
        return pricelists and pricelists[0] or False

    @api.model
    def sale_get_order(self, force_create=False, code=None,
                       update_pricelist=None, context=None):
        if not code:
            return super(Website, self).sale_get_order(
                force_create, code, update_pricelist)
        if self.get_coupon_with_limit_applicable(code):
            return super(Website, self).sale_get_order(
                force_create, code, update_pricelist)
        if self.get_coupon_unique_partner_applicable(code):
            return super(Website, self).sale_get_order(
                force_create, code, update_pricelist)
        return super(Website, self).sale_get_order(
            force_create=force_create, code=None,
            update_pricelist=None)
