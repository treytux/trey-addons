# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api, _
from openerp.exceptions import Warning
from openerp.addons.website_sale.controllers import main
import logging

_log = logging.getLogger(__name__)


class website(models.Model):
    _inherit = 'website'

    shop_products_per_page = fields.Integer(
        string=u'Products per page',
        default=20
    )

    @api.one
    @api.constrains('shop_products_per_page')
    def _check_seats_limit(self):
        if self.shop_products_per_page <= 0:
            raise Warning(_('Products per page must be greater than zero.'))

    def read(self, cr, user, ids, fields=None, context=None,
             load='_classic_read'):
        r = super(website, self).read(cr, user, ids, fields, context, load)
        if 'shop_products_per_page' in r[0]:
            main.__dict__['PPG'] = r[0]['shop_products_per_page']
        # Si devuelve un list index out of... sustituir por estas líneas
        # r = super(website, self).read(
        #     cr, user, ids, fields=fields, context=context, load=load)
        # if r and 'shop_products_per_page' in r[0]:
        #         main.__dict__['PPG'] = r[0]['shop_products_per_page']
        return r
