# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    migration_id = fields.Integer(
        string='MigrationId',
        help='Old system identificator',
        default=0)
    migration_key = fields.Char(
        string='MigrationKey',
        help='Old system identificator Key',
        default='@@@')
    filename = fields.Char(
        string='File Name',
        help='Import File Name',
        required=False)
    sheetname = fields.Char(
        string='Sheet Name',
        help='Import Sheet Name',
        required=False)
    row = fields.Char(
        string='Row',
        help='Import Row Number',
        required=False)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    migration_id = fields.Integer(
        string='MigrationId',
        help='Old system identificator',
        default=0)
    migration_key = fields.Char(
        string='MigrationKey',
        help='Old system identificator Key',
        default='@@@')
    filename = fields.Char(
        string='File Name',
        help='Import File Name',
        required=False)
    sheetname = fields.Char(
        string='Sheet Name',
        help='Import Sheet Name',
        required=False)
    row = fields.Char(
        string='Row',
        help='Import Row Number',
        required=False)


class ProductCategory(models.Model):
    _inherit = 'product.category'

    migration_id = fields.Integer(
        string='MigrationId',
        help='Old system identificator',
        default=0)
    migration_key = fields.Char(
        string='MigrationKey',
        help='Old system identificator Key',
        default='@@@')
    filename = fields.Char(
        string='File Name',
        help='Import File Name',
        required=False)
    sheetname = fields.Char(
        string='Sheet Name',
        help='Import Sheet Name',
        required=False)
    row = fields.Char(
        string='Row',
        help='Import Row Number',
        required=False)


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    migration_id = fields.Integer(
        string='MigrationId',
        help='Old system identificator',
        default=0)
    migration_key = fields.Char(
        string='MigrationKey',
        help='Old system identificator Key',
        default='@@@')
    filename = fields.Char(
        string='File Name',
        help='Import File Name',
        required=False)
    sheetname = fields.Char(
        string='Sheet Name',
        help='Import Sheet Name',
        required=False)
    row = fields.Char(
        string='Row',
        help='Import Row Number',
        required=False)


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    migration_id = fields.Integer(
        string='MigrationId',
        help='Old system identificator',
        default=0)
    migration_key = fields.Char(
        string='MigrationKey',
        help='Old system identificator Key',
        default='@@@')
    filename = fields.Char(
        string='File Name',
        help='Import File Name',
        required=False)
    sheetname = fields.Char(
        string='Sheet Name',
        help='Import Sheet Name',
        required=False)
    row = fields.Char(
        string='Row',
        help='Import Row Number',
        required=False)


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    migration_id = fields.Integer(
        string='MigrationId',
        help='Old system identificator',
        default=0)
    migration_key = fields.Char(
        string='MigrationKey',
        help='Old system identificator Key',
        default='@@@')
    filename = fields.Char(
        string='File Name',
        help='Import File Name',
        required=False)
    sheetname = fields.Char(
        string='Sheet Name',
        help='Import Sheet Name',
        required=False)
    row = fields.Char(
        string='Row',
        help='Import Row Number',
        required=False)
