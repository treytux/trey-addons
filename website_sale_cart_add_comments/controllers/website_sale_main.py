# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

import openerp.addons.website_sale.controllers.main as main

from openerp import SUPERUSER_ID
from openerp.http import request

import logging
_log = logging.getLogger(__name__)


class WebsiteSale(main.website_sale):

    def checkout_values(self, data=None):
        result = super(WebsiteSale, self).checkout_values(data=data)

        result['checkout']['comments_order'] = \
            data.get('comments_order', None) if data else None

        return result

    def checkout_form_save(self, checkout):
        result = super(WebsiteSale, self).checkout_form_save(checkout)

        if 'comments_order' in checkout and checkout['comments_order']:
            cr, context = request.cr, request.context
            order_obj = request.registry.get('sale.order')

            order = request.website.sale_get_order(force_create=1,
                                                   context=context)

            order_obj.write(cr, SUPERUSER_ID, [order.id], {
                'note': checkout['comments_order']
            }, context=context)

        return result
