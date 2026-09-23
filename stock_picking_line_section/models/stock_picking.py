###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _SALE_SECTION_SORT_FALLBACK = 10 ** 9

    def _get_sale_section_data_by_sale_line(self):
        self.ensure_one()
        sale_lines = self.move_ids.sale_line_id.filtered(
            lambda line: not line.display_type)
        if not sale_lines:
            return {}
        sections = {}
        for order in sale_lines.order_id:
            current_section = False
            section_sequence = False
            for order_line in order.order_line.sorted(
                    lambda line: (line.sequence, line.id)):
                if order_line.display_type == 'line_section':
                    current_section = order_line.name
                    section_sequence = order_line.sequence
                elif not order_line.display_type:
                    sections[order_line.id] = {
                        'section_name': current_section or '',
                        'section_sequence': (
                            section_sequence
                            if section_sequence is not False
                            else order_line.sequence),
                        'line_sequence': order_line.sequence,
                        'line_id': order_line.id,
                    }
        return sections

    def _get_sale_line_sections(self, sale_line_sections=None):
        self.ensure_one()
        if sale_line_sections is None:
            return self._get_sale_section_data_by_sale_line()
        fallback_order = self._SALE_SECTION_SORT_FALLBACK
        normalized_sections = {}
        for line_id, section_data in sale_line_sections.items():
            if isinstance(section_data, dict):
                normalized_sections[line_id] = {
                    'section_name': section_data.get('section_name') or '',
                    'section_sequence': section_data.get(
                        'section_sequence', fallback_order),
                    'line_sequence': section_data.get(
                        'line_sequence', fallback_order),
                    'line_id': section_data.get('line_id', line_id),
                }
                continue
            normalized_sections[line_id] = {
                'section_name': section_data or '',
                'section_sequence': fallback_order,
                'line_sequence': fallback_order,
                'line_id': line_id,
            }
        return normalized_sections

    def _get_sale_section_sort_key(
            self, move, fallback_key, sale_line_sections):
        fallback_order = self._SALE_SECTION_SORT_FALLBACK
        if not move:
            return (
                1, fallback_order, fallback_order, fallback_order,
                fallback_key)
        if self.picking_type_code != 'outgoing' or not move.sale_line_id:
            return (
                1, fallback_order, fallback_order, fallback_order,
                fallback_key)
        section_data = sale_line_sections.get(move.sale_line_id.id)
        if not section_data:
            return (
                0, fallback_order, fallback_order, move.sale_line_id.id,
                fallback_key)
        return (
            0, section_data.get('section_sequence', fallback_order),
            section_data.get('line_sequence', fallback_order),
            section_data.get('line_id', move.sale_line_id.id),
            fallback_key)

    def _sort_items_by_sale_section(
            self, items, get_move, get_fallback, sale_line_sections):
        self.ensure_one()
        if hasattr(items, 'sorted'):
            return items.sorted(
                key=lambda item: self._get_sale_section_sort_key(
                    get_move(item), get_fallback(item), sale_line_sections))
        return sorted(
            items,
            key=lambda item: self._get_sale_section_sort_key(
                get_move(item), get_fallback(item), sale_line_sections))

    def _get_moves_sorted_by_sale_section(
            self, moves=None, sale_line_sections=None):
        self.ensure_one()
        moves = moves if moves is not None else self.move_ids
        sale_line_sections = self._get_sale_line_sections(sale_line_sections)
        return self._sort_items_by_sale_section(
            moves,
            lambda move: move,
            lambda move: (move.sequence, move.id),
            sale_line_sections)

    def _get_move_lines_sorted_by_sale_section(
            self, move_lines=None, sale_line_sections=None):
        self.ensure_one()
        move_lines = (
            move_lines if move_lines is not None else self.move_line_ids)
        sale_line_sections = self._get_sale_line_sections(sale_line_sections)
        has_sequence = 'sequence' in self.env['stock.move.line']._fields
        return self._sort_items_by_sale_section(
            move_lines, lambda move_line: move_line.move_id,
            lambda move_line: (
                move_line.sequence if has_sequence else move_line.id,
                move_line.id),
            sale_line_sections)

    def _get_aggregated_line_keys_sorted_by_sale_section(
            self, aggregated_lines, sale_line_sections=None):
        self.ensure_one()
        sale_line_sections = self._get_sale_line_sections(sale_line_sections)
        line_keys = list(aggregated_lines.keys())
        return sorted(
            line_keys, key=lambda line_key: self._get_sale_section_sort_key(
                aggregated_lines[line_key].get('move'), line_key,
                sale_line_sections))

    def _get_move_sale_section_name(
            self, move=None, move_line=None, sale_line_sections=None):
        self.ensure_one()
        move = move or (move_line and move_line.move_id)
        if not move:
            return ''
        if self.picking_type_code != 'outgoing' or not move.sale_line_id:
            return ''
        sale_line_sections = self._get_sale_line_sections(sale_line_sections)
        section_data = sale_line_sections.get(move.sale_line_id.id, {})
        if isinstance(section_data, dict):
            return section_data.get('section_name') or ''
        return section_data or ''
