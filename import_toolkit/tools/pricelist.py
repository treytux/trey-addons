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


class ProductPricelist(struct.Csv):
    _from = 'raya_dental_product_pricelist.txt'
    _first_row_titles = True
    _initialized = False

    _map = [
        parser.Custom(src='name', dst='name', parser='parser_name'),
        parser.Custom(src='type', dst='type', parser='parser_type'),
        parser.Str(src='filename', dst='filename'),
        parser.Str(src='sheetname', dst='sheetname'),
        parser.Str(src='row', dst='row'),
        parser.Str(src='migration_key', dst='migration_key'),
    ]

    def parser_name(self, value):
        value = value.strip()
        value = value.capitalize()
        self.record.name = value

    def parser_type(self, value):
        value = value.strip()
        self.record.type = value

    def to(self):
        for pricelist in self.read():  # (count=200):
            try:
                pl = self.env['product.pricelist'].create(pricelist.dict())
                data = {
                    'name': pricelist.name,
                    'pricelist_id': pl.id}
                version = self.env['product.pricelist.version'].create(data)
                _log.info(
                    'Pricelist "%s" imported with id %s version id %s' % (
                        pricelist.name, pl.id, version.id))
            except Exception as e:
                _log.error('Pricelist %s' % pricelist.dict())
                _log.error('With errors: %s' % e)
                raise


class ProductPricelistItem(struct.Csv):
    _from = 'raya_dental_product_pricelist_item.txt'
    _first_row_titles = True
    _initialized = False

    _map = [
        parser.Int(src='price_version_id', dst='price_version_id'),
        parser.Custom(src='product_tmpl_id', dst='product_tmpl_id',
                      parser='parser_product_tmpl_id'),
        parser.Int(src='min_quantity', dst='min_quantity'),
        parser.Int(src='sequence', dst='sequence'),
        parser.Custom(src='base', dst='base', parser='parser_base'),
        parser.Float(src='price_discount', dst='price_discount'),
        parser.Float(src='price_surcharge', dst='price_surcharge'),
        parser.Float(src='price_round', dst='price_round'),
        parser.Float(src='price_min_margin', dst='price_min_margin'),
        parser.Float(src='price_max_margin', dst='price_max_margin'),
        parser.Str(src='filename', dst='filename'),
        parser.Str(src='sheetname', dst='sheetname'),
        parser.Str(src='row', dst='row'),
        parser.Custom(src='migration_key', dst='migration_key',
                      parser='parser_migration_key'),

    ]

    def parser_migration_key(self, value):
        value = value.strip()
        versions = self.env['product.pricelist'].search([
            ('migration_key', '=', value)])
        if versions:
            self.record.price_version_id = versions[0].id
            self.record.migration_key = value
        else:
            self.record.price_version_id = None
            self.record.migration_key = value

    def parser_product_tmpl_id(self, value):
        value = value.strip()
        templates = self.env['product.template'].search([
            ('default_code', 'like', value)])
        if templates:
            self.record.product_tmpl_id = templates[0].id
            self.record.name = templates[0].name
        else:
            self.record.product_tmpl_id = None

    def parser_base(self, value):
        value = value.strip()
        self.record.base = 1

    def to(self):
        for item in self.read():  # (count=200):
            try:
                i = self.env['product.pricelist.item'].create(item.dict())
            except Exception as e:
                _log.error('User data %s' % item.dict())
                _log.error('With errors: %s' % e)
                raise
            _log.info('PriceItem row=%s imported with id=%s' % (
                item.row, i.id))


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
    #                      CARGA DE TARIFAS
    # *************************************************************

    _log = logging.getLogger('MIGRATE::PriceList')
    _log.info('=' * 100)
    _log.info('ProductPricelist')
    ProductPricelist(csv).to(odoo)
    odoo.commit()

    # *************************************************************
    #                      CARGA DE ITEMS DE TARIFAS
    # *************************************************************

    _log = logging.getLogger('MIGRATE::PriceListItems')
    _log.info('=' * 100)
    _log.info('ProductPricelistItems')
    ProductPricelistItem(csv).to(odoo)
    odoo.commit()

    # *************************************************************
    #                           GENERAL
    # *************************************************************

    _log = logging.getLogger('MIGRATE')
    _log.info('=' * 100)
    _log.info('Commiting data')
    odoo.commit()
    odoo.close()
