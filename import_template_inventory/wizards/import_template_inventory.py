###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class ImportTemplateInventory(models.TransientModel):
    _name = 'import.template.inventory'
    _description = 'Template for import inventory file'

    def _get_location(self, field_name, location_code):
        def _get_location_daughter(loc_name, parent_id):
            physical_loc = self.env.ref('stock.stock_location_locations')
            errors = []
            if not parent_id:
                locations = self.env['stock.location'].search([
                    ('name', '=', loc_name),
                    '|', ('location_id', '=', False),
                    ('location_id', '=', physical_loc.id),
                ])
            else:
                locations = self.env['stock.location'].search([
                    ('name', '=', loc_name),
                    ('location_id', '=', parent_id),
                ])
            if len(locations) > 1:
                errors.append(_(
                    'More than one location found for \'%s\', in \'%s\'.') %
                    (loc_name, field_name))
                return None, errors
            if not locations:
                errors.append(_(
                    'The location \'%s\' does not exist, select one of the '
                    'available ones, for \'%s\'.') % (loc_name, field_name))
                return None, errors
            return locations[0].id, errors
        errors = []
        if not location_code:
            errors.append(_('No value found for \'%s\'.') % field_name)
            return None, errors
        parent_id = None
        locations = location_code.split('/')
        for loc in locations:
            parent_id, errors = _get_location_daughter(loc, parent_id)
            if errors:
                return None, errors
        return parent_id, errors

    def location_id_get_or_create(self, location_code):
        return self._get_location('location_id', location_code)

    def inventory_location_id_get_or_create(self, location_code):
        return self._get_location('inventory_location_id', location_code)

    def product_id_get_or_create(self, product_code):
        errors = []
        if not product_code:
            errors.append(_('No value found for \'product_id\'.'))
            return None, errors
        products = self.env['product.product'].search([
            '|',
            ('default_code', '=', product_code),
            ('barcode', '=', product_code),
        ])
        if len(products) > 1:
            errors.append(_(
                'More than one product found for \'%s\'.') % product_code)
        if not products:
            errors.append(_(
                'The product \'%s\' does not exist, select one of the '
                'available ones.') % product_code)
            return None, errors
        if products[0].type != 'product':
            errors.append(_(
                'The product \'%s\' is a service or consumible and not is a '
                'storable product.') % product_code)
            return None, errors
        return products[0].id, errors

    def _create_inventory(self, inv_name, location_id):
        inventory = self.env['stock.inventory'].create({
            'name': inv_name,
            'filter': 'partial',
            'location_id': location_id,
            'exhausted': True,
        })
        inventory.action_start()
        return inventory.id

    def _get_lot(self, lot_name, product_id):
        errors = []
        lots = self.env['stock.production.lot'].search([
            ('name', '=', lot_name),
            ('product_id', '=', product_id),
        ])
        if len(lots) > 1:
            errors.append(_(
                'More than one lot found for \'%s\'.') % lot_name)
            return None, errors
        if not lots:
            errors.append(_(
                'Lot \'%s\' not found for product \'%s\'.') %
                (lot_name, product_id))
            return None, errors
        return lots[0].id, errors

    def inventory_id_get_or_create(self, name):
        return name, []

    def prod_lot_id_get_or_create(self, name):
        return name, []

    def check_required_fields(self, required_fields, data):
        errors = []
        msg = _('The \'%s\' field is required, you must fill it with a valid '
                'value.')
        for field in required_fields:
            if field == 'product_qty':
                required_condition = (
                    field not in data or data[field] is None
                    or data[field] == '')
            else:
                required_condition = (
                    field not in data or data[field] is None
                    or data[field] == 0.0 or data[field] == '')
            if required_condition:
                errors.append(msg % field)
        return errors

    def _check_product_inventory_confirm(self, product_id):
        errors = []
        inventories = self.env['stock.inventory'].search([
            ('state', '=', 'confirm'),
        ])
        for inv in inventories:
            if len(inv.line_ids.filtered(
                    lambda i: i.product_id.id == product_id)):
                errors.append(_(
                    'Already exists an inventory in progress with the product '
                    '\'%s\'. Please first validate the first inventory '
                    'adjustment before creating another one.') % product_id)
                return errors
        return errors

    def _check_positive_product_qty(self, product_qty):
        errors = []
        msg = _('The value of the \'product_qty\' field cannot be a negative.')
        if product_qty < 0.0:
            errors.append(msg)
        return errors

    def import_file(self, simulation=True):
        def _add_errors(errors):
            for error in errors:
                if error != [] and error[1] != []:
                    wizard.error(error[0], error[1][0])

        wizard = self._context.get('wizard')
        wizard.line_ids.unlink()
        df = wizard.dataframe_get()
        wizard.dataframe_required_columns(
            df, [
                'inventory_id', 'product_id', 'location_id', 'product_qty',
                'inventory_location_id',
            ])
        wizard.total_rows = len(df)
        stock_inv_line_obj = self.env['stock.inventory.line']
        all_errors = []
        orm_errors = False
        inventory_id = None
        for index, row in df.iterrows():
            wizard.savepoint('import_template_inventory')
            row_index = index + 2
            wizard.step(index + 1, 'Import "%s".' % row['product_id'])
            data, errors = wizard.get_data_row(
                self, 'stock.inventory.line', df, row)
            for error in errors:
                all_errors.append((row_index, [error]))
            data, errors = wizard.parser('stock.inventory.line', data)
            for error in errors:
                all_errors.append((row_index, [error]))
            if data['product_qty']:
                errors = self._check_positive_product_qty(data['product_qty'])
                for error in errors:
                    all_errors.append((row_index, [error]))
            errors = self._check_product_inventory_confirm(data['product_id'])
            for error in errors:
                all_errors.append((row_index, [error]))
            if data['prod_lot_id'] and data['product_id']:
                lot_id, errors = self._get_lot(
                    data['prod_lot_id'], data['product_id'])
                data['prod_lot_id'] = lot_id
            for error in errors:
                all_errors.append((row_index, [error]))
            errors = self.check_required_fields([
                'inventory_id', 'product_qty', 'inventory_location_id',
            ], data)
            for error in errors:
                all_errors.append((row_index, [error]))
            if simulation:
                wizard.rollback('import_template_inventory')
                continue
            row_error = any(
                [e for e in all_errors if e[0] == row_index and e[1] != []])
            if row_error:
                wizard.rollback('import_template_inventory')
                continue
            if not inventory_id:
                inventory_id = self._create_inventory(
                    data['inventory_id'], data['inventory_location_id'])
            data['inventory_id'] = inventory_id
            try:
                stock_inv_line_obj.create(data)
                wizard.release('import_template_inventory')
            except Exception as e:
                orm_errors = True
                all_errors.append((row_index, [e]))
                wizard.rollback('import_template_inventory')
        _add_errors(all_errors)
        return not orm_errors
