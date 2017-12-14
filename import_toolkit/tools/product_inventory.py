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


class StockInventoryLne(struct.Csv):
    _from = 'raya_dental_product_inventory.txt'
    _first_row_titles = True
    _default_record = {
    }
    _initialized = False

    _map = [

        parser.Custom(src='ref', dst='product_id', parser='parser_product'),
        parser.Float(src='quantity', dst='product_qty'),
    ]

    def parser_product(self, value):
        value = value.strip()
        products = self.env['product.template'].search([
            ('default_code', '=', value)])
        if products:
            self.record.product_id = products[0].id or None

    def to(self):

        inventory_data = {
            'name': 'Carga Inventario inicial',
            'date': '2016-01-31',
        }
        inventory = self.env['stock.inventory'].create(inventory_data)
        for values in self.read():  # (count=200):
            if not values.product_id:
                continue
            if values.product_qty < 0:
                continue
            values.inventory_id = inventory.id
            values.location_id = inventory.location_id.id
            try:
                i = self.env['stock.inventory.line'].create(values.dict())
            except Exception as e:
                _log.error('Inventory data %s' % values.dict())
                _log.error('With errors: %s' % e)
                raise
            _log.info('InventoryLine "%s" imported with id %s' % (
                values.product_id, i.id))


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
    #       CREACION DE INVENTARIO INICIAL PARA EL ARRANQUE
    # *************************************************************

    _log = logging.getLogger('MIGRATE::InventoryLines')
    _log.info('=' * 100)
    _log.info('InventoryLines')
    StockInventoryLne(csv).to(odoo)
    odoo.commit()

    # *************************************************************
    #                           GENERAL
    # *************************************************************

    _log = logging.getLogger('MIGRATE')
    _log.info('=' * 100)
    _log.info('Commiting data')
    odoo.commit()
    odoo.close()
