###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class ImportTemplateStockOrderpoint(models.TransientModel):
    _name = 'import.template.stock_orderpoint'
    _description = 'Template for import stock orderpoint file'

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

    def _check_positive_qty(self, field_name, qty):
        errors = []
        msg = _(
            'The value of the \'%s\' field cannot be a negative.' % field_name)
        if qty < 0.0:
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
                'product_id', 'location_id', 'product_min_qty',
                'product_max_qty', 'qty_multiple',
            ])
        wizard.total_rows = len(df)
        orderpoint_obj = self.env['stock.warehouse.orderpoint']
        all_errors = []
        orm_errors = False
        for index, row in df.iterrows():
            wizard.savepoint('import_template_stock_orderpoint')
            row_index = index + 2
            wizard.step(index + 1, 'Import "%s".' % row['product_id'])
            data, errors = wizard.get_data_row(
                self, 'stock.warehouse.orderpoint', df, row)
            for error in errors:
                all_errors.append((row_index, [error]))
            data, errors = wizard.parser('stock.warehouse.orderpoint', data)
            for error in errors:
                all_errors.append((row_index, [error]))
            if data['qty_multiple']:
                errors = self._check_positive_qty(
                    'qty_multiple', data['qty_multiple'])
                for error in errors:
                    all_errors.append((row_index, [error]))
            orderpoints = orderpoint_obj.search([
                ('product_id', '=', data['product_id']),
                ('location_id', '=', data['location_id']),
            ])
            if len(orderpoints) > 1:
                msg = _(
                    'The combination \'product_id\' and \'location_id\' has '
                    '\'%s\' orderpoints in the systems.' % len(orderpoints))
                all_errors.append((row_index, [msg]))
            if simulation:
                wizard.rollback('import_template_stock_orderpoint')
                continue
            row_error = any(
                [e for e in all_errors if e[0] == row_index and e[1] != []])
            if row_error:
                wizard.rollback('import_template_stock_orderpoint')
                continue
            try:
                if len(orderpoints) == 1:
                    orderpoints.write(data)
                elif len(orderpoints) == 0:
                    orderpoints.create(data)
                wizard.release('import_template_stock_orderpoint')
            except Exception as e:
                orm_errors = True
                all_errors.append((row_index, [e]))
                wizard.rollback('import_template_stock_orderpoint')
        _add_errors(all_errors)
        return not orm_errors
