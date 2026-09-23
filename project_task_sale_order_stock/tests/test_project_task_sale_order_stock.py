##############################################################################
# For copyright and license notices, see __manifest__.py file in root
# directory
##############################################################################
from unittest import mock

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestProjectTaskSaleOrderStock(TransactionCase):

    def setUp(self):
        super().setUp()
        self.main_company = self.env.company
        self.company_2 = self.env['res.company'].create({
            'name': 'Test company 2',
        })
        self.uom_hour = self.env.ref('uom.product_uom_hour')
        self.uom_unit = self.env.ref('uom.product_uom_unit')
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
        })
        self.employee = self.env['hr.employee'].create({
            'name': 'Test employee',
            'company_id': self.env.company.id,
        })
        self.project = self.env['project.project'].create({
            'name': 'Test project',
            'partner_id': self.partner.id,
            'allow_timesheets': True,
            'allow_billable': True,
        })
        self.product_01 = self.env['product.product'].create({
            'name': 'Test product 1',
            'detailed_type': 'product',
            'list_price': 35,
            'standard_price': 10,
            'uom_id': self.uom_unit.id,
            'uom_po_id': self.uom_unit.id,
        })
        self.product_02 = self.env['product.product'].create({
            'name': 'Test product 2',
            'detailed_type': 'product',
            'list_price': 18,
            'standard_price': 6,
            'uom_id': self.uom_unit.id,
            'uom_po_id': self.uom_unit.id,
        })
        self.service_product = self.env['product.product'].create({
            'name': 'Test timesheet service',
            'detailed_type': 'service',
            'invoice_policy': 'delivery',
            'service_type': 'timesheet',
            'list_price': 99,
            'uom_id': self.uom_hour.id,
            'uom_po_id': self.uom_hour.id,
        })
        self.user = self.env['res.users'].create({
            'name': 'Test user',
            'login': 'test_user',
            'email': 'test_user@test.com',
            'company_ids': [(6, 0, [self.main_company.id, self.company_2.id])],
            'company_id': self.main_company.id,
            'groups_id': [
                (6, 0, [
                    self.env.ref('base.group_user').id,
                    self.env.ref('hr_timesheet.group_hr_timesheet_user').id,
                    self.env.ref('sales_team.group_sale_salesman').id,
                    self.env.ref('project.group_project_user').id,
                ]),
            ],
        })
        self.employee = self.env['hr.employee'].create({
            'name': 'Test employee',
            'company_id': self.env.company.id,
            'user_id': self.user.id,
        })
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.warehouse_company_2 = self.env['stock.warehouse'].search([
            ('company_id', '=', self.company_2.id),
        ], limit=1)
        self.assertTrue(self.warehouse_company_2)
        self.project_company_2 = self.env['project.project'].with_company(
            self.company_2).create({
                'name': 'Test project company 2',
                'partner_id': self.partner.id,
                'allow_timesheets': True,
                'allow_billable': True,
                'company_id': self.company_2.id,
            })
        self.employee_company_2 = self.env['hr.employee'].create({
            'name': 'Test employee company 2',
            'company_id': self.company_2.id,
            'user_id': self.user.id,
        })
        self.env['stock.quant']._update_available_quantity(
            self.product_01, self.stock_location, 10)
        self.env['stock.quant']._update_available_quantity(
            self.product_02, self.stock_location, 10)
        self.env['stock.quant']._update_available_quantity(
            self.product_01, self.warehouse_company_2.lot_stock_id, 10)
        self.env['stock.quant']._update_available_quantity(
            self.product_02, self.warehouse_company_2.lot_stock_id, 10)

    def _create_task(self, with_partner=True):
        project = self.project.copy({
            'name': 'Test project copy',
            'partner_id': self.partner.id if with_partner else False,
        })
        task = self.env['project.task'].create({
            'name': 'Task',
            'project_id': project.id,
            'partner_id': self.partner.id if with_partner else False,
        })
        return task

    def _create_timesheet(self, task, hours):
        return self.env['account.analytic.line'].create({
            'name': 'Thimesheet hours',
            'project_id': task.project_id.id,
            'task_id': task.id,
            'unit_amount': hours,
            'employee_id': self.employee.id,
        })

    def _create_material(self, task, product, quantity):
        return self.env['project.task.material'].create({
            'task_id': task.id,
            'product_id': product.id,
            'quantity': quantity,
        })

    def test_create_task_wizard_computes_partner_and_employee(self):
        partner_2 = self.env['res.partner'].create({
            'name': 'Test partner 2',
        })
        project_2 = self.env['project.project'].create({
            'name': 'Project 2',
            'partner_id': partner_2.id,
            'allow_timesheets': True,
        })
        wizard = self.env['create.project.task'].create({
            'task_name': 'Task',
            'date_deadline': fields.Date.today(),
            'user_id': self.user.id,
            'partner_id': self.partner.id,
            'project_id': self.project.id,
        })
        self.assertEqual(wizard.partner_id, self.project.partner_id)
        timesheet_line = (
            self.env['project.task.create.task.timesheet.line'].create({
                'wizard_id': wizard.id,
                'date': fields.Date.today(),
                'employee_id': self.employee.id,
                'name': 'Computed line',
                'unit_amount': 1,
            }))
        self.assertEqual(timesheet_line.employee_id, self.employee)
        wizard.write({
            'project_id': project_2.id,
        })
        self.assertEqual(wizard.partner_id, partner_2)

    def test_service_product_compute_updates_timesheet_lines(self):
        task = self._create_task()
        self._create_timesheet(task, hours=2.5)
        self._create_material(task, self.product_01, quantity=3)
        wizard = self.env['project.task.create.sale.order'].with_context(
            active_id=task.id,
            active_model='project.task'
        ).create({})
        timesheet_line = wizard.line_ids.filtered(
            lambda line: line.line_type == 'timesheet')
        self.assertEqual(len(timesheet_line), 1)
        material_line = wizard.line_ids.filtered(
            lambda line: line.line_type == 'material')
        self.assertEqual(len(material_line), 1)
        wizard.write({
            'service_product_id': self.service_product.id,
        })
        self.assertEqual(timesheet_line.product_id, self.service_product)
        self.assertEqual(
            timesheet_line.product_uom_id, self.service_product.uom_id)
        self.assertEqual(
            timesheet_line.name, self.service_product.display_name)
        self.assertEqual(
            timesheet_line.price_unit, self.service_product.lst_price)
        self.assertEqual(material_line.product_id, self.product_01)

    def test_create_sale_order_from_task_materials_and_timesheets(self):
        task = self._create_task()
        timesheet = self._create_timesheet(task, hours=2.5)
        material = self._create_material(task, self.product_01, quantity=3)
        wizard = self.env['project.task.create.sale.order'].with_context(
            active_id=task.id,
            active_model='project.task'
        ).create({})
        self.assertEqual(wizard.partner_id, self.partner)
        self.assertEqual(len(wizard.line_ids), 2)
        timesheet_wizard_line = wizard.line_ids.filtered(
            lambda line: line.line_type == 'timesheet')
        self.assertEqual(len(timesheet_wizard_line), 1)
        material_wizard_line = wizard.line_ids.filtered(
            lambda line: line.line_type == 'material')
        self.assertEqual(len(material_wizard_line), 1)
        self.assertEqual(timesheet_wizard_line.quantity, 2.5)
        self.assertEqual(material_wizard_line.quantity, 3)
        action = wizard.action_create_sale_order()
        sale_order = self.env['sale.order'].browse(action['res_id'])
        timesheet_line = sale_order.order_line.filtered(
            lambda line: line.product_id == wizard.service_product_id)
        self.assertEqual(len(timesheet_line), 1)
        material_line = sale_order.order_line.filtered(
            lambda line: line.product_id == self.product_01)
        self.assertEqual(len(material_line), 1)
        self.assertEqual(sale_order.partner_id, self.partner)
        self.assertEqual(len(sale_order.order_line), 2)
        self.assertEqual(timesheet.sale_order_line_id, timesheet_line)
        self.assertEqual(material.sale_order_line_id, material_line)
        self.assertIn(sale_order, task.sale_order_from_task_ids)
        self.assertEqual(timesheet_line.product_uom_qty, 2.5)
        self.assertEqual(material_line.product_uom_qty, 3)
        with self.assertRaises(UserError) as res:
            task.action_create_sale_order_from_task_stock()
        self.assertIn(
            'There are no pending timesheets or materials to add to a '
            'sales order.', str(res.exception))
        sale_order.action_confirm()
        self.assertTrue(sale_order.picking_ids)
        self.assertEqual(
            sale_order.picking_ids.move_ids.product_id, self.product_01)
        self.assertEqual(
            sale_order.picking_ids.move_ids.product_uom_qty, 3)

    def test_create_sale_order_from_task_with_multiple_lines(self):
        task = self._create_task()
        timesheet_1 = self._create_timesheet(task, hours=1.5)
        timesheet_2 = self._create_timesheet(task, hours=2)
        material_1 = self._create_material(task, self.product_01, quantity=1)
        material_2 = self._create_material(task, self.product_01, quantity=2)
        material_3 = self._create_material(task, self.product_02, quantity=4)
        wizard = self.env['project.task.create.sale.order'].with_context(
            active_id=task.id,
            active_model='project.task'
        ).create({})
        self.assertEqual(len(wizard.line_ids), 4)
        timesheet_wizard_lines = wizard.line_ids.filtered(
            lambda line: line.line_type == 'timesheet')
        self.assertEqual(len(timesheet_wizard_lines), 2)
        self.assertEqual(timesheet_wizard_lines.mapped('quantity'), [1.5, 2])
        material_wizard_lines = wizard.line_ids.filtered(
            lambda line: line.line_type == 'material')
        self.assertEqual(len(material_wizard_lines), 2)
        material_line_1 = material_wizard_lines.filtered(
            lambda line: line.product_id == self.product_01)
        self.assertEqual(material_line_1.quantity, 3)
        material_line_2 = material_wizard_lines.filtered(
            lambda line: line.product_id == self.product_02)
        self.assertEqual(material_line_2.quantity, 4)
        action = wizard.action_create_sale_order()
        sale_order = self.env['sale.order'].browse(action['res_id'])
        self.assertEqual(len(sale_order.order_line), 4)
        self.assertEqual(
            len(sale_order.order_line.filtered(
                lambda line: line.product_id == wizard.service_product_id)), 2)
        self.assertEqual(
            len(sale_order.order_line.filtered(
                lambda line: line.product_id == self.product_01)), 1)
        self.assertEqual(
            len(sale_order.order_line.filtered(
                lambda line: line.product_id == self.product_02)), 1)
        material_1_line = sale_order.order_line.filtered(
            lambda line: line.product_id == self.product_01)
        material_2_line = sale_order.order_line.filtered(
            lambda line: line.product_id == self.product_02)
        self.assertEqual(timesheet_1.sale_order_line_id.order_id, sale_order)
        self.assertEqual(
            timesheet_1.sale_order_line_id.product_uom_qty, 1.5)
        self.assertEqual(timesheet_2.sale_order_line_id.order_id, sale_order)
        self.assertEqual(
            timesheet_2.sale_order_line_id.product_uom_qty, 2)
        self.assertEqual(material_1.sale_order_line_id, material_1_line)
        self.assertEqual(material_2.sale_order_line_id, material_1_line)
        self.assertEqual(material_3.sale_order_line_id, material_2_line)

    def test_create_sale_order_from_task_allows_multiple_sale_orders(self):
        task = self._create_task()
        timesheet_1 = self._create_timesheet(task, hours=1)
        wizard_1 = self.env['project.task.create.sale.order'].with_context(
            active_id=task.id,
            active_model='project.task'
        ).create({})
        wizard_1_timesheet_lines = wizard_1.line_ids.filtered(
            lambda line: line.line_type == 'timesheet')
        self.assertEqual(len(wizard_1.line_ids), 1)
        self.assertEqual(len(wizard_1_timesheet_lines), 1)
        self.assertEqual(wizard_1_timesheet_lines.quantity, 1)
        sale_1 = self.env['sale.order'].browse(
            wizard_1.action_create_sale_order()['res_id'])
        self.assertEqual(timesheet_1.sale_order_line_id, sale_1.order_line)
        timesheet_2 = self._create_timesheet(task, hours=2)
        wizard_2 = self.env['project.task.create.sale.order'].with_context(
            active_id=task.id,
            active_model='project.task'
        ).create({})
        wizard_2_timesheet_lines = wizard_2.line_ids.filtered(
            lambda line: line.line_type == 'timesheet')
        self.assertEqual(len(wizard_2.line_ids), 1)
        self.assertEqual(len(wizard_2_timesheet_lines), 1)
        self.assertEqual(wizard_2_timesheet_lines.quantity, 2)
        sale_2 = self.env['sale.order'].browse(
            wizard_2.action_create_sale_order()['res_id'])
        self.assertEqual(timesheet_2.sale_order_line_id, sale_2.order_line)
        self.assertEqual(len(sale_1.order_line), 1)
        self.assertEqual(len(sale_1.order_line), 1)
        self.assertEqual(sale_1.order_line.product_uom_qty, 1)
        self.assertEqual(len(sale_2.order_line), 1)
        self.assertEqual(len(sale_2.order_line), 1)
        self.assertEqual(sale_2.order_line.product_uom_qty, 2)
        self.assertEqual(
            task.sale_order_from_task_ids, sale_1 | sale_2)
        self.assertEqual(task.sale_order_stock_count, 2)
        sale_order_action = task.action_view_sale_order_stock_orders()
        self.assertEqual(
            sale_order_action['domain'],
            [('id', 'in', task.sale_order_from_task_ids.ids)])
        self.assertNotIn('res_id', sale_order_action)

    def test_create_sale_order_from_task_no_pending_lines(self):
        task = self._create_task()
        with self.assertRaises(UserError) as res:
            task.action_create_sale_order_from_task_stock()
        self.assertIn(
            'There are no pending timesheets or materials to add to a '
            'sales order.', str(res.exception))

    def test_create_sale_order_from_task_requires_customer(self):
        task = self._create_task(with_partner=False)
        self._create_timesheet(task, hours=1)
        with self.assertRaises(UserError) as res:
            task.action_create_sale_order_from_task_stock()
        self.assertIn(
            'A customer is required on the task or project to create a '
            'sales order.', str(res.exception))

    def test_create_sale_order_from_task_avoids_duplicates(self):
        task = self._create_task()
        timesheet = self._create_timesheet(task, hours=1)
        material = self._create_material(task, self.product_01, quantity=2)
        wizard = self.env['project.task.create.sale.order'].with_context(
            active_id=task.id,
            active_model='project.task'
        ).create({})
        sale_order = self.env['sale.order'].browse(
            wizard.action_create_sale_order()['res_id'])
        timesheet_line = sale_order.order_line.filtered(
            lambda line: line.product_id == wizard.service_product_id)
        material_line = sale_order.order_line.filtered(
            lambda line: line.product_id == self.product_01)
        self.assertEqual(timesheet.sale_order_line_id, timesheet_line)
        self.assertEqual(material.sale_order_line_id, material_line)
        with self.assertRaises(UserError) as res:
            task.action_create_sale_order_from_task_stock()
        self.assertIn(
            'There are no pending timesheets or materials to add to a '
            'sales order.', str(res.exception))

    def test_create_sale_order_from_task_raises_if_timesheet_is_reused(self):
        task = self._create_task()
        timesheet = self._create_timesheet(task, hours=1)
        wizard_1 = self.env['project.task.create.sale.order'].with_context(
            active_id=task.id,
            active_model='project.task'
        ).create({})
        wizard_2 = self.env['project.task.create.sale.order'].with_context(
            active_id=task.id,
            active_model='project.task'
        ).create({})
        timesheet_line = wizard_2.line_ids.filtered(
            lambda line: line.line_type == 'timesheet')
        self.assertEqual(len(timesheet_line), 1)
        sale_order = self.env['sale.order'].browse(
            wizard_1.action_create_sale_order()['res_id'])
        self.assertEqual(timesheet.sale_order_line_id, sale_order.order_line)
        with self.assertRaises(UserError) as res:
            wizard_2.action_create_sale_order()
        self.assertIn(
            'One of the selected timesheets is already included in a '
            'sales order.', str(res.exception))

    def test_create_sale_order_from_task_raises_if_material_is_reused(self):
        task = self._create_task()
        material = self._create_material(task, self.product_01, quantity=2)
        wizard_1 = self.env['project.task.create.sale.order'].with_context(
            active_id=task.id,
            active_model='project.task'
        ).create({})
        wizard_2 = self.env['project.task.create.sale.order'].with_context(
            active_id=task.id,
            active_model='project.task'
        ).create({})
        material_line = wizard_2.line_ids.filtered(
            lambda line: line.line_type == 'material')
        self.assertEqual(len(material_line), 1)
        sale_order = self.env['sale.order'].browse(
            wizard_1.action_create_sale_order()['res_id'])
        self.assertEqual(material.sale_order_line_id, sale_order.order_line)
        with self.assertRaises(UserError) as res:
            wizard_2.action_create_sale_order()
        self.assertIn(
            'One of the selected materials is already included in a '
            'sales order.', str(res.exception))

    def test_create_sale_order_from_task_requires_at_least_one_line(self):
        task = self._create_task()
        self._create_timesheet(task, hours=1)
        wizard = self.env['project.task.create.sale.order'].with_context(
            active_id=task.id,
            active_model='project.task'
        ).create({})
        self.assertTrue(wizard.line_ids)
        wizard.line_ids.unlink()
        with self.assertRaises(UserError) as res:
            wizard.action_create_sale_order()
        self.assertIn(
            'At least one line is required to create a sales order.',
            str(res.exception))

    def test_smart_buttons_open_related_records(self):
        task = self._create_task()
        self._create_timesheet(task, hours=1)
        self._create_material(task, self.product_01, quantity=2)
        wizard = self.env['project.task.create.sale.order'].with_context(
            active_id=task.id,
            active_model='project.task'
        ).create({})
        action = wizard.action_create_sale_order()
        sale_order = self.env['sale.order'].browse(action['res_id'])
        sale_order.action_confirm()
        self.assertEqual(task.sale_order_from_task_ids, sale_order)
        self.assertEqual(task.sale_order_id, sale_order)
        self.assertEqual(task.sale_order_stock_count, 1)
        self.assertEqual(task.picking_stock_count, 1)
        self.assertEqual(task.stock_move_count, 1)
        self.assertEqual(sale_order.order_line.mapped('task_id'), task)
        self.assertTrue(all(task.timesheet_ids.mapped('sale_order_line_id')))
        self.assertTrue(all(task.material_ids.mapped('sale_order_line_id')))
        self.assertEqual(
            task.action_view_sale_order_stock_orders()['res_id'],
            sale_order.id)
        self.assertEqual(
            task.action_view_sale_order_stock_pickings()['res_id'],
            sale_order.picking_ids.id)
        self.assertEqual(
            task.action_view_sale_order_stock_moves()['res_id'],
            sale_order.picking_ids.move_ids.id)

    def test_wizard_line_type_is_inferred_on_create(self):
        task = self._create_task()
        timesheet = self._create_timesheet(task, hours=1)
        material = self._create_material(task, self.product_01, quantity=2)
        wizard = self.env['project.task.create.sale.order'].with_context(
            active_id=task.id,
            active_model='project.task'
        ).create({})
        timesheet_line = (
            self.env['project.task.create.sale.order.line'].create({
                'wizard_id': wizard.id,
                'product_id': wizard.service_product_id.id,
                'product_uom_id': wizard.service_product_id.uom_id.id,
                'name': 'Timesheet',
                'quantity': 1,
                'price_unit': wizard.service_product_id.lst_price,
                'timesheet_ids': [(6, 0, timesheet.ids)],
            }))
        material_line = (
            self.env['project.task.create.sale.order.line'].create({
                'wizard_id': wizard.id,
                'product_id': self.product_01.id,
                'product_uom_id': self.product_01.uom_id.id,
                'name': 'Material',
                'quantity': 2,
                'price_unit': self.product_01.lst_price,
                'material_ids': [(6, 0, material.ids)],
            }))
        self.assertEqual(timesheet_line.line_type, 'timesheet')
        self.assertEqual(material_line.line_type, 'material')

    def test_create_task_wizard_creates_sale_order_invoice_and_lots(self):
        warehouse = self.env.ref('stock.warehouse0')
        tracked_product = self.env['product.product'].create({
            'name': 'Tracked material',
            'detailed_type': 'product',
            'tracking': 'lot',
            'list_price': 24,
            'standard_price': 8,
            'uom_id': self.uom_unit.id,
            'uom_po_id': self.uom_unit.id,
            'taxes_id': False,
        })
        lot_1 = self.env['stock.lot'].create({
            'name': 'LOT-001',
            'product_id': tracked_product.id,
            'company_id': warehouse.company_id.id,
        })
        lot_2 = self.env['stock.lot'].create({
            'name': 'LOT-002',
            'product_id': tracked_product.id,
            'company_id': warehouse.company_id.id,
        })
        self.env['stock.quant']._update_available_quantity(
            tracked_product, warehouse.lot_stock_id, 1, lot_id=lot_1)
        self.env['stock.quant']._update_available_quantity(
            tracked_product, warehouse.lot_stock_id, 2, lot_id=lot_2)
        wizard = self.env['create.project.task'].create({
            'task_name': 'Wizard Task',
            'date_deadline': fields.Date.today(),
            'user_id': self.env.user.id,
            'partner_id': self.partner.id,
            'project_id': self.project.id,
            'destination_location_id': warehouse.lot_stock_id.id,
        })
        self.env['project.task.create.task.timesheet.line'].create({
            'wizard_id': wizard.id,
            'date': fields.Date.today(),
            'employee_id': self.employee.id,
            'name': 'Wizard work',
            'unit_amount': 1.5,
        })
        self.env['project.task.create.task.material.line'].create({
            'wizard_id': wizard.id,
            'product_id': tracked_product.id,
            'quantity': 1,
            'lot_id': lot_1.id,
        })
        self.env['project.task.create.task.material.line'].create({
            'wizard_id': wizard.id,
            'product_id': tracked_product.id,
            'quantity': 2,
            'lot_id': lot_2.id,
        })
        action = wizard.action_create_task()
        task = self.env['project.task'].browse(action['res_id'])
        sale_order = task.sale_order_from_task_ids
        tracked_order_line = sale_order.order_line.filtered(
            lambda line: line.product_id == tracked_product)
        picking = sale_order.picking_ids
        tracked_move = picking.move_ids.filtered(
            lambda move: move.product_id == tracked_product)
        tracked_move_lines = picking.move_line_ids.filtered(
            lambda line: line.product_id == tracked_product and line.lot_id)
        self.assertEqual(task.name, 'Wizard Task')
        self.assertEqual(task.date_deadline, fields.Date.today())
        self.assertEqual(task.user_ids, self.env.user)
        self.assertEqual(task.partner_id, self.partner)
        self.assertEqual(task.project_id, self.project)
        self.assertEqual(task.destination_location_id, warehouse.lot_stock_id)
        self.assertEqual(len(task.timesheet_ids), 1)
        self.assertEqual(len(task.material_ids), 2)
        self.assertEqual(task.timesheet_ids.employee_id, self.employee)
        self.assertEqual(
            task.material_ids.mapped('product_id'), tracked_product)
        self.assertEqual(task.material_ids.mapped('lot_id'), lot_1 | lot_2)
        self.assertEqual(len(sale_order), 1)
        self.assertEqual(sale_order.warehouse_id, warehouse)
        self.assertEqual(sale_order.state, 'sale')
        self.assertEqual(len(sale_order.invoice_ids), 1)
        self.assertEqual(sale_order.invoice_ids.state, 'draft')
        self.assertEqual(len(sale_order.order_line), 2)
        self.assertEqual(tracked_order_line.product_uom_qty, 3)
        self.assertTrue(all(task.timesheet_ids.mapped('sale_order_line_id')))
        self.assertTrue(all(task.material_ids.mapped('sale_order_line_id')))
        self.assertEqual(
            task.material_ids.mapped('sale_order_line_id'), tracked_order_line)
        self.assertEqual(len(picking), 1)
        self.assertEqual(picking.state, 'done')
        self.assertEqual(tracked_move.product_uom_qty, 3)
        self.assertEqual(len(tracked_move_lines), 2)
        self.assertEqual(
            sorted((line.lot_id.name, line.qty_done)
                   for line in tracked_move_lines),
            [('LOT-001', 1), ('LOT-002', 2)])

    def test_create_task_wizard_raises_if_material_stock_is_insufficient(self):
        warehouse = self.env.ref('stock.warehouse0')
        tracked_product = self.env['product.product'].create({
            'name': 'Tracked material without enough stock',
            'detailed_type': 'product',
            'tracking': 'lot',
            'list_price': 24,
            'standard_price': 8,
            'uom_id': self.uom_unit.id,
            'uom_po_id': self.uom_unit.id,
            'taxes_id': False,
        })
        lot = self.env['stock.lot'].create({
            'name': 'LOT-NO-STOCK',
            'product_id': tracked_product.id,
            'company_id': warehouse.company_id.id,
        })
        self.env['stock.quant']._update_available_quantity(
            tracked_product, warehouse.lot_stock_id, 1, lot_id=lot)
        wizard = self.env['create.project.task'].create({
            'task_name': 'Wizard task no stock',
            'date_deadline': fields.Date.today(),
            'user_id': self.env.user.id,
            'partner_id': self.partner.id,
            'project_id': self.project.id,
            'destination_location_id': warehouse.lot_stock_id.id,
        })
        self.env['project.task.create.task.material.line'].create({
            'wizard_id': wizard.id,
            'product_id': tracked_product.id,
            'quantity': 2,
            'lot_id': lot.id,
        })
        existing_tasks = self.env['project.task'].search_count([
            ('name', '=', 'Wizard task no stock'),
        ])
        with self.assertRaises(UserError) as res:
            wizard.action_create_task()
        self.assertIn(
            'There is not enough stock for lot LOT-NO-STOCK',
            str(res.exception))
        self.assertEqual(
            self.env['project.task'].search_count([
                ('name', '=', 'Wizard task no stock'),
            ]), existing_tasks)

    def test_create_task_wizard_warns_if_invoice_is_not_created(self):
        warehouse = self.env.ref('stock.warehouse0')
        wizard = self.env['create.project.task'].create({
            'task_name': 'Wizard task no invoice',
            'date_deadline': fields.Date.today(),
            'user_id': self.env.user.id,
            'partner_id': self.partner.id,
            'project_id': self.project.id,
            'destination_location_id': warehouse.lot_stock_id.id,
        })
        self.env['project.task.create.task.material.line'].create({
            'wizard_id': wizard.id,
            'product_id': self.product_01.id,
            'quantity': 2,
            'lot_id': False,
        })
        empty_invoice = self.env['account.move']
        with mock.patch.object(
                type(self.env['sale.order']),
                '_create_invoices',
                return_value=empty_invoice):
            action = wizard.action_create_task()
        task = self.env['project.task'].search([
            ('name', '=', 'Wizard task no invoice'),
        ], limit=1)
        self.assertEqual(action['type'], 'ir.actions.client')
        self.assertEqual(action['tag'], 'display_notification')
        self.assertEqual(action['params']['type'], 'warning')
        self.assertEqual(
            action['params']['message'],
            'The sales order could not be invoiced automatically. '
            'The rest of the flow was completed except invoicing.')
        self.assertEqual(action['params']['next']['res_id'], task.id)
        self.assertEqual(task.sale_order_from_task_ids.state, 'sale')
        self.assertEqual(
            task.sale_order_from_task_ids.picking_ids.state, 'done')
        self.assertFalse(task.sale_order_from_task_ids.invoice_ids)

    def test_create_task_wizard_raise_if_nothing_to_invoice(self):
        warehouse = self.env.ref('stock.warehouse0')
        self.service_product.service_policy = 'delivered_timesheet'
        wizard = self.env['create.project.task'].create({
            'task_name': 'Wizard task no invoice',
            'date_deadline': fields.Date.today(),
            'user_id': self.env.user.id,
            'partner_id': self.partner.id,
            'project_id': self.project.id,
            'destination_location_id': warehouse.lot_stock_id.id,
        })
        self.env['project.task.create.task.timesheet.line'].create({
            'wizard_id': wizard.id,
            'date': fields.Date.today(),
            'employee_id': self.employee.id,
            'name': 'Computed line',
            'unit_amount': 1,
        })
        with self.assertRaises(UserError) as res:
            wizard.action_create_task()
        self.assertIn('There is nothing to invoice!', str(res.exception))
        self.assertIn(
            'For Services, you should modify the Service Invoicing Policy',
            str(res.exception))

    def test_create_sale_order_from_task_multicompany(self):
        task = self.env['project.task'].with_company(self.company_2).create({
            'name': 'Task company 2',
            'project_id': self.project_company_2.id,
            'partner_id': self.partner.id,
            'company_id': self.company_2.id,
            'destination_location_id': (
                self.warehouse_company_2.lot_stock_id.id),
        })
        timesheet = self.env['account.analytic.line'].with_company(
            self.company_2).create({
                'name': 'Timesheet company 2',
                'project_id': task.project_id.id,
                'task_id': task.id,
                'unit_amount': 2,
                'employee_id': self.employee_company_2.id,
            })
        material = self.env['project.task.material'].with_company(
            self.company_2).create({
                'task_id': task.id,
                'product_id': self.product_01.id,
                'quantity': 3,
            })
        wizard_model = self.env['project.task.create.sale.order'].with_user(
            self.user).with_company(self.company_2).with_context(
                active_id=task.id,
                active_model='project.task')
        wizard = wizard_model.create({})
        self.assertEqual(wizard.env.company, self.company_2)
        self.assertEqual(wizard.task_id.company_id, self.company_2)
        self.assertEqual(wizard.partner_id, self.partner)
        self.assertEqual(
            wizard.line_ids.mapped('line_type'), ['timesheet', 'material'])
        action = wizard.action_create_sale_order()
        sale_order = self.env['sale.order'].browse(action['res_id'])
        self.assertEqual(task.sale_order_from_task_ids, sale_order)
        self.assertEqual(sale_order.company_id, self.company_2)
        self.assertEqual(sale_order.warehouse_id.company_id, self.company_2)
        self.assertEqual(sale_order.warehouse_id, self.warehouse_company_2)
        self.assertEqual(sale_order.order_line.mapped('task_id'), task)
        self.assertEqual(
            sale_order.order_line.mapped('company_id'), self.company_2)
        timesheet_line = sale_order.order_line.filtered(
            lambda line: line.product_id == wizard.service_product_id)
        material_line = sale_order.order_line.filtered(
            lambda line: line.product_id == self.product_01)
        self.assertEqual(timesheet.sale_order_line_id, timesheet_line)
        self.assertEqual(material.sale_order_line_id, material_line)
