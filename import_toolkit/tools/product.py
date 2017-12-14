# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from odoocli import client, struct, parser, origin
import sys
import os
import logging
_log = logging.getLogger('MIGRATE')

struct.Csv._float_decimal_separator = ','
struct.Csv._float_thousand_separator = '.'
struct.Csv._date_format = '%d-%m-%y'


class ProductCategory(struct.Csv):
    _from = 'raya_dental_product_category.txt'
    _first_row_titles = True
    _initialized = False

    _map = [
        parser.Custom(src='name', dst='name', parser='parser_name'),
        parser.Custom(src='parent_id', dst='parent_id',
                      parser='parser_parent'),
        parser.Str(src='type', dst='type'),
        parser.Str(src='filename', dst='filename'),
        parser.Str(src='sheetname', dst='sheetname'),
        parser.Str(src='row', dst='row'),
        parser.Str(src='odoo_ext_id', dst='migration_key'),
    ]

    def parser_name(self, value):
        value = value.strip()
        value = value.capitalize()
        self.record.name = value

    def parser_parent(self, value):
        value = value.strip()
        categorys = self.env['product.category'].search([
            ('migration_key', 'ilike', value)])
        if categorys:
            self.record.parent_id = categorys[0].id
        else:
            self.record.parent_id = None

    def to(self):
        for category in self.read():  # (count=200):
            try:
                c = self.env['product.category'].create(category.dict())
            except Exception as e:
                _log.error('User data %s' % category.dict())
                _log.error('With errors: %s' % e)
                raise
            _log.info('User "%s" imported with id %s' % (
                category.name, c.id))


class ProductBrand(struct.Csv):
    _from = 'raya_dental_product_brand.txt'
    _first_row_titles = True
    _initialized = False

    _map = [
        parser.Custom(src='name', dst='name', parser='parser_name'),
        parser.Str(src='description', dst='description'),
        parser.Str(src='filename', dst='filename'),
        parser.Str(src='sheetname', dst='sheetname'),
        parser.Str(src='row', dst='row'),
        parser.Str(src='odoo_ext_id', dst='migration_key'),
    ]

    def parser_name(self, value):
        value = value.strip()
        value = value.capitalize()
        self.record.name = value

    def parser_parent(self, value):
        value = value.strip()
        categorys = self.env['product.category'].search([
            ('migration_key', 'ilike', value)])
        if categorys:
            self.record.parent_id[0].id = None
        else:
            self.record.parent_id = None

    def to(self):
        for brand in self.read():  # (count=200):
            try:
                b = self.env['product.brand'].create(brand.dict())
            except Exception as e:
                _log.error('User data %s' % brand.dict())
                _log.error('With errors: %s' % e)
                raise
            _log.info('User "%s" imported with id %s' % (
                brand.name, b.id))


class ProductTemplate(struct.Csv):
    _from = 'raya_dental_product.txt'
    _first_row_titles = True
    _initialized = False

    _map = [
        parser.Custom(src='purchase_ok', dst='purchase_ok',
                      parser='parser_boolean'),
        parser.Custom(src='sale_ok', dst='sale_ok',
                      parser='parser_boolean'),
        parser.Str(src='default_code', dst='default_code'),
        parser.Custom(src='name', dst='name', parser='parser_capitalize'),
        parser.Str(src='type', dst='type'),
        parser.Custom(src='categ_id', dst='categ_id', parser='parser_categ'),
        parser.Str(src='cost_method', dst='cost_method'),
        parser.Custom(src='uom_id', dst='uom_id', parser='parser_uom_id'),
        parser.Custom(src='uom_po_id', dst='uom_po_id',
                      parser='parser_uom_po_id'),
        parser.Float(src='list_price', dst='list_price'),
        parser.Float(src='standard_price', dst='standard_price'),
        parser.Custom(src='route_purchase', dst='route_ids',
                      parser='parser_route_ids'),
        parser.Int(src='sale_delay', dst='sale_delay'),
        parser.Float(src='weight', dst='weight'),
        parser.Float(src='weight_net', dst='weight_net'),
        parser.Float(src='volume', dst='volume'),
        parser.Custom(src='property_account_income',
                      dst='property_account_income',
                      parser='parser_property_account_income'),
        parser.Custom(src='property_account_expense',
                      dst='property_account_expense',
                      parser='parser_property_account_expense'),
        parser.Custom(src='taxes_id', dst='taxes_id',
                      parser='parser_taxes_id'),
        parser.Custom(src='supplier_taxes_id', dst='supplier_taxes_id',
                      parser='parser_supplier_taxes_id'),
        parser.Custom(src='track_incoming', dst='track_incoming',
                      parser='parser_track_incoming'),
        parser.Custom(src='track_outgoing', dst='track_outgoing',
                      parser='parser_track_outgoing'),
        parser.Custom(src='track_production', dst='track_production',
                      parser='parser_track_production'),

        parser.Str(src='loc_rack', dst='loc_rack'),
        parser.Str(src='loc_row', dst='loc_row'),
        parser.Str(src='loc_row', dst='loc_row'),

        parser.Str(src='loc_case', dst='loc_case'),
        parser.Custom(src='avilable_in_pos', dst='avilable_in_pos',
                      parser='parser_boolean'),
        parser.Str(src='description', dst='description'),
        parser.Str(src='description_sale', dst='description_sale'),
        parser.Int(src='produce_delay', dst='produce_delay'),
        parser.Str(src='filename', dst='filename'),
        parser.Str(src='sheetname', dst='sheetname'),
        parser.Custom(src='product_brand_id', dst='product_brand_id',
                      parser='parser_product_brand'),
        parser.Custom(src='default_code', dst='migration_key',
                      parser='parser_migration_key'),
        parser.Str(src='row', dst='row'),
    ]

    def parser_boolean(self, value):
        value = value.strip()
        if value == 'S':
            return True
        else:
            return False

    def parser_capitalize(self, value):
        value = value.strip()
        value = value.capitalize()
        self.record.name = value

    def parser_categ(self, value):
        value = value.strip()
        categorys = self.env['product.category'].search([
            ('migration_key', 'ilike', value)])
        if categorys:
            self.record.categ_id = categorys[0].id
        else:
            self.record.categ_id = 1

    def parser_uom_id(self, value):
        value = value.strip()
        uoms = self.env['product.uom'].search([
            ('name', '=', value)])
        if uoms:
            self.record.uom_id = uoms[0].id
        else:
            self.record.uom_id = 1

    def parser_uom_po_id(self, value):
        value = value.strip()
        uoms = self.env['product.uom'].search([
            ('name', '=', value)])
        if uoms:
            self.record.uom_po_id = uoms[0].id
        else:
            self.record.uom_po_id = 1

    def parser_route_ids(self, value):
        value = value.strip()
        route_ids = []
        if value == 'S':
            buy_id = self.env['stock.location.route'].search([
                ('name', 'ilike', 'buy')])
            route_ids.append(buy_id[0].id or None)
        elif self.record.route_manufacture == 'S':
            manufactures = self.env['stock.location.route'].search([
                ('name', 'ilike', 'manufacture')])
            route_ids.append(manufactures[0].id or None)
        elif self.record.route_order == 'S':
            orders = self.env['stock.location.route'].search([
                ('name', 'ilike', 'pedido')])
            route_ids.append(orders[0].id or None)
        self.record.route_ids = [(6, 0, route_ids)] or None

    def parser_taxes_id(self, value):
        value = value.strip()
        taxes = self.env['account.tax'].search([
            ('description', '=', value)])
        if taxes:
            self.record.taxes_id = taxes[0].id
        else:
            self.record.taxes_id = None

    def parser_supplier_taxes_id(self, value):
        value = value.strip()
        taxes = self.env['account.tax'].search([
            ('description', '=', value)])
        if taxes:
            self.record.taxes_id = taxes[0].id
        else:
            self.record.taxes_id = None

    def parser_property_account_income(self, value):
        value = value.strip()
        accounts = self.env['account.account'].search([
            ('code', '=', value)])
        if accounts:
            self.record.taxes_id = accounts[0].id
        else:
            self.record.taxes_id = None

    def parser_property_account_expense(self, value):
        value = value.strip()
        accounts = self.env['account.account'].search([
            ('code', '=', value)])
        if accounts:
            self.record.taxes_id = accounts[0].id
        else:
            self.record.taxes_id = None

    def parser_track_incoming(self, value):
        value = value.strip()
        if value == 'S':
            self.record.track_incoming = True
        else:
            self.record.track_incoming = False

    def parser_track_outgoing(self, value):
        value = value.strip()
        if value == 'S':
            self.record.track_outgoing = True
        else:
            self.record.track_outgoing = False

    def parser_track_production(self, value):
        value = value.strip()
        if value == 'S':
            self.record.track_production = True
        else:
            self.record.track_production = False

    def parser_migration_key(self, value):
        self.record.migration_key = self.record.default_code.strip() or None

    def parser_product_brand(self, value):
        value = value.strip()
        brands = self.env['product.brand'].search([
            ('migration_id', 'ilike', value)])
        if brands:
            self.record.product_brand_id = brands[0].id
        else:
            self.record.product_brand_id = None

    def to(self):
        for product in self.read():  # (count=200):
            try:
                p = self.env['product.template'].create(product.dict())
            except Exception as e:
                _log.error('User data %s' % product.dict())
                _log.error('With errors: %s' % e)
                raise
            _log.info('Partner "%s" imported with id %s' % (
                product.name, p.id))


# -----------------------------------------------------------------------------
#                                   MAIN
# -----------------------------------------------------------------------------
def get_path(*relative_path):
    fname = os.path.join(__file__, '../../../../..', *relative_path)
    return os.path.abspath(fname)


def test_before_init(env, company_ref):
    return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Añada el nombre de la base de datos por ejemplo:'
        print '   python %s BASE_DE_DATOS' % sys.argv[0]
        print ''
        sys.exit()
    dbname = sys.argv[1:][:1][0]

    odoo = client(
        path=get_path('server'),
        args='-c %s -d %s' % (
            get_path('instances', 'trey', 'openerp-server.conf'),
            dbname))
    csv = origin.Csv(
        path=get_path(
            'addons',
            'custom',
            'raya_customize',
            'migrate',
            'data'),
        delimiter=';',
        charset='utf-8')

    # *************************************************************
    #                      CARGA DE CATEGORIAS DE PRODUCTO
    # *************************************************************
    # _log = logging.getLogger('MIGRATE::ProductCategory')
    # _log.info('=' * 100)
    # _log.info('ProductCategory')
    # ProductCategory(csv).to(odoo)
    # odoo.commit()
    # *************************************************************
    #                      CARGA DE MARCAS DE PRODUCTO
    # *************************************************************
    # _log = logging.getLogger('MIGRATE::ProductBrand')
    # _log.info('=' * 100)
    # _log.info('ProductBrand')
    # ProductBrand(csv).to(odoo)
    # odoo.commit()
    # *************************************************************
    #                      CARGA DE CONTACTOS
    # *************************************************************

    _log = logging.getLogger('MIGRATE::ProductTemplate')
    _log.info('=' * 100)
    _log.info('ProductTemplate')
    ProductTemplate(csv).to(odoo)
    odoo.commit()

    # *************************************************************
    #                           GENERAL
    # *************************************************************

    _log = logging.getLogger('MIGRATE')
    _log.info('=' * 100)
    _log.info('Commiting data')
    odoo.commit()
    odoo.close()
