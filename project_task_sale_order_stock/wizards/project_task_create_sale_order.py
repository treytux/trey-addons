##############################################################################
# For copyright and license notices, see __manifest__.py file in root
# directory
##############################################################################
from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProjectTaskCreateSaleOrder(models.TransientModel):
    _name = 'project.task.create.sale.order'
    _description = 'Create sales order from task'

    task_id = fields.Many2one(
        comodel_name='project.task',
        string='Task',
        required=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        required=True,
    )
    service_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Timesheet product',
        domain='''
            [
                ('detailed_type', '=', 'service'),
                ('invoice_policy', '=', 'delivery'),
                ('service_type', '=', 'timesheet'),
            ]
        ''',
        required=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='partner_id.property_product_pricelist.currency_id',
    )
    line_ids = fields.One2many(
        comodel_name='project.task.create.sale.order.line',
        inverse_name='wizard_id',
        string='Lines',
    )
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sales order',
        readonly=True,
        copy=False,
    )

    @api.model
    def _get_active_task(self):
        if self._context.get('active_model') != 'project.task':
            return self.env['project.task']
        return self.env['project.task'].browse(self._context.get('active_id'))

    @api.model
    def _prepare_default_lines(self, task):
        lines = []
        pending_timesheets = task._get_pending_sale_order_timesheets()
        if pending_timesheets:
            service_product = task._get_sale_order_stock_service_product()
            for timesheet in pending_timesheets:
                lines.append((0, 0, {
                    'line_type': 'timesheet',
                    'name': timesheet.name or service_product.display_name,
                    'price_unit': service_product.lst_price,
                    'product_id': service_product.id,
                    'product_uom_id': service_product.uom_id.id,
                    'quantity': timesheet.unit_amount,
                    'timesheet_ids': [(6, 0, timesheet.ids)],
                }))
        grouped_materials = defaultdict(
            lambda: self.env['project.task.material'])
        for material in task._get_pending_sale_order_materials():
            key = (material.product_id.id, material.product_id.uom_id.id)
            grouped_materials[key] |= material
        for product_id, uom_id in grouped_materials:
            materials = grouped_materials[(product_id, uom_id)]
            product = materials[:1].product_id
            quantity = sum(materials.mapped('quantity'))
            lines.append((0, 0, {
                'line_type': 'material',
                'name': product.display_name,
                'price_unit': product.lst_price,
                'product_id': product.id,
                'product_uom_id': uom_id,
                'quantity': quantity,
                'material_ids': [(6, 0, materials.ids)],
            }))
        return lines

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        task = self._get_active_task()
        if not task:
            return values
        task._check_can_create_sale_order_from_task()
        if 'task_id' in fields_list:
            values['task_id'] = task.id
        if 'partner_id' in fields_list:
            values['partner_id'] = task._get_sale_order_stock_partner().id
        if 'service_product_id' in fields_list:
            values['service_product_id'] = (
                task._get_sale_order_stock_service_product().id)
        if 'line_ids' in fields_list:
            values['line_ids'] = self._prepare_default_lines(task)
        return values

    def _create_sale_order_line(self, sale_order, line, line_type=None):
        line_type = line_type or line._get_line_type()
        values = {
            'order_id': sale_order.id,
            'name': line.name,
            'price_unit': line.price_unit,
            'product_id': line.product_id.id,
            'product_uom': line.product_uom_id.id,
            'product_uom_qty': line.quantity,
            'task_id': self.task_id.id,
        }
        if line_type == 'timesheet':
            values.update({
                'project_id': self.task_id.project_id.id,
            })
        return self.env['sale.order.line'].create(values)

    def _create_sale_order(self):
        self.ensure_one()
        sale_order_vals = {
            'partner_id': self.partner_id.id,
            'partner_shipping_id': self.partner_id.id,
            'partner_invoice_id': self.partner_id.id,
            'client_order_ref': self.task_id.display_name,
            'company_id': self.task_id.company_id.id,
        }
        warehouse = self.task_id._get_sale_order_stock_warehouse()
        if warehouse:
            sale_order_vals['warehouse_id'] = warehouse.id
        sale_order = self.env['sale.order'].create(sale_order_vals)
        for line in self.line_ids:
            line_type = line._get_line_type()
            if not line_type:
                continue
            is_timesheet_in_sale = (
                line_type == 'timesheet'
                and line._get_timesheet_records().filtered(
                    'sale_order_line_id'))
            if is_timesheet_in_sale:
                raise UserError(_(
                    'One of the selected timesheets is already included in a '
                    'sales order.'))
            is_material_in_sale = (
                line_type == 'material'
                and line.material_ids.filtered('sale_order_line_id'))
            if is_material_in_sale:
                raise UserError(_(
                    'One of the selected materials is already included in a '
                    'sales order.'))
            sale_order_line = self._create_sale_order_line(
                sale_order, line, line_type=line_type)
            if line_type == 'timesheet':
                line._get_timesheet_records().write({
                    'sale_order_line_id': sale_order_line.id,
                })
            else:
                line.material_ids.write({
                    'sale_order_line_id': sale_order_line.id,
                })
        task_values = {}
        if 'sale_order_id' in self.task_id._fields:
            task_values['sale_order_id'] = sale_order.id
        task_values['sale_order_from_task_ids'] = [(4, sale_order.id)]
        if task_values:
            self.task_id.write(task_values)
        return sale_order

    def action_create_sale_order(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_(
                'At least one line is required to create a sales order.'))
        sale_order = self._create_sale_order()
        self.sale_order_id = sale_order
        action = self.env['ir.actions.actions']._for_xml_id(
            'sale.action_orders')
        action.update({
            'views': [(self.env.ref('sale.view_order_form').id, 'form')],
            'view_mode': 'form',
            'res_id': sale_order.id,
            'name': sale_order.name,
        })
        return action


class ProjectTaskCreateSaleOrderLine(models.TransientModel):
    _name = 'project.task.create.sale.order.line'
    _description = 'Create sales order from task line'

    wizard_id = fields.Many2one(
        comodel_name='project.task.create.sale.order',
        required=True,
    )
    line_type = fields.Selection(
        selection=[
            ('timesheet', 'Timesheet'),
            ('material', 'Material'),
        ],
        string='Line type',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        compute='_compute_timesheet_product_values',
        readonly=False,
        store=True,
        string='Product',
        required=True,
    )
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        compute='_compute_timesheet_product_values',
        readonly=False,
        store=True,
        string='Unit of measure',
        required=True,
    )
    name = fields.Char(
        compute='_compute_timesheet_product_values',
        readonly=False,
        store=True,
        required=True,
        string='Description',
    )
    quantity = fields.Float(
        string='Quantity',
        required=True,
        default=1,
    )
    price_unit = fields.Float(
        compute='_compute_timesheet_product_values',
        readonly=False,
        store=True,
        string='Unit price',
        required=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='wizard_id.currency_id',
    )
    timesheet_ids = fields.Many2many(
        comodel_name='account.analytic.line',
        relation='project_task_create_sale_order_line_aal_rel',
        column1='wizard_line_id',
        column2='analytic_line_id',
        string='Timesheets',
    )
    material_ids = fields.Many2many(
        comodel_name='project.task.material',
        relation='project_task_create_sale_order_line_material_rel',
        column1='wizard_line_id',
        column2='material_id',
        string='Materials',
    )

    def _get_line_type(self):
        self.ensure_one()
        if self.line_type:
            return self.line_type
        if self.timesheet_ids:
            return 'timesheet'
        if self.material_ids:
            return 'material'
        return False

    def _get_timesheet_records(self):
        self.ensure_one()
        return self.timesheet_ids

    @api.depends('line_type', 'wizard_id.service_product_id')
    def _compute_timesheet_product_values(self):
        for line in self:
            if (
                    line.line_type != 'timesheet'
                    or not line.wizard_id.service_product_id):
                continue
            service_product = line.wizard_id.service_product_id
            line.product_id = service_product
            line.name = service_product.display_name
            line.product_uom_id = service_product.uom_id
            line.price_unit = service_product.lst_price

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('line_type'):
                continue
            if vals.get('timesheet_ids'):
                vals['line_type'] = 'timesheet'
            elif vals.get('material_ids'):
                vals['line_type'] = 'material'
        return super().create(vals_list)
