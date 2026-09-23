###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    move_line_relation_ids = fields.Many2many(
        comodel_name='stock.move.line.relation',
        relation='move_line_move_lines_rel',
        column1='col_move_line',
        column2='col_move_line_rel',
        readonly=True,
    )
    move_line_relation_count = fields.Integer(
        string='Move line relation count',
        compute='_compute_move_line_relation_count',
    )

    @api.depends('move_line_relation_ids')
    def _compute_move_line_relation_count(self):
        move_line_relation_obj = self.env['stock.move.line.relation']
        for move_line in self:
            move_line.move_line_relation_count = (
                move_line_relation_obj.search_count([
                    ('move_line_id', '=', move_line.id),
                ]))

    def action_view_stock_move_relation_ids(self):
        self.ensure_one()
        tree_view = self.env.ref(
            'stock_move_line_relation.view_stock_move_line_relation_tree')
        form_view = self.env.ref(
            'stock_move_line_relation.view_stock_move_line_relation_form')
        search_view = self.env.ref(
            'stock_move_line_relation.view_stock_move_line_relation_search')
        move_lines_rel = self.env['stock.move.line.relation'].search([
            ('move_line_id', '=', self.id),
        ])
        return {
            'name': _('Stock move line relation'),
            'res_model': 'stock.move.line.relation',
            'type': 'ir.actions.act_window',
            'views': [
                (tree_view.id, 'tree'),
                (form_view.id, 'form'),
            ],
            'search_view_id': search_view.id,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'domain': [('id', 'in', move_lines_rel.ids)],
        }

    def _create_relation(self, qty):
        self.ensure_one()
        if qty <= 0:
            raise exceptions.ValidationError(
                _('Quantity in relations must be greater than 0'))
        return self.env['stock.move.line.relation'].create({
            'move_line_id': self.id,
            'quantity': qty,
            'price_unit': self.move_id.price_unit,
        })

    def _create_move_line_relation_in(self):
        move = self[0].move_id
        if not move._is_in():
            return False
        is_return_sale_return = (
            move.is_return if 'is_return' in move._fields else False)
        is_return_from_picking = bool(move.move_orig_ids)
        if is_return_sale_return:
            for move_line in self:
                relations = self.env['stock.move.line.relation'].browse([])
                out_move_lines = move_line.search(
                    [
                        ('lot_id', '=', move_line.lot_id.id),
                        ('product_id', '=', move_line.product_id.id),
                        ('state', '=', 'done'),
                        ('date', '<', move_line.date),
                    ],
                    order='date desc')
                out_move_lines = out_move_lines.filtered(
                    lambda ml: ml.move_id._is_out())
                if not out_move_lines:
                    return False
                qty_need = move_line.qty_done
                in_move_lines = out_move_lines.mapped(
                    'move_line_relation_ids.move_line_id')
                in_move_lines = in_move_lines.sorted(key='id', reverse=True)
                for in_move_line in in_move_lines:
                    if qty_need <= in_move_line.qty_done:
                        relations |= in_move_line._create_relation(qty_need)
                        qty_need = 0
                    else:
                        relations |= in_move_line._create_relation(
                            in_move_line.qty_done)
                        qty_need -= in_move_line.qty_done
                    if qty_need == 0:
                        break
                move_line.write({
                    'move_line_relation_ids': [(4, r.id) for r in relations],
                })
        elif is_return_from_picking:
            relations = self.env['stock.move.line.relation'].browse([])
            for move_line in self:
                qty_need = move_line.qty_done
                for out_orig_move in move_line.move_id.move_orig_ids:
                    if not out_orig_move._is_out():
                        continue
                    out_rel_move_line = (
                        out_orig_move.move_line_ids.filtered(
                            lambda ml: (ml.lot_id == move_line.lot_id)
                        ).mapped('move_line_relation_ids.move_line_id')
                    )
                    if not out_rel_move_line:
                        continue
                    for out_rel_move_line in out_rel_move_line:
                        qty = min(out_rel_move_line.qty_done, qty_need)
                        relations |= out_rel_move_line._create_relation(qty)
                        qty_need -= qty
                        if qty_need == 0:
                            break
                    if qty_need == 0:
                        break
                move_line.write({
                    'move_line_relation_ids': [(4, r.id) for r in relations],
                })
        return True

    def _create_move_line_relation_out(self):
        def available_qty_before_move_line(move_line):
            _domain_quant_loc, domain_move_in_loc, domain_move_out_loc = (
                move_line.product_id._get_domain_locations())
            qty_in = self.env['stock.move.line'].read_group(
                [
                    ('state', '=', 'done'),
                    ('date', '<', move_line.date),
                    ('product_id', '=', move_line.product_id.id),
                    ('lot_id', '=', move_line.lot_id.id)
                ] + domain_move_in_loc,
                ['product_id', 'qty_done'],
                ['product_id'],
                orderby='id'
            )
            qty_in = qty_in[0]['qty_done'] if qty_in else 0
            qty_out = self.env['stock.move.line'].read_group(
                [
                    ('state', '=', 'done'),
                    ('date', '<', move_line.date),
                    ('product_id', '=', move_line.product_id.id),
                    ('lot_id', '=', move_line.lot_id.id)
                ] + domain_move_out_loc,
                ['product_id', 'qty_done'],
                ['product_id'],
                orderby='id'
            )
            qty_out = qty_out[0]['qty_done'] if qty_out else 0
            return qty_in - qty_out

        move = self[0].move_id
        if not move._is_out():
            return False
        move_candidates = (
            move.product_id._get_fifo_candidates_in_move_with_company(
                move.company_id.id
            )
        )
        move_line_candidates = move_candidates.mapped('move_line_ids')
        for move_line in self:
            in_move_lines = move_line_candidates.filtered(
                lambda cml:
                    cml.lot_id == move_line.lot_id
                    and cml.date <= move_line.date)
            relations = self.env['stock.move.line.relation'].browse([])
            qty_need = move_line.qty_done
            qty_available_total = available_qty_before_move_line(move_line)
            for in_move_line in in_move_lines:
                qty_available = qty_available_total
                for ml in in_move_lines.sorted(key='date', reverse=True):
                    if ml == in_move_line:
                        break
                    qty_available -= ml.qty_done
                if qty_available <= 0:
                    continue
                elif qty_need <= qty_available:
                    relations |= in_move_line._create_relation(qty_need)
                    qty_need = 0
                else:
                    relations |= in_move_line._create_relation(qty_available)
                    qty_need -= qty_available
                    qty_available_total -= qty_available
                if qty_need == 0:
                    break
            move_line.write({
                'move_line_relation_ids': [(4, r.id) for r in relations],
            })
        return True

    def create_move_line_relation(self):
        move_lines_group_move = {}
        for move_line in self:
            move_lines_group_move.setdefault(
                move_line.move_id, self.env['stock.move.line'])
            move_lines_group_move[move_line.move_id] |= move_line
        for _move, move_lines in move_lines_group_move.items():
            move_lines._create_move_line_relation_in()
            move_lines._create_move_line_relation_out()
