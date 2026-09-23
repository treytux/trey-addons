##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.tools import float_compare, float_round


class RentalAvailability(models.AbstractModel):
    _name = 'rental.availability'
    _description = 'Rental availability service'

    @api.model
    def _get_projection_data(
            self, product, warehouse, start_date, end_date, extra_lines=None,
            exclude_order=None, exclude_line=None):
        start_date = fields.Date.to_date(start_date)
        end_date = fields.Date.to_date(end_date)
        event_floor = min(start_date - timedelta(days=1), fields.Date.today())
        product = product.with_company(warehouse.company_id)
        location = warehouse.rental_in_location_id
        rounding = product.uom_id.rounding
        rental_locations = warehouse.rental_in_location_id
        if warehouse.rental_out_location_id:
            rental_locations |= warehouse.rental_out_location_id
        quants = self.env['stock.quant'].with_company(
            warehouse.company_id).search([
                ('product_id', '=', product.id),
                ('location_id', 'child_of', rental_locations.ids),
            ])
        available = sum(quants.mapped('quantity'))
        available = float_round(available, precision_rounding=rounding)
        events = {}
        potential_events = {}
        commitments = self.env['sale.rental']
        stock_moves = self.env['stock.move']

        def add_event(day, amount, target=events):
            if day > end_date + timedelta(days=1):
                return
            day = max(start_date, day)
            target[day] = target.get(day, 0) + amount

        rentals = self.env['sale.rental'].search([
            ('rented_product_id', '=', product.id),
            ('company_id', '=', warehouse.company_id.id),
            ('start_order_id.warehouse_id', '=', warehouse.id),
            ('state', '!=', 'cancel'),
            ('start_date', '<=', end_date),
            ('end_date', '>=', event_floor),
        ])
        if exclude_order:
            rentals = rentals.filtered(
                lambda r: r.start_order_id != exclude_order)
        commitments |= rentals
        for rental in rentals:
            if rental.state == 'in':
                continue
            add_event(rental.start_date, -rental.rental_qty)
            if rental.state != 'sold':
                add_event(
                    rental.end_date + timedelta(days=1), rental.rental_qty)
        confirmed_lines = self.env['sale.order.line'].search([
            ('product_id.rented_product_id', '=', product.id),
            ('rental_type', 'in', ['new_rental', 'rental_extension']),
            ('order_id.state', 'in', ['sale', 'done']),
            ('order_id.company_id', '=', warehouse.company_id.id),
            ('order_id.warehouse_id', '=', warehouse.id),
            ('start_date', '<=', end_date),
            ('end_date', '>=', event_floor),
        ])
        known = rentals.mapped('start_order_line_id')
        for line in confirmed_lines - known:
            if exclude_order and line.order_id == exclude_order:
                continue
            add_event(line.start_date, - line.rental_qty)
            add_event(line.end_date + timedelta(days=1), line.rental_qty)
        if extra_lines:
            for line in extra_lines.filtered(lambda ln: ln.rental_type in (
                    'new_rental', 'rental_extension')):
                if exclude_line and line == exclude_line:
                    continue
                if (line.product_id.rented_product_id != product
                    or not line.start_date
                        or not line.end_date):
                    continue
                add_event(line.start_date, -line.rental_qty)
                add_event(line.end_date + timedelta(days=1), line.rental_qty)
        moves = self.env['stock.move'].search([
            ('product_id', '=', product.id),
            ('company_id', '=', warehouse.company_id.id),
            ('location_id', 'child_of', location.id),
            ('state', 'in', [
                'confirmed', 'waiting', 'partially_available', 'assigned']),
            ('date', '<=', (
                fields.Datetime.to_datetime(end_date + timedelta(days=1)))),
        ])
        rental_moves = rentals.mapped('out_move_id')
        rental_path = location.parent_path or ''
        for move in moves.filtered(
            lambda m: m.location_dest_id != location
            and not (
                m.location_dest_id.parent_path or '').startswith(rental_path)
            and not (
                m.sale_line_id
                and m.sale_line_id.order_id.state in ('draft', 'sent'))
        ) - rental_moves:
            day = max(start_date, fields.Date.to_date(move.date))
            if day > end_date:
                continue
            if float_compare(
                move.reserved_availability,
                move.product_uom_qty,
                precision_rounding=rounding
            ) < 0:
                stock_moves |= move
                add_event(day, - (
                    move.product_uom_qty - move.reserved_availability))
        quotations = self.env['sale.order.line'].search([
            ('product_id.rented_product_id', '=', product.id),
            ('order_id.warehouse_id', '=', warehouse.id),
            ('order_id.company_id', '=', warehouse.company_id.id),
            ('order_id.state', 'in', ['draft', 'sent']),
            ('start_date', '<=', end_date),
            ('end_date', '>=', start_date),
            ('rental_type', 'in', ['new_rental', 'rental_extension']),
        ])
        for line in quotations:
            add_event(line.start_date, line.rental_qty, potential_events)
            add_event(line.end_date + timedelta(days=1),
                      - line.rental_qty, potential_events)
        return {
            'available': available,
            'events': events,
            'potential_events': potential_events,
            'commitments': commitments,
            'stock_moves': stock_moves,
            'rounding': rounding,
        }

    @api.model
    def _get_rental_availability(
            self, product, warehouse, start_date, end_date, quantity=0,
            extra_lines=None, exclude_order=None, exclude_line=None):
        start_date = fields.Date.to_date(start_date)
        end_date = fields.Date.to_date(end_date)
        rounding = product.uom_id.rounding if product else 0.01
        requested = float_round(quantity or 0, precision_rounding=rounding)
        result = {
            'product': product,
            'warehouse': warehouse,
            'start_date': start_date,
            'end_date': end_date,
            'available_quantity': 0,
            'minimum_available_quantity': 0,
            'requested_quantity': requested,
            'first_insufficient_date': False,
            'commitments': self.env['sale.rental'],
            'stock_moves': self.env['stock.move'],
            'is_available': True,
            'warning': False,
        }
        if not product or not warehouse or not warehouse.rental_in_location_id:
            result.update(is_available=False, warning=_(
                'No rental stock location is configured.'))
            return result
        product = product.with_company(warehouse.company_id)
        rounding = product.uom_id.rounding
        if not start_date or not end_date or end_date < start_date:
            result.update(is_available=False, warning=_(
                'Rental dates are invalid.'))
            return result
        projection = self._get_projection_data(
            product, warehouse, start_date, end_date,
            extra_lines=extra_lines, exclude_order=exclude_order,
            exclude_line=exclude_line)
        available = projection['available']
        result['available_quantity'] = available
        result['commitments'] = projection['commitments']
        result['stock_moves'] = projection['stock_moves']
        projected = available
        minimum_available = available
        insufficient_available = False
        for day in (start_date + timedelta(days=i) for i in range(
                (end_date - start_date).days + 1)):
            projected += projection['events'].get(day, 0)
            projected = float_round(projected, precision_rounding=rounding)
            minimum_available = min(minimum_available, projected)
            if (
                float_compare(
                    projected, requested, precision_rounding=rounding)
                    < 0 and not result['first_insufficient_date']
            ):
                result['first_insufficient_date'] = day
                insufficient_available = projected
        result['is_available'] = not result['first_insufficient_date']
        result['minimum_available_quantity'] = minimum_available
        if not result['is_available']:
            result['warning'] = _(
                'Not enough rental availability '
                'for %(product)s in %(warehouse)s '
                'on %(date)s: %(requested)s requested, '
                '%(available)s available.',
                product=product.display_name, warehouse=warehouse.display_name,
                date=result['first_insufficient_date'], requested=requested,
                available=float_round(
                    insufficient_available, precision_rounding=rounding))
        return result
