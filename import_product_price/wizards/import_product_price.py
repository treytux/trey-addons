# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api, _, exceptions
import base64
import csv
import StringIO

import logging
_log = logging.getLogger(__name__)


def get_value(row, colName):
    '''Returns the value of the row to the column 'colName'.'''
    cols = {
        'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9,
        'J': 10, 'K': 11, 'L': 12, 'M': 13, 'N': 14, 'O': 15, 'P': 16, 'Q': 17,
        'R': 18, 'S': 19, 'T': 20, 'U': 21, 'V': 22, 'W': 23, 'X': 24, 'Y': 25,
        'Z': 26, 'AA': 27, 'AB': 28, 'AC': 29, 'AD': 30, 'AE': 31, 'AF': 32,
        'AG': 33, 'AH': 34, 'AI': 35, 'AJ': 36, 'AK': 37, 'AL': 38, 'AM': 39,
        'AN': 40, 'AO': 41, 'AP': 42, 'AQ': 43, 'AR': 44, 'AS': 45, 'AT': 46,
        'AU': 47, 'AV': 48, 'AW': 49, 'AX': 50, 'AY': 51, 'AZ': 52
    }
    colName = str(colName).upper()
    if colName in cols:
        colId = cols[colName] - 1
        if colId < len(row):
            return row[colId]
        else:
            return ''
    else:
        return '*** DESCONOCIDO **** %s' % colName


def to_integer(num):
    try:
        res = int(num)
    except Exception as e:
        _log.warn(_(
            'Error to convert %s to float; error: %s. It is returned 0.' % (
                num, e)))
        res = 0
    return res


def to_float(num):
    try:
        res = float(num)
    except Exception as e:
        _log.warn(_(
            'Error to convert %s to float; error: %s. It is returned 0.' % (
                num, e)))
        res = 0
    return res


class WizImportProductPrice(models.TransientModel):
    _name = 'wiz.import.product.price'
    _description = 'Import product price'

    name = fields.Char(
        string='Empty')
    ffile = fields.Binary(
        string='File csv',
        filters='*.csv',
        required=True)
    to_create = fields.Boolean(
        string='Create',
        help="If you select this option, pressing the 'Accept' button all "
        "products listed in the 'New products' page will be created.")
    to_update = fields.Boolean(
        string='Update',
        help="If you select this option, pressing the 'Accept' button all "
        "products listed in the 'Updated products' page will be created.")
    line_new_ids = fields.Many2many(
        comodel_name='import.product.line.new',
        relation='import_prod_price2import_line_new_rel',
        column1='import_prod_price',
        column2='import_line_new')
    line_update_ids = fields.Many2many(
        comodel_name='import.product.line.update',
        relation='import_prod_price2import_line_update_rel',
        column1='import_prod_price',
        column2='import_line_update')
    line_unknown_ids = fields.Many2many(
        comodel_name='import.product.line.unknown',
        relation='import_prod_price2import_line_unknown_rel',
        column1='import_prod_price',
        column2='import_line_unknown')
    read_lines = fields.Integer(
        string='Read lines',
        readonly=True)

    def get_default_categ_id(self):
        '''Returns the id of the default category.'''
        categs = self.env['product.category'].search(
            ['|', ('name', '=', 'All'), ('name', '=', 'Todos')])
        if not categs:
            raise exceptions.Warning(_(
                'The default category \'All\' or \'Todos\' does not exist in '
                'the system. You should define it.'))
        else:
            categ_id = categs[0].id
        return categ_id

    def get_categ_id(self, name):
        '''Returns the id of the category whose name is passed as a parameter
        or the id of category by default.'''
        categ_obj = self.env['product.category']
        categories = name.split(' / ')
        categories.reverse()
        parent_name = categories[1] if len(categories) > 1 else ''
        category_name = categories[0]
        if parent_name == '':
            categs = categ_obj.with_context(lang='es_ES').search(
                [('name', '=', category_name)])
        else:
            categs = categ_obj.with_context(lang='es_ES').search([
                ('name', '=', category_name),
                ('parent_id.name', '=', parent_name)])
        if not categs.exists():
            categ_id = self.get_default_categ_id()
            _log.warn(_(
                'The category \'%s\' does not exist in the system, it is '
                'assigned default category \'%s\'.' % (name, categ_id)))
            return categ_id
        else:
            categ_id = categs[0].id
        return categ_id

    def get_discount(self, current_price, updated_price):
        '''Calculates the discount between the current price and the price
        updated.'''
        if round(current_price, 2) == round(updated_price, 2):
            return 0
        return current_price / (current_price - updated_price)

    def get_route_ids(self, routes):
        '''Obtains the routes from the string passed as a parameter.'''
        route_obj = self.env['stock.location.route']
        route_ids = []
        for route_name in routes.split(','):
            routes = route_obj.search([('name', '=', route_name)])
            if routes.exists():
                route_ids.append(routes[0].id)
        return route_ids

    def get_uom_id(self, name):
        '''Returns the id of the unit of measure whose name is passed as a
        parameter.'''
        product_uoms = self.env['product.uom'].search([('name', '=', name)])
        if not product_uoms:
            uom_id = None
            _log.warn(_(
                'The unit of mesasure \'%s\' does not exist in the system, it '
                'is not assigned.' % name))
        else:
            uom_id = product_uoms[0].id
        return uom_id

    def get_cost_method(self, name):
        '''Obtains the cost method from the string passed as a parameter.'''
        if name == 'standard':
            return 'standard'
        elif name == 'average':
            return 'average'
        elif name == 'real':
            return 'real'
        else:
            _log.warn(_(
                'The cost method \'%s\' does not exist in the system, it is'
                'assigned default cost method (Real Price).' % name))
            return 'real'

    def get_state(self, name):
        '''Obtains the state from the string passed as a parameter.'''
        if name == 'En desarrollo':
            return 'draft'
        elif name == 'Fin del ciclo de vida':
            return 'end'
        elif name == 'Obsoleto':
            return 'obsolete'
        else:
            return 'sellable'

    def get_partner_id(self, name):
        '''Returns the id of the partner whose name is passed as a parameter.
        '''
        partners = self.env['res.partner'].search([('name', '=', name)])
        if not partners:
            partner_id = None
            _log.warn(_(
                'The partner \'%s\' does not exist in the system, it is not '
                'assigned.' % name))
        else:
            partner_id = partners[0].id
        return partner_id

    @api.multi
    def read_file_lines(self, rows):
        '''Read product lines of the file and create the lines classified by
        types (new, update, unknown).'''
        new_products = {}
        update_products = {}
        unknown_products = {}
        product_obj = self.env['product.product']
        import_line_new_obj = self.env['import.product.line.new']
        import_line_update_obj = self.env['import.product.line.update']
        import_line_unknown_obj = self.env['import.product.line.unknown']
        line = -1
        # Iterate all rows
        for row in rows:
            line += 1
            # Ignore the first row that contains the name of the columns
            if line == 0:
                continue
            if (get_value(row, 'b') == '' or get_value(row, 'b') is None or
               get_value(row, 'b') is False):
                data = {
                    'product_name': get_value(row, 'b'),
                    'categ_name': get_value(row, 'u'),
                    'updated_price': to_float(get_value(row, 'z'))}
                unknown_products[get_value(row, 'b')] = data
                line_unknown = import_line_unknown_obj.create(data)
                self.write({'line_unknown_ids': [(4, line_unknown.id)]})
                continue
            # Search the product by name
            products = product_obj.search([
                ('name_template', '=', get_value(row, 'b'))])
            if not products.exists():
                sale_ok = True if to_integer(
                    get_value(row, 'd')) == 1 else False
                purchase_ok = True if to_integer(
                    get_value(row, 'e')) == 1 else False
                active = True if to_integer(
                    get_value(row, 'g')) == 1 else False
                website_published = True if to_integer(
                    get_value(row, 't')) == 1 else False
                data_object = {
                    'pt_data': {
                        'name': get_value(row, 'b'),
                        'sale_ok': sale_ok,
                        'purchase_ok': purchase_ok,
                        'description': get_value(row, 'j'),
                        'seller_data': {
                            'name': self.get_partner_id(get_value(row, 'k')),
                            'delay': to_integer(get_value(row, 'ag')),
                            'min_qty': to_float(get_value(row, 'ah')),
                            'pricelist_data': {
                                'min_quantity': to_float(get_value(row, 'ai')),
                                'price': to_float(get_value(row, 'aj'))}},
                        'state': self.get_state(get_value(row, 'l')),
                        'volume': to_float(get_value(row, 'm')),
                        'weight': to_float(get_value(row, 'n')),
                        'weight_net': to_float(get_value(row, 'o')),
                        'warranty': to_integer(get_value(row, 'p')),
                        'sale_delay': to_integer(get_value(row, 'q')),
                        'description_sale': get_value(row, 'r'),
                        # @ TODO funcion cuando sepa que va a venir, en los
                        # ejemplos esta en blanco.
                        # La tabla de relacion es
                        # product_public_category_product_template_rel
                        # 'public_categ_ids': [(4, self.get_public_categ_ids(
                        #     get_value(row, 's')))],
                        'website_published': website_published,
                        'categ_id': self.get_categ_id(get_value(row, 'u')),
                        'length': to_float(get_value(row, 'v')),
                        'high': to_float(get_value(row, 'w')),
                        'width': to_float(get_value(row, 'x')),
                        'dimensional_uom': self.get_uom_id(
                            get_value(row, 'y')),
                        'list_price': to_float(get_value(row, 'z')),
                        'cost_method': self.get_cost_method(
                            get_value(row, 'aa')),
                        'standard_price': to_float(get_value(row, 'ab')),
                        'uom_po_id': self.get_uom_id(get_value(row, 'ac')),
                        'uom_id': self.get_uom_id(get_value(row, 'ad')),
                        'uos_id': self.get_uom_id(get_value(row, 'ae')),
                        'uos_coeff': to_float(get_value(row, 'af')),
                        'orderpoint_data': {
                            'product_min_qty': to_float(get_value(row, 'ak')),
                            'product_max_qty': to_float(get_value(row, 'al')),
                            'qty_multiple': to_float(get_value(row, 'am'))},
                        'urlproduct_ecom': get_value(row, 'an'),
                        'urlproduct_support': get_value(row, 'ao')},
                    'pp_data': {
                        'name_template': get_value(row, 'b'),
                        'default_code': get_value(row, 'c'),
                        'type': get_value(row, 'f'),
                        'active': active,
                        'route_ids': [
                            (4, route_id)
                            for route_id in self.get_route_ids(
                                get_value(row, 'h'))],
                        'ean13': get_value(row, 'i')}}
                data = {
                    'product_name': get_value(row, 'b'),
                    'categ_name': get_value(row, 'u'),
                    'updated_price': to_float(get_value(row, 'z')),
                    'data_object': data_object}
                new_products[get_value(row, 'b')] = data
                line_new = import_line_new_obj.create(data)
                self.write({'line_new_ids': [(4, line_new.id)]})
            else:
                data_object = {
                    'pt_data': {
                        'list_price': to_float(get_value(row, 'z')),
                        'product_tmpl_id': products[0].product_tmpl_id.id}}
                data = {
                    'product_name': get_value(row, 'b'),
                    'categ_name': get_value(row, 'u'),
                    'current_price': to_float(products[0].list_price),
                    'updated_price': to_float(get_value(row, 'z')),
                    'discount': self.get_discount(
                        to_float(products[0].list_price),
                        to_float(get_value(row, 'z'))),
                    'data_object': data_object}
                if (round(data['current_price'], 2) !=
                        round(data['updated_price'], 2)):
                    update_products[get_value(row, 'b')] = data
                    line_update = import_line_update_obj.create(data)
                    self.write({'line_update_ids': [(4, line_update.id)]})
        self.read_lines = line
        return True

    @api.multi
    def button_import(self):
        '''Imports the file and creates the lines of the wizard.'''
        if self.ffile:
            try:
                # Open file
                ffile = base64.decodestring(self.ffile)
                ffile = StringIO.StringIO(ffile)
                rows = csv.reader(ffile, delimiter=',', quotechar='"')
                # Reads file lines and creates wizard lines
                self.read_file_lines(rows)
            except Exception as e:
                raise exceptions.Warning(_(
                    'It has occurred following error: %s.' % e))
        # Open the following view
        res = self.env['ir.model.data'].get_object_reference(
            'import_product_price',
            'wizard_import_product_price_update_create')
        res_id = res and res[1] or False
        return {
            'name': _('Import product price'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'wiz.import.product.price',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
        }

    @api.multi
    def button_update_create(self):
        '''Depending on which option is selected: create or update, it will
        create or it will update the following models:
            - Product template
            - Product
            - Supplier information
            - Minimum stock rules'''
        product_tmpl_obj = self.env['product.template']
        product_obj = self.env['product.product']
        supplier_obj = self.env['product.supplierinfo']
        pricelist_info_obj = self.env['pricelist.partnerinfo']
        orderpoint_obj = self.env['stock.warehouse.orderpoint']
        if self.to_create:
            for line in self.line_new_ids:
                # Convert unicode to dictionary
                data_dic = eval(line.data_object)
                # Get data about supplier info and orderpoints
                seller_data = data_dic['pt_data']['seller_data']
                del data_dic['pt_data']['seller_data']
                orderpoint_data = data_dic['pt_data']['orderpoint_data']
                del data_dic['pt_data']['orderpoint_data']
                # Create template
                product_tmpl = product_tmpl_obj.create(data_dic['pt_data'])
                data_dic['pp_data'].update({
                    'product_tmpl_id': product_tmpl.id})
                # Update product (automatically created by product template)
                products = product_obj.search([(
                    'product_tmpl_id', '=', product_tmpl.id)])
                if not products.exists():
                    raise exceptions.Warning(_(
                        'Error: the system has not created any product.'))
                products[0].write(data_dic['pp_data'])
                # Create supplier info
                if seller_data and seller_data['name'] is not None:
                    supplier = supplier_obj.create({
                        'product_tmpl_id': product_tmpl.id,
                        'name': seller_data['name'],
                        'min_qty': seller_data['min_qty'],
                        'delay': seller_data['delay']
                    })
                    if (seller_data['pricelist_data']['min_quantity'] and
                       seller_data['pricelist_data']['price']):
                        pricelist_info_obj.create({
                            'suppinfo_id': supplier.id,
                            'min_quantity': seller_data[
                                'pricelist_data']['min_quantity'],
                            'price': seller_data['pricelist_data']['price'],
                        })
                # Create orderpoint
                if orderpoint_data:
                    orderpoint_obj.create({
                        'product_id': products[0].id,
                        'product_min_qty': orderpoint_data['product_min_qty'],
                        'product_max_qty': orderpoint_data['product_max_qty'],
                        'qty_multiple': orderpoint_data['qty_multiple']
                    })
        if self.to_update:
            for line in self.line_update_ids:
                # Convert unicode to dictionary
                data_dic = eval(line.data_object)
                # Get data about the product to update
                product_tmpl_id = data_dic['pt_data']['product_tmpl_id']
                del data_dic['pt_data']['product_tmpl_id']
                product_tmpl = product_tmpl_obj.browse(product_tmpl_id)
                product_tmpl.write(data_dic['pt_data'])
        return True


class ImportProductLineNew(models.TransientModel):
    _name = 'import.product.line.new'

    name = fields.Char(
        string='Empty')
    product_name = fields.Char(
        string='Product name')
    categ_name = fields.Char(
        string='Category name')
    updated_price = fields.Float(
        string='Updated price')
    data_object = fields.Text(
        string='Data object')


class ImportProductLineUpdate(models.TransientModel):
    _name = 'import.product.line.update'

    name = fields.Char(
        string='Empty')
    product_name = fields.Char(
        string='Product name')
    categ_name = fields.Char(
        string='Category name')
    current_price = fields.Float(
        string='Current price')
    updated_price = fields.Float(
        string='Updated price')
    discount = fields.Float(
        string='Discount (%)')
    data_object = fields.Text(
        string='Data object')


class ImportProductLineUnknown(models.TransientModel):
    _name = 'import.product.line.unknown'

    name = fields.Char(
        string='Empty')
    product_name = fields.Char(
        string='Product name')
    categ_name = fields.Char(
        string='Category name')
    updated_price = fields.Float(
        string='Updated price')
