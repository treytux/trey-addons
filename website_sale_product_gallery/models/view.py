# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp.osv import osv


class View(osv.osv):
    _inherit = "ir.ui.view"

    def render(self, cr, uid, id_or_xml_id, values=None, engine='ir.qweb',
               context={}):
        ctx = context.copy()
        ctx.update({'get_gallery': self.get_gallery})

        return super(View, self).render(cr, uid, id_or_xml_id, values, engine,
                                        context=ctx)

    def get_gallery(self, obj):
        """
        Devuelve las images de un producto.
            - Si es un product.product devuelve la galeria para esta variante
              concreta
            - Si es un product.template devuelve la galeria de todas las
              imagenes sin atributos.
        """
        if obj._name == 'product.template':
            return [l for l in obj.gallery_ids
                    if len(l.attribute_value_ids) == 0]
        elif obj._name == 'product.product':
            attr = [a.id for a in obj.attribute_value_ids
                    if a.attribute_id.affects_image]
            lines = []
            for l in obj.product_tmpl_id.gallery_ids:
                if [a for a in l.attribute_value_ids if a.id in attr]:
                    lines.append(l)
                    break
            if not lines or len(lines) == 0:
                return [l for l in obj.gallery_ids
                        if len(l.attribute_value_ids) == 0]
            else:
                return list(set(lines))
        else:
            return []
