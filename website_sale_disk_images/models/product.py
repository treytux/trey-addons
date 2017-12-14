# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

import os
import logging
import glob

from openerp.addons.website.models.website import slugify
from openerp import fields
from openerp.osv import osv
from PIL import Image

logger = logging.getLogger(__name__)

STATIC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(STATIC_DIR, 'static', 'src', 'products')

STATIC_URL = '/website_sale_disk_images/static/src/products'


class ImageGallery(object):
    def __init__(self, path):
        self.path = path
        self.filename = os.path.basename(path)
        self.src = os.path.join(STATIC_URL, self.filename)

    def get(self, width=None, height=None):
        if width is not None:
            assert height is not None, u'Parametro height no definido'

            # comprobamos si existe el directorio de thumbs
            static_dir_thumb = os.path.join(STATIC_DIR,
                                            '{}x{}'.format(width, height))
            if not os.path.exists(static_dir_thumb):
                os.makedirs(static_dir_thumb)

            # comprobamos si existe la imagen
            static_thumb = os.path.join(static_dir_thumb, self.filename)
            if not os.path.exists(static_thumb):
                create_thumbnails(self.path, static_thumb, width, height)

            # creamos url thumb
            return os.path.join(STATIC_URL, '{}x{}'.format(width, height),
                                self.filename)

        # imagen original
        return self.src


class Gallery(list):
    def __init__(self, *args, **kwargs):
        super(Gallery, self).__init__(*args, **kwargs)
        self._product = None
        self._name_product = None

        self._template = None
        self._name_template = None

    @property
    def product(self):
        return self._product

    @product.setter
    def product(self, value):
        self._product = value

    @property
    def name_product(self):
        return self._name_product + '.jpg'

    @name_product.setter
    def name_product(self, value):
        self._name_product = value

    @property
    def path_product(self):
        return STATIC_DIR

    @property
    def template(self):
        return self._template

    @template.setter
    def template(self, value):
        self._template = value

    @property
    def name_template(self):
        return self._name_template + '.jpg'

    @name_template.setter
    def name_template(self, value):
        self._name_template = value

    @property
    def products(self):
        """ Devuelve las variantes """
        return self


def create_thumbnails(path_image_origin, path_image_desc, width, height,
                      quality=100):
    method_resize = getattr(Image, 'ANTIALIAS')
    infile = Image.open(path_image_origin)
    im = infile.copy()

    if im.size[0] <= im.size[1]:
        im.convert('RGB')
        im.thumbnail((height * im.size[0] / im.size[1], height), method_resize)
    else:
        im.convert('RGB')
        im.thumbnail((width, width * im.size[1] / im.size[0]), method_resize)

    im.save(path_image_desc, quality=quality)


def get_name_product(product):
    logger.debug("Get name product {}".format(product._name))
    name = None

    if product._name == 'product.template':
        # producto por defecto y primera valor de cada variante que afecte
        # a la imagen
        # ====================================================================
        assert len(product.product_variant_ids) > 0, \
            u"El producto {} no tiene variantes".format(product)

        template = product
        product = product.product_variant_ids[0]  # producto por defecto
        name = slugify(template.name)

        # product.template
        #   - attribute_line_ids => product.attribute.line
        # product.attribute.line
        #   - attribute_id product.attribute
        #   - value_ids => product.attribute.value

        attributes_lines = [l for l in template.attribute_line_ids
                            if l.attribute_id.affects_image]

        for al in attributes_lines:
            av = al.value_ids[0]
            name += u'-{}-{}'.format(
                slugify(av.attribute_id.name), slugify(av.name))
    else:
        # valor de cada variante que afecta a la imagen
        # =============================================
        template = product.product_tmpl_id
        name = slugify(template.name)

        # product.product
        #   - attribute_value_ids => product.attribute.value
        # product.attribute.value
        #   - attribute_id => product.attribute

        attributes_values = [l for l in product.attribute_value_ids
                             if l.attribute_id.affects_image]

        for av in attributes_values:
            name += u'-{}-{}'.format(
                slugify(av.attribute_id.name), slugify(av.name))

    assert name is not None, \
        u"No se ha podido calcular el nombre de la imagen para {}" \
        .format(product)

    return name, slugify(template.name)


def get_images_disk(name_template):
    images = []

    path_template_image = os.path.join(STATIC_DIR, name_template)
    path_template_image += '*.jpg'

    for image_disk in glob.glob(path_template_image):
        images.append(image_disk)

    images.sort()
    return images


def get_gallery(obj):
    assert obj._name in ('product.template', 'product.product'), \
        u"Tipo de objeto no permitido"

    # nombres de variantes y plantilla
    name_image, name_template = get_name_product(obj)
    logger.info("GALLERY ({}) {}, {}".format(obj._name, name_image,
                                             name_template))

    # variantes
    image_gallery = [ImageGallery(path=image_path) for image_path
                     in get_images_disk(name_image)]

    # plantilla
    image_gallery_template = [ImageGallery(path=image_path) for image_path
                              in get_images_disk(name_template)]

    g = Gallery(image_gallery)
    g.product = obj
    g.name_product = name_image
    g.template = image_gallery_template
    g.name_template = name_template

    return g


class View(osv.osv):
    _inherit = "ir.ui.view"

    def render(self, cr, uid, id_or_xml_id, values=None, engine='ir.qweb',
               context=None):
        cxn = context.copy()
        cxn.update({'gallery': self.gallery})

        return super(View, self).render(cr, uid, id_or_xml_id, values, engine,
                                        context=cxn)

    def gallery(self, obj):
        return get_gallery(obj)


class ProductAttribute(osv.osv):
    _inherit = "product.attribute"

    affects_image = fields.Boolean(string=u"Afecta a la imagen del producto")
