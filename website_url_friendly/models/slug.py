# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class Slug(models.Model):
    _name = 'website_url_friendly.slug'

    name = fields.Char(
        string=u'Slug',
        required=True,
        translate=True)
    path = fields.Char(
        string=u'Path',
        required=True,
        translate=False)
    model = fields.Char(
        string=u'Model',
        required=True,
        translate=False)
    model_id = fields.Integer(
        string=u'Model Id',
        required=True)

    _sql_constraints = [
        ('name_unique', 'unique (name)', u'The slug must be unique !'),
        ('path_unique', 'unique (path)', u'The path must be unique !'),
    ]
