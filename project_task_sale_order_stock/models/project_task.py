##############################################################################
# For copyright and license notices, see __manifest__.py file in root
# directory
##############################################################################
from odoo import _, fields, models
from odoo.exceptions import UserError


class ProjectTask(models.Model):
    _inherit = 'project.task'

    sale_order_from_task_ids = fields.Many2many(
        comodel_name='sale.order',
        string='Sales order from task',
        copy=False,
    )
    can_create_sale_order_stock = fields.Boolean(
        compute='_compute_can_create_sale_order_stock',
    )
    sale_order_stock_count = fields.Integer(
        compute='_compute_sale_order_stock_count',
        string='Sales orders from task',
    )
    picking_stock_count = fields.Integer(
        compute='_compute_sale_order_stock_count',
        string='Pickings from task',
    )
    stock_move_count = fields.Integer(
        compute='_compute_sale_order_stock_count',
        string='Stock moves from task',
    )
    destination_location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Destination location',
        copy=False,
    )

    def _compute_sale_order_stock_count(self):
        for task in self:
            sale_orders = task.sale_order_from_task_ids
            pickings = sale_orders.picking_ids
            stock_moves = pickings.move_ids
            task.sale_order_stock_count = len(sale_orders)
            task.picking_stock_count = len(pickings)
            task.stock_move_count = len(stock_moves)

    def _compute_can_create_sale_order_stock(self):
        for task in self:
            task.can_create_sale_order_stock = bool(
                task._get_sale_order_stock_partner()
                and (
                    task._get_pending_sale_order_timesheets()
                    or task._get_pending_sale_order_materials()
                )
            )

    def _get_sale_order_stock_records(self):
        self.ensure_one()
        sale_orders = self.sale_order_from_task_ids
        pickings = sale_orders.picking_ids
        stock_moves = pickings.move_ids
        return sale_orders, pickings, stock_moves

    def _get_action(self, action_xml_id, records):
        action = self.env["ir.actions.actions"]._for_xml_id(action_xml_id)
        action['domain'] = [('id', 'in', records.ids)]
        action['context'] = dict(self.env.context, create=False)
        action.pop('res_id', None)
        if len(records) == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = records.id
        return action

    def action_view_sale_order_stock_orders(self):
        self.ensure_one()
        sale_orders, _, _ = self._get_sale_order_stock_records()
        return self._get_action('sale.action_orders', sale_orders)

    def action_view_sale_order_stock_pickings(self):
        self.ensure_one()
        _, pickings, _ = self._get_sale_order_stock_records()
        return self._get_action('stock.action_picking_tree_all', pickings)

    def action_view_sale_order_stock_moves(self):
        self.ensure_one()
        _, _, stock_moves = self._get_sale_order_stock_records()
        return self._get_action('stock.stock_move_action', stock_moves)

    def _get_sale_order_stock_partner(self):
        self.ensure_one()
        return (
            self.partner_id.commercial_partner_id
            or self.project_id.partner_id.commercial_partner_id)

    def _get_sale_order_stock_service_product(self):
        self.ensure_one()
        return (
            self.project_id.timesheet_product_id
            or self.env.ref('sale_timesheet.time_product'))

    def _get_sale_order_stock_warehouse(self):
        self.ensure_one()
        location = self.destination_location_id
        if not location:
            return self.env['stock.warehouse']
        return self.env['stock.warehouse'].search([
            ('company_id', '=', self.company_id.id),
            ('lot_stock_id', 'parent_of', location.id),
        ], limit=1)

    def _get_pending_sale_order_timesheets(self):
        self.ensure_one()
        return self.timesheet_ids.filtered(
            lambda line:
            not line.sale_order_line_id
            and not line.timesheet_invoice_id
            and line.unit_amount > 0)

    def _get_pending_sale_order_materials(self):
        self.ensure_one()
        return self.material_ids.filtered(
            lambda material:
            not material.sale_order_line_id
            and material.quantity > 0)

    def _check_can_create_sale_order_from_task(self):
        self.ensure_one()
        partner = self._get_sale_order_stock_partner()
        if not partner:
            raise UserError(_(
                'A customer is required on the task or project to create a '
                'sales order.'))
        if (
                not self._get_pending_sale_order_timesheets()
                and not self._get_pending_sale_order_materials()
        ):
            raise UserError(_(
                'There are no pending timesheets or materials to add to a '
                'sales order.'))

    def action_create_sale_order_from_task_stock(self):
        self.ensure_one()
        self._check_can_create_sale_order_from_task()
        view = self.env.ref(
            'project_task_sale_order_stock.'
            'project_task_create_sale_order_view_form')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create sales order'),
            'res_model': 'project.task.create.sale.order',
            'view_mode': 'form',
            'views': [(view.id, 'form')],
            'target': 'new',
            'context': {
                'active_id': self.id,
                'active_model': 'project.task',
                'default_task_id': self.id,
            },
        }
