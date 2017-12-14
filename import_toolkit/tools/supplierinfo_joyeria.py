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


class ProductSupplierInfo(struct.Csv):
    _from = 'raya_joyeria_supplierinfo.txt'
    _first_row_titles = True
    _initialized = False

    _map = [
        parser.Custom(src='product_id', dst='product_tmpl_id',
                      parser='parser_product_id'),
        parser.Custom(src='partner_id', dst='name',
                      parser='parser_partner_id'),
        parser.Custom(src='product_code', dst='product_code',
                      parser='parser_product_code'),
        parser.Custom(src='product_name', dst='product_name',
                      parser='parser_product_name'),
        parser.Str(src='filename', dst='filename'),
        parser.Str(src='sheetname', dst='sheetname'),
        parser.Str(src='row', dst='row'),
        parser.Str(src='product_id', dst='migration_key'),
    ]

    def parser_product_id(self, value):
        value = value.strip()
        products = self.env['product.template'].search([
            ('default_code', 'like', value)])
        if products:
            self.record.product_tmpl_id = products[0].id
        else:
            self.record.product_tmpl_id = None

    def parser_partner_id(self, value):
        value = value.strip()
        partners = self.env['res.partner'].search([
            ('supplier', '=', True),
            ('ref', 'like', value)])
        if partners:
            self.record.name = partners[0].id
        else:
            self.record.name = None

    def parser_product_code(self, value):
        value = value.strip()
        if value == '':
            self.record.product_code = None
        else:
            self.record.product_code = value

    def parser_product_name(self, value):
        value = value.strip()
        if value == '':
            self.record.product_name = None
        else:
            self.record.product_name = value

    def to(self):
        for supplierinfo in self.read():  # (count=200):

            try:
                if supplierinfo.name and supplierinfo.product_tmpl_id:
                    sp = self.env['product.supplierinfo'].create(
                        supplierinfo.dict())
                    _log.info('Reg.Info "%s" imported with id %s' % (
                        supplierinfo.name, sp.id))
                else:
                    _log.info('Reg.Info "%s" NOT IMPORTED with row %s' % (
                        supplierinfo.name, supplierinfo.row))
            except Exception as e:
                _log.error('Reg.Info %s' % supplierinfo.dict())
                _log.error('With errors: %s' % e)
                raise


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

    _log = logging.getLogger('MIGRATE::SupplierInfo')
    _log.info('=' * 100)
    _log.info('ProductCategory')
    ProductSupplierInfo(csv).to(odoo)
    odoo.commit()

    # *************************************************************
    #                           GENERAL
    # *************************************************************

    _log = logging.getLogger('MIGRATE')
    _log.info('=' * 100)
    _log.info('Commiting data')
    odoo.commit()
    odoo.close()
