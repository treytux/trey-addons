# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import SUPERUSER_ID
from openerp.osv import orm
from openerp.addons.web.http import request


class Website(orm.Model):
    _inherit = 'website'

    def sale_get_order(self, cr, uid, ids, force_create=False, code=None,
                       update_pricelist=None, context=None):
        SaleOrder = self.pool['sale.order']
        sale_order_id = request.session.get('sale_order_id')

        if not sale_order_id:
            # buscamos si existe un sale order para el partner en borrador
            partner = self.pool['res.users'].browse(cr, SUPERUSER_ID, uid,
                                                    context=context).partner_id

            for website in self.browse(cr, uid, ids):
                section_id = self.pool.get('ir.model.data') \
                    .get_object_reference(
                        cr, uid, 'website', 'salesteam_website_sales')[1]

                domain = [
                    # ('user_id', '=', website.user_id.id),
                    ('state', '=', 'draft'),
                    ('partner_id', '=', partner.id),
                    ('pricelist_id', '=',
                     partner.property_product_pricelist.id),
                    ('section_id', '=', section_id)]

                so = SaleOrder.search(cr, SUPERUSER_ID, domain,
                                      order='date_order DESC')
                if len(so) > 0:
                    request.session['sale_order_id'] = so[0]

        return super(Website, self).sale_get_order(
            cr, uid, ids, force_create, code, update_pricelist, context)
