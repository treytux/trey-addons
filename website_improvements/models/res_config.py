# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp.osv import fields, osv


class website_config_settings(osv.osv_memory):
    _inherit = 'website.config.settings'

    _columns = {
        'website_id': fields.many2one('website', string="website",
                                      required=True),
        'shop_products_per_page': fields.related(
            'website_id',
            'shop_products_per_page',
            type="integer",
            string='Products per page'),
    }

    _defaults = {
        'shop_products_per_page': 20,
        'website_id': lambda self, cr, uid, c:
        self.pool.get('website').search(cr, uid, [], context=c)[0],
    }

    def on_change_website_id(self, cr, uid, ids, website_id, context=None):
        website_data = self.pool.get('website').read(cr, uid, [website_id], [],
                                                     context=context)[0]
        values = {}
        for fname, v in website_data.items():
            if fname in self._columns:
                values[fname] = v[0] if v \
                    and self._columns[fname]._type == 'many2one' else v

        return {'value': values}

    # FIXME in trunk for god sake. Change the fields above to fields.char
    # instead of fields.related, and create the function set_website who
    # will set the value on the website_id create does not forward the
    # values to the related many2one. Write does.
    def create(self, cr, uid, vals, context=None):
        config_id = super(website_config_settings, self).create(
            cr, uid, vals, context=context)
        self.write(cr, uid, config_id, vals, context=context)
        return config_id
