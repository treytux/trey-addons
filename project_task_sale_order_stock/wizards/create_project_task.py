##############################################################################
# For copyright and license notices, see __manifest__.py file in root
# directory
##############################################################################
from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero


class CreateProjectTask(models.TransientModel):
    _name = 'create.project.task'
    _description = 'Create task'

    task_name = fields.Char(
        string='Task name',
        required=True,
    )
    date_deadline = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.today(),
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
        required=True,
        default=lambda self: self.env.user,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        compute='_compute_partner_id',
        readonly=False,
        store=True,
        string='Partner',
        required=True,
    )
    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
        required=True,
        domain='[("partner_id", "=", partner_id)]',
    )
    destination_location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Destination location',
        domain='[("usage", "=", "internal")]',
    )
    timesheet_line_ids = fields.One2many(
        comodel_name='project.task.create.task.timesheet.line',
        inverse_name='wizard_id',
        string='Thimesheet lines',
    )
    material_line_ids = fields.One2many(
        comodel_name='project.task.create.task.material.line',
        inverse_name='wizard_id',
        string='Material lines',
    )

    @api.model
    def _get_active_project(self):
        if self._context.get('active_model') == 'project.project':
            return self.env['project.project'].browse(
                self._context.get('active_id'))
        return self.env['project.project']

    @api.model
    def _get_active_task(self):
        if self._context.get('active_model') == 'project.task':
            return self.env['project.task'].browse(
                self._context.get('active_id'))
        return self.env['project.task']

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        project = self._get_active_project()
        task = self._get_active_task()
        if task and not project:
            project = task.project_id
        if project:
            if 'project_id' in fields_list:
                values['project_id'] = project.id
            if 'partner_id' in fields_list:
                values['partner_id'] = project.partner_id.id
        if task:
            if 'task_name' in fields_list:
                values['task_name'] = task.name
            if 'date_deadline' in fields_list:
                values['date_deadline'] = (
                    task.date_deadline or fields.Date.today())
            if 'user_id' in fields_list and task.user_ids:
                values['user_id'] = task.user_ids[:1].id
            if 'destination_location_id' in fields_list:
                values['destination_location_id'] = (
                    task.destination_location_id.id)
        return values

    @api.depends('project_id')
    def _compute_partner_id(self):
        for wizard in self:
            if wizard.project_id:
                wizard.partner_id = wizard.project_id.partner_id

    def _create_timesheet_lines(self, task):
        timesheet_vals = []
        for line in self.timesheet_line_ids:
            timesheet_vals.append({
                'name': line.name or '/',
                'date': line.date,
                'project_id': task.project_id.id,
                'task_id': task.id,
                'unit_amount': line.unit_amount,
                'employee_id': line.employee_id.id,
            })
        if timesheet_vals:
            self.env['account.analytic.line'].create(timesheet_vals)

    def _create_material_lines(self, task):
        material_vals = []
        for line in self.material_line_ids:
            material_vals.append({
                'task_id': task.id,
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'lot_id': line.lot_id and line.lot_id.id or False,
            })
        if material_vals:
            self.env['project.task.material'].create(material_vals)

    def _create_task(self):
        self.ensure_one()
        task = self.env['project.task'].create({
            'name': self.task_name,
            'date_deadline': self.date_deadline,
            'user_ids': [(6, 0, self.user_id.ids)],
            'partner_id': self.partner_id.id,
            'project_id': self.project_id.id,
            'destination_location_id': self.destination_location_id.id,
        })
        self._create_timesheet_lines(task)
        self._create_material_lines(task)
        return task

    def _get_sale_order_stock_warehouse(self):
        self.ensure_one()
        location = self.destination_location_id
        if not location:
            return self.env['stock.warehouse']
        company = self.project_id.company_id or self.env.company
        return self.env['stock.warehouse'].search([
            ('company_id', '=', company.id),
            ('lot_stock_id', 'parent_of', location.id),
        ], limit=1)

    def _check_material_line_lots(self):
        self.ensure_one()
        for line in self.material_line_ids.filtered('lot_id'):
            if line.lot_id.product_id != line.product_id:
                raise UserError(_(
                    'The lot %s does not belong to product %s.') % (
                        line.lot_id.display_name,
                        line.product_id.display_name))

    def _check_material_line_stock(self):
        self.ensure_one()
        self._check_material_line_lots()
        warehouse = self._get_sale_order_stock_warehouse()
        if not warehouse or not self.material_line_ids:
            return
        stock_location = warehouse.lot_stock_id
        generic_quantities = defaultdict(float)
        lot_quantities = defaultdict(float)
        lot_quantities_by_product = defaultdict(float)
        for line in self.material_line_ids:
            if line.lot_id:
                lot_quantities[(line.product_id, line.lot_id)] += line.quantity
                lot_quantities_by_product[line.product_id] += line.quantity
            else:
                generic_quantities[line.product_id] += line.quantity
        for (product, lot), quantity in lot_quantities.items():
            qty_available = self.env['stock.quant']._get_available_quantity(
                product, stock_location, lot_id=lot)
            if float_compare(
                    qty_available, quantity,
                    precision_rounding=product.uom_id.rounding) < 0:
                raise UserError(_(
                    'There is not enough stock for lot %s of product %s in '
                    'warehouse %s.') % (
                        lot.display_name,
                        product.display_name, warehouse.display_name))
        for product, quantity in generic_quantities.items():
            qty_available = self.env['stock.quant']._get_available_quantity(
                product, stock_location)
            qty_available -= lot_quantities_by_product.get(product, 0.0)
            if float_compare(
                    qty_available, quantity,
                    precision_rounding=product.uom_id.rounding) < 0:
                raise UserError(_(
                    'There is not enough stock for product %s in warehouse '
                    '%s.') % (product.display_name, warehouse.display_name))

    def _create_sale_order_from_task(self, task):
        self.ensure_one()
        if (
                not task._get_pending_sale_order_timesheets()
                and not task._get_pending_sale_order_materials()):
            return self.env['sale.order']
        wizard = self.env['project.task.create.sale.order'].with_context({
            'active_id': task.id,
            'active_model': 'project.task',
        }).create({})
        if not wizard.line_ids:
            return self.env['sale.order']
        return wizard._create_sale_order()

    def _assign_lots_to_stock_moves(self, sale_order, task):
        self.ensure_one()
        materials_by_sale_line = defaultdict(
            lambda: self.env['project.task.material'])
        for material in task.material_ids.filtered(
                lambda m: m.sale_order_line_id and m.lot_id):
            materials_by_sale_line[material.sale_order_line_id] |= material
        if not materials_by_sale_line:
            return
        moves = sale_order.picking_ids.filtered(
            lambda picking: picking.state not in ('done', 'cancel')
        ).move_ids.filtered(
            lambda move: move.sale_line_id in materials_by_sale_line)
        for move in moves:
            materials = materials_by_sale_line[move.sale_line_id]
            lot_quantities = defaultdict(float)
            for material in materials:
                lot_quantities[material.lot_id] += material.quantity
            move._do_unreserve()
            for lot, quantity in lot_quantities.items():
                available_quantity = move._get_available_quantity(
                    move.location_id, lot_id=lot, strict=True)
                reserved_quantity = move._update_reserved_quantity(
                    quantity, available_quantity, move.location_id, lot_id=lot,
                    strict=True)
                if float_compare(
                        reserved_quantity,
                        quantity,
                        precision_rounding=move.product_id.uom_id.rounding
                ) < 0:
                    raise UserError(_(
                        'Not enough quantity is available in lot %s for '
                        'product %s.') % (
                            lot.display_name, move.product_id.display_name))
            reserved_quantity = sum(move.move_line_ids.mapped('reserved_qty'))
            remaining_quantity = move.product_uom_qty - reserved_quantity
            if float_compare(
                    remaining_quantity, 0,
                    precision_rounding=move.product_uom.rounding) > 0:
                move._action_assign()

    def _confirm_and_invoice_sale_order(self, sale_order, task):
        self.ensure_one()
        if not sale_order:
            return False
        sale_order.action_confirm()
        pickings = sale_order.picking_ids.filtered(
            lambda picking: picking.state not in ('done', 'cancel'))
        if pickings:
            pickings.action_assign()
            self._assign_lots_to_stock_moves(sale_order, task)
            for move_line in pickings.move_line_ids.filtered(
                    lambda line: line.state not in ('done', 'cancel')):
                move_line.qty_done = move_line.reserved_uom_qty
            pickings.with_context(
                skip_backorder=True, skip_immediate=True).button_validate()
        invoices = sale_order._create_invoices()
        if not invoices and not float_is_zero(
                sum(sale_order.order_line.mapped('price_total')),
                precision_rounding=sale_order.currency_id.rounding):
            return _(
                'The sales order could not be invoiced automatically. The '
                'rest of the flow was completed except invoicing.')
        return False

    def action_create_task(self):
        self.ensure_one()
        self._check_material_line_stock()
        task = self._create_task()
        sale_order = self._create_sale_order_from_task(task)
        warning_message = self._confirm_and_invoice_sale_order(
            sale_order, task)
        action = self.env['ir.actions.actions']._for_xml_id(
            'project.action_view_all_task')
        action.update({
            'views': [(self.env.ref('project.view_task_form2').id, 'form')],
            'view_mode': 'form',
            'res_id': task.id,
            'name': task.display_name,
        })
        if warning_message:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Warning'),
                    'message': warning_message,
                    'sticky': False,
                    'type': 'warning',
                    'next': action,
                },
            }
        return action


class CreateProjectTaskTimesheetLine(models.TransientModel):
    _name = 'project.task.create.task.timesheet.line'
    _description = 'Create task timesheet line'

    wizard_id = fields.Many2one(
        comodel_name='create.project.task',
        required=True,
        ondelete='cascade',
    )
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.today(),
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        compute='_compute_employee_id',
        string='Employee',
        required=True,
        readonly=False,
        store=True,
    )
    account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        related='wizard_id.project_id.analytic_account_id',
        string='Analytic account',
        readonly=True,
    )
    name = fields.Char(
        string='Description',
        required=True,
    )
    unit_amount = fields.Float(
        string='Duration',
        required=True,
    )

    @api.depends('wizard_id.user_id')
    def _compute_employee_id(self):
        for line in self:
            if line.employee_id or not line.wizard_id.user_id.employee_id:
                continue
            line.employee_id = line.wizard_id.user_id.employee_id


class CreateProjectTaskMaterialLine(models.TransientModel):
    _name = 'project.task.create.task.material.line'
    _description = 'Create task material line'

    wizard_id = fields.Many2one(
        comodel_name='create.project.task',
        required=True,
        ondelete='cascade',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
    )
    quantity = fields.Float(
        string='Quantity',
        required=True,
        default=1,
    )
    lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Lot/Serial number',
        domain='[("product_id", "=", product_id)]',
    )
