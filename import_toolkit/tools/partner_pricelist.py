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


class Partner(struct.Csv):
    _from = 'raya_dental_partner.txt'
    _first_row_titles = True
    _default_record = {
    }
    _initialized = False

    _map = [
        parser.Str(src='ref', dst='ref'),
        parser.Custom(src='property_product_pricelist',
                      dst='property_product_pricelist',
                      parser='parser_pricelist_sale'),
        parser.Custom(src='property_product_pricelist_purchase',
                      dst='property_product_pricelist_purchase',
                      parser='parser_pricelist_purchase'),
    ]

    def parser_pricelist_sale(self, value):
        value = value.strip()
        if value == '':
            self.record.property_product_pricelist = \
                self.env.ref('product.list0').id
        else:
            pricelist = self.env['product.pricelist'].search([
                ('migration_key', '=', value)])
            self.record.property_product_pricelist = \
                pricelist and pricelist[0].id

    def parser_pricelist_purchase(self, value):
        value = value.strip()
        if value == "":
            self.record.property_product_pricelist_purchase = \
                self.env.ref('purchase.list0').id
        else:
            pricelist = self.env['product.pricelist'].search([
                ('migration_key', '=', value)])
            self.record.property_product_pricelist_purchase = \
                pricelist and pricelist[0].id

    def to(self):
        for values in self.read():  # (count=200):

            partner = self.env['res.partner'].search([
                ('ref', '=', values.ref)])
            if partner:
                try:
                    partner.write({
                        'property_product_pricelist':
                            values.property_product_pricelist})
                except Exception as e:
                    _log.error('PriceList data %s' % partner.dict())
                    _log.error('With errors: %s' % e)
                    raise
            _log.info('Partner Pricelist update "%s" ' % (values))


# *****************************************************************************
#                                   MAIN
# *****************************************************************************
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
    #       ACTUALIZACION DE TARIFAS DE CLIENTE Y PROVEEDOR
    # *************************************************************

    _log = logging.getLogger('MIGRATE::PartnerPricelist')
    _log.info('=' * 100)
    _log.info('PartnerPricelist')
    Partner(csv).to(odoo)
    odoo.commit()

    # *************************************************************
    #                           GENERAL
    # *************************************************************

    _log = logging.getLogger('MIGRATE')
    _log.info('=' * 100)
    _log.info('Commiting data')
    odoo.commit()
    odoo.close()
