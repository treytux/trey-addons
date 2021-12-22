###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, exceptions, fields, models


class WizProductLabel(models.TransientModel):
    _name = 'product.label'
    _description = 'Wizard for report label'

    print_type = fields.Selection(
        selection=[
            ('one', 'One label for each product'),
            ('line', 'One label for each line'),
            ('free_print', 'Free print'),
        ],
        string='Print type',
        default='one',
    )
    state = fields.Selection(
        string='State',
        selection=[
            ('step_1', 'Step 1'),
            ('step_2', 'Step 2'),
            ('done', 'Done'),
        ],
        required=True,
        default='step_1',
    )
    line_ids = fields.One2many(
        comodel_name='product.label.line',
        inverse_name='label_id',
        string='Lines',
    )
    quantity_origin = fields.Selection(
        selection=[
            ('product_uom_qty', 'Initial demand'),
            ('reserved_availability', 'Reserved quantity'),
            ('qty_done', 'Done quantity'),
        ],
        string='Quantity origin',
        default='product_uom_qty',
    )
    quantity_use = fields.Selection(
        selection=[
            ('quantity', 'Show it'),
            ('labels', 'Generate labels'),
        ],
        string='Use quantity to',
        default='labels',
    )
    show_price = fields.Boolean(
        string='Show price',
        default=True,
    )
    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist',
    )
    is_product = fields.Boolean(
        string='Is product',
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res['is_product'] = (
            self._context.get('active_model') in
            ['product.template', 'product.product'])
        res['pricelist_id'] = self.env.ref('product.list0').id
        return res

    def _get_default_report(self):
        reports = self.env['ir.actions.report'].with_context(
            lang='en_US').search([('name', 'ilike', '(product_label)')])
        if not reports.exists():
            return None
        return reports[0]

    @api.model
    def _get_domain_report(self):
        reports = self.env['ir.actions.report'].with_context(
            lang='en_US').search([('name', 'ilike', '(product_label)')])
        return [('id', 'in', reports and reports.ids or [0])]

    report_id = fields.Many2one(
        comodel_name='ir.actions.report',
        string='Report',
        domain=_get_domain_report,
        default=_get_default_report,
        required=True,
    )

    @api.multi
    def _reopen_view(self, ctx=None):
        view = self.env.ref(
            'print_formats_product_label.wizard_product_label')
        if not ctx:
            ctx = {}
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.ids[0],
            'res_model': self._name,
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }

    def get_line_values(self, move_rec, qty, qty_use):
        return {
            'label_id': self.id,
            'product_id': move_rec.product_id.id,
            'quantity': qty,
            'quantity_use': qty_use,
            'show_price': False,
            'price': 0,
            'price_with_taxes': 0,
        }

    @api.model
    def get_lines_by_product(self):
        lines = {}
        moves = self.env['stock.move'].search([
            ('picking_id', '=', self.env.context['active_ids'])])
        for move in moves:
            if (
                move.product_id.type == 'product'
                    and move.product_id.id not in lines):
                lines.setdefault(
                    move.product_id.id,
                    self.get_line_values(move, 1, False)
                )
        return lines.values()

    @api.model
    def get_lines_by_lines(self):
        lines = []
        moves = self.env['stock.move'].search([
            ('picking_id', '=', self.env.context['active_ids'])])
        for move in moves:
            if move.product_id.type != 'product':
                continue
            if move.has_move_lines:
                for move_line in move.move_line_ids:
                    qty = int(
                        self.quantity_origin != 'qty_done'
                        and move[self.quantity_origin]
                        or move_line[self.quantity_origin])
                    lines.append(
                        self.get_line_values(move_line, qty, self.quantity_use)
                    )
            else:
                qty = int(
                    self.quantity_origin != 'qty_done'
                    and move[self.quantity_origin] or 0)
                lines.append(
                    self.get_line_values(move, qty, self.quantity_use)
                )
        return lines

    @api.model
    def get_lines_by_free(self):
        lines = {}
        moves = self.env['stock.move'].search([
            ('picking_id', '=', self.env.context['active_ids'])])
        for move in moves:
            if move.product_id.type != 'product':
                continue
            if move.has_move_lines:
                for move_line in move.move_line_ids:
                    lines.setdefault(
                        move_line.product_id.id,
                        self.get_line_values(move_line, 0, self.quantity_use)
                    )
                    lines[move_line.product_id.id]['quantity'] += int(
                        self.quantity_origin != 'qty_done'
                        and move[self.quantity_origin]
                        or move_line[self.quantity_origin])
            else:
                lines.setdefault(
                    move.product_id.id,
                    self.get_line_values(move, 0, self.quantity_use)
                )
                lines[move.product_id.id]['quantity'] += int(
                    self.quantity_origin != 'qty_done'
                    and move[self.quantity_origin] or 0)
        return lines.values()

    @api.multi
    def button_next_step(self):
        self.ensure_one()
        active_ids = self.env.context['active_ids']
        line_ids = []
        if self.is_product:
            for active_id in active_ids:
                product_id = active_id
                if self._context['active_model'] == 'product.template':
                    template = self.env['product.template'].browse(active_id)
                    product = template.product_variant_id
                    product_id = product.id
                else:
                    product = self.env['product.product'].browse(active_id)
                price = self.pricelist_id.get_product_price(product, 1, False)
                taxes = 0
                for t in product.taxes_id:
                    taxes += price * (t.amount * 0.01)
                price_with_taxes = round(
                    price + taxes, self.env.ref('product.decimal_price').digits)
                line_id = self.env['product.label.line'].create({
                    'label_id': self.id,
                    'product_id': product_id,
                    'quantity': 1,
                    'quantity_use': self.quantity_use,
                    'show_price': self.show_price,
                    'price': price,
                    'price_with_taxes': price_with_taxes,
                })
                line_ids.append(line_id.id)
            self.state = 'done'
        else:
            if self.print_type == 'one':
                lines = self.get_lines_by_product()
            elif self.print_type == 'line':
                lines = self.get_lines_by_lines()
            elif self.print_type == 'free_print':
                lines = self.get_lines_by_free()
            else:
                self.state = 'done'
            line_ids = []
            if self.state != 'done':
                for line in lines:
                    line_id = self.env['product.label.line'].create(line)
                    line_ids.append(line_id.id)
                self.state = 'step_2'
        ctx = self.env.context.copy()
        ctx.update({'active_ids': line_ids})
        return self._reopen_view(ctx=ctx)

    def button_print_accept(self):
        self.ensure_one()
        model = self._context['active_model']
        assert model, 'You must set active_model key in context'
        model = model.replace('.', '_')
        if not hasattr(self, '_print_%s' % model):
            raise exceptions.UserError('Active model not supported: %s' % model)
        return getattr(self, '_print_%s' % model)()

    @api.multi
    def _print_product_template(self):
        ctx = self.env.context.copy()
        ctx.update({'active_model': 'product.product'})
        return self.with_context(ctx).env.ref(
            self.report_id.xml_id).report_action(self.mapped('line_ids'))

    @api.multi
    def _print_product_product(self):
        return self.env.ref(
            self.report_id.xml_id).report_action(self.mapped('line_ids'))

    @api.multi
    def _print_stock_picking(self):
        return self.env.ref(
            self.report_id.xml_id).report_action(self.mapped('line_ids'))


class WizProductLabelFromPickingLine(models.TransientModel):
    _name = 'product.label.line'
    _description = 'Product Label Line'

    label_id = fields.Many2one(
        comodel_name='product.label',
        string='Label',
        required=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
    )
    quantity_use = fields.Selection(
        selection=[
            ('quantity', 'Show it'),
            ('labels', 'Generate labels'),
        ],
        string='Use quantity to',
        default='labels',
    )
    quantity = fields.Integer(
        string='Quantity',
        required=True,
    )
    price = fields.Float(
        string='Price',
    )
    price_with_taxes = fields.Float(
        string='Price with taxes',
    )
    show_price = fields.Boolean(
        string='Show price',
        default=True,
    )
