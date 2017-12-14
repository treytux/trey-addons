# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

import os
import base64
import fnmatch
import cStringIO
from openerp import fields, api, tools, _
from openerp.osv import osv
from openerp.addons.website.models.website import slugify
from PIL import Image

import logging

_log = logging.getLogger(__name__)


def _filestorage(cr):
    path = os.path.join(tools.config.filestore(cr.dbname), 'product_gallery')
    if not os.path.exists(path):
        os.makedirs(path)
    return path


class GalleryImage(osv.AbstractModel):
    """
    Modelo base para guardar imágenes que se asocian a los modelos
    """
    _name = "gallery_image"
    _description = "Gallery Image"
    _order = 'sequence'
    _sql_constraints = [('name_uniq', 'unique(name)',
                        _(u"El nombre debe ser único!"))]

    def _last_update_default(self):
        """ Devuelve la fecha actual """
        return fields.Datetime.now()

    name = fields.Char(u'Image', required=False)
    sequence = fields.Integer(u'Sequence', required=True, store=True)
    image = fields.Binary(u'Image File', required=True, store=False,
                          compute='_comput_image', inverse='_inverse_image')
    src = fields.Char(u'URL imagen', store=True, compute='_compute_src')
    last_update_img = fields.Datetime(u'Fecha modificacion',
                                      default=_last_update_default)

    def _get_next_sequence(self, cr, uid, object_relation_id=None):
        """ Devuelve el siguiente valor para la sequence """
        object_relation_id = self.object_relation.id \
            if not object_relation_id else object_relation_id

        return self.search(
            cr, uid, [(self.object_relation_name, '=', object_relation_id)],
            count=True) + 1

    def _delete_thumbails(self, image_path):
        """ Borra del disco las imagenes asociadas a este fichero con sus
        diferentes tamaños """
        if not image_path:
            return

        path, file_name = os.path.split(image_path)
        matches = []
        for root, dirnames, filenames in os.walk(path):
            for filename in fnmatch.filter(filenames, file_name):
                matches.append(os.path.join(root, filename))

        # no borramos el original
        if image_path in matches:
            matches.remove(image_path)

        for f in matches:
            os.remove(f)

    def _compute_name_image(self, name=None, sequence=None):
        """
        Devuelve el nombre de la imagen en función del nombre del objecto
        y su sequencia
        """
        name = name or self.object_relation.name
        sequence = sequence or self.sequence
        if sequence > 1:
            name_file = u"{}-{}.jpg".format(slugify(name), sequence)
        else:
            name_file = u"{}.jpg".format(slugify(name))
        # comprobamos si existe ya una imagen con este nombre
        count = self.search_count(
            [(self.object_relation_name, '!=', self.object_relation.id),
             ('name', '=', name_file)])
        if count > 0:
            if sequence > 1:
                name_file = u"{}_{}-{}.jpg".format(slugify(name), count,
                                                   sequence)
            else:
                name_file = u"{}_{}.jpg".format(slugify(name), count)
        return name_file

    @api.one
    @api.depends('name')
    def _compute_src(self):
        self.src = False
        if self.name:
            self.src = u'/images/{}'.format(self.name)

    @api.one
    @api.depends('name')
    def _comput_image(self):
        self.image = False
        if self.name:
            fs = _filestorage(self.env.cr)
            image_path = os.path.join(fs, self._compute_name_image())
            if not os.path.exists(image_path):
                return
            with open(image_path, 'rb') as f:
                self.image = base64.b64encode(f.read())

    @api.one
    @api.depends('name', 'sequence')
    def _inverse_image(self):
        fs = _filestorage(self.env.cr)
        name_file = self._compute_name_image()
        image_path = os.path.join(fs, name_file)
        if os.path.isfile(image_path):
            count = 1
            while not os.path.isfile(image_path):
                name = u"{}_{}".format(slugify(self.name), count)
                image_path = os.path.join(fs, name)
                count += 1
                name_file = name
            image_path = os.path.join(fs, name_file)
        # salvamos imagen
        img = Image.open(cStringIO.StringIO(base64.b64decode(self.image)))
        img.save(image_path)
        self.write({'name': name_file})

    @property
    def object_relation_name(self):
        raise NotImplementedError()

    @property
    def object_relation(self):
        if not hasattr(self, self.object_relation_name):
            raise NotImplementedError(
                u"No existe el campo '{}' en la clase '{}'".format(
                    self.object_relation_name, self._name))

        return getattr(self, self.object_relation_name)

    def unlink(self, cr, uid, ids, context=None):
        fs = _filestorage(cr)
        for img in self.browse(cr, uid, ids, context=context):
            image_path = os.path.join(fs, img.name)
            # borramos thumbnails y original
            self._delete_thumbails(image_path)
            try:
                os.remove(image_path)
            except:
                _log.exception(u"Error al borrar el original {}"
                               .format(image_path))

        return super(GalleryImage, self).unlink(cr, uid, ids, context)

    def write(self, cr, uid, ids, vals, context=None):
        if 'name' in vals:
            fs = _filestorage(cr)
            for gallery in self.browse(cr, uid, ids, context=context):
                if gallery.name:
                    image_path = os.path.join(fs, gallery.name)
                    self._delete_thumbails(image_path)
                vals.update({'last_update_img': fields.Datetime.now()})
        return super(GalleryImage, self).write(cr, uid, ids, vals, context)

    def create(self, cr, uid, vals, context=None):
        vals['sequence'] = self._get_next_sequence(
            cr, uid, vals[self.object_relation_name])
        return super(GalleryImage, self).create(cr, uid, vals, context)


def update_sequences_gallery(self, cr, uid, ids, field_gallery,
                             model_gallery_name):
    """ Actualiza los nombres de una galleria asociada a un object self
    en función de su sequencia """
    fs = _filestorage(cr)
    for obj in self.browse(cr, uid, ids):
        fix_images = []
        for image in getattr(obj, field_gallery):
            name_compute = image._compute_name_image(
                image.object_relation.name, image.sequence)
            if name_compute != image.name:
                image_path = os.path.join(fs, image.name)
                image._delete_thumbails(image_path)
                fix_images.append((image, name_compute))
                image.name = 'fix_{}_{}'.format(
                    slugify(model_gallery_name), image.id)
                # rename
                path, file_name = os.path.split(image_path)
                new_image_path = os.path.join(path, image.name)
                try:
                    os.rename(image_path, new_image_path)
                except:
                    _log.exception(u"Error actualizando nombre gallery")
        if len(fix_images):
            for image, name_compute in fix_images:
                # rename
                new_image_path = os.path.join(fs, name_compute)
                try:
                    os.rename(os.path.join(path, image.name), new_image_path)
                except:
                    _log.exception(u"Error actualizando nombre gallery fixed")
                # write
                image.write({'name': name_compute})
