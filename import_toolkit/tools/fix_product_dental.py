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


class ProductTemplate(struct.Csv):
    _from = 'raya_dental_product.txt'
    _first_row_titles = True
    _initialized = False

    _map = [
        parser.Str(src='default_code', dst='default_code'),
        parser.Str(src='name', dst='name'),
        parser.Str(src='type', dst='type'),
        parser.Custom(src='product_brand_id', dst='product_brand_id',
                      parser='parser_product_brand'),
    ]

    def parser_product_brand(self, value):
        value = value.strip()
        brands = self.env['product.brand'].search([
            ('name', '=', value)])
        if brands:
            self.record.product_brand_id = brands[0].id
        else:
            self.record.product_brand_id = None
            print value

    def to(self):
        for product in self.read():  # (count=200):
            product_id = self.env['product.template'].search([
                ('migration_key', '=', product.default_code)])
            try:
                product_id.write(product.dict())
            except Exception as e:
                _log.error('Product data %s' % product.dict())
                _log.error('With errors: %s' % e)
                raise
            _log.info('Product "%s" updated with id %s' % (
                product_id.name, product.product_brand_id))


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
    #                      CARGA DE TEMPLATES
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
