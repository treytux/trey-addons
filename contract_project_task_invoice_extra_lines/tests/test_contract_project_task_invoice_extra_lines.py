###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime, timedelta

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestContractProjectTaskInvoiceExtraLines(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner_01 = self.env['res.partner'].create({
            'name': 'Test partner 1',
        })
        self.partner_02 = self.env['res.partner'].create({
            'name': 'Test partner 2',
        })
        self.partner_03 = self.env['res.partner'].create({
            'name': 'Test partner 3',
        })
        self.product_quota = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Quota product',
            'standard_price': 10,
            'list_price': 35,
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Product 01',
            'standard_price': 1,
            'list_price': 5,
        })
        self.product_02 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Product 02',
            'standard_price': 2,
            'list_price': 10,
        })

    def create_contract(self, partner, product, qty):
        return self.env['contract.contract'].create({
            'partner_id': partner.id,
            'invoice_partner_id': partner.id,
            'name': 'Contract for %s' % partner.name,
            'contract_line_ids': [
                (0, 0, {
                    'product_id': product.id,
                    'name': product.display_name,
                    'quantity': qty,
                    'uom_id': product.uom_id.id,
                    'price_unit': product.list_price,
                    'recurring_rule_type': 'monthly',
                    'recurring_interval': 1,
                }),
            ],
        })

    def create_project(self, partner):
        return self.env['project.project'].create({
            'partner_id': partner.id,
            'name': 'Project for %s' % partner.name,
        })

    def create_project_task(self, project, partner_ids):
        return self.env['project.task'].create({
            'project_id': project.id,
            'name': 'Task for project %s' % project.name,
            'partner_ids': [(6, 0, partner_ids)],
        })

    def test_project_task_line_extra(self):
        contract_partner_01 = self.create_contract(
            self.partner_01, self.product_quota, 1)
        contract_partner_02 = self.create_contract(
            self.partner_02, self.product_quota, 2)
        self.assertTrue(contract_partner_01)
        self.assertEqual(contract_partner_01.partner_id, self.partner_01)
        self.assertEqual(
            contract_partner_01.invoice_partner_id, self.partner_01)
        contract_lines = contract_partner_01.contract_line_fixed_ids
        self.assertEqual(len(contract_lines), 1)
        self.assertEqual(contract_lines.product_id, self.product_quota)
        self.assertEqual(contract_lines.quantity, 1)
        self.assertEqual(contract_lines.price_unit, 35)
        project = self.create_project(self.partner_01)
        self.assertTrue(project)
        self.assertEqual(project.partner_id, self.partner_01)
        project.contract_id = contract_partner_01.id
        self.assertEqual(project.contract_id, contract_partner_01)
        partner_ids = [self.partner_01.id, self.partner_02.id]
        project_task = self.create_project_task(project, partner_ids)
        self.assertTrue(project_task)
        self.assertEqual(project_task.partner_id, self.partner_01)
        self.assertEqual(project_task.partner_ids.ids, partner_ids)
        self.assertFalse(contract_partner_01.get_project_task_line_extra())
        self.assertFalse(contract_partner_02.get_project_task_line_extra())
        project_task.project_task_line_extra_ids = [
            (0, 0, {
                'product_id': self.product_01.id,
                'quantity': 1,
                'price_unit': self.product_01.list_price,
            }),
            (0, 0, {
                'product_id': self.product_02.id,
                'quantity': 2,
                'price_unit': self.product_02.list_price,
            }),
        ]
        for line_extra in project_task.project_task_line_extra_ids:
            line_extra._onchange_product_id()
            self.assertEqual(line_extra.partner_ids.ids, partner_ids)
        self.assertFalse(
            project_task.project_task_line_extra_ids.mapped('invoice_line_ids')
        )
        contracts = self.env['contract.contract']
        contracts |= contract_partner_01
        contracts |= contract_partner_02
        for contract in contracts:
            contract.recurring_create_invoice()
        invoices_partner_01 = contract_partner_01._get_related_invoices()
        self.assertEqual(len(invoices_partner_01), 1)
        invoice_partner_01 = invoices_partner_01
        invoices_partner_02 = contract_partner_02._get_related_invoices()
        self.assertEqual(len(invoices_partner_02), 1)
        invoice_partner_02 = invoices_partner_02
        self.assertEqual(
            len(project_task.project_task_line_extra_ids.mapped(
                'invoice_line_ids')), 4)
        self.assertEqual(len(invoice_partner_01), 1)
        self.assertEqual(len(invoice_partner_01.invoice_line_ids), 3)
        invoice_line_quota = invoice_partner_01.invoice_line_ids.filtered(
            lambda ln: ln.contract_line_id
            and ln.product_id == self.product_quota)
        self.assertEqual(len(invoice_line_quota), 1)
        self.assertEqual(
            invoice_line_quota.name, self.product_quota.display_name)
        self.assertEqual(invoice_line_quota.quantity, 1)
        self.assertEqual(invoice_line_quota.price_unit, 35)
        self.assertEqual(invoice_line_quota.move_id, invoice_partner_01)
        self.assertTrue(invoice_line_quota.tax_ids)
        invoice_line_extra_p1 = invoice_partner_01.invoice_line_ids.filtered(
            lambda ln: ln.project_task_line_extra_id
            and ln.product_id == self.product_01)
        self.assertEqual(len(invoice_line_extra_p1), 1)
        self.assertEqual(
            invoice_line_extra_p1.name, self.product_01.display_name)
        self.assertEqual(invoice_line_extra_p1.quantity, 1)
        self.assertEqual(invoice_line_extra_p1.price_unit, 5)
        self.assertEqual(invoice_line_extra_p1.move_id, invoice_partner_01)
        self.assertTrue(invoice_line_extra_p1.tax_ids)
        invoice_line_extra_p2 = invoice_partner_01.invoice_line_ids.filtered(
            lambda ln: ln.project_task_line_extra_id
            and ln.product_id == self.product_02)
        self.assertEqual(len(invoice_line_extra_p2), 1)
        self.assertEqual(
            invoice_line_extra_p2.name, self.product_02.display_name)
        self.assertEqual(invoice_line_extra_p2.quantity, 2)
        self.assertEqual(invoice_line_extra_p2.price_unit, 10)
        self.assertEqual(invoice_line_extra_p2.move_id, invoice_partner_01)
        self.assertTrue(invoice_line_extra_p2.tax_ids)
        projects = self.env['project.project'].search([
            ('partner_id', '=', self.partner_02.id),
        ])
        self.assertFalse(projects)
        tasks = self.env['project.task'].search([
            ('partner_id', '=', self.partner_02.id),
        ])
        self.assertFalse(tasks)
        self.assertEqual(len(invoice_partner_02), 1)
        self.assertEqual(len(invoice_partner_02.invoice_line_ids), 3)
        invoice_line_quota = invoice_partner_02.invoice_line_ids.filtered(
            lambda ln: ln.contract_line_id
            and ln.product_id == self.product_quota)
        self.assertEqual(len(invoice_line_quota), 1)
        self.assertEqual(
            invoice_line_quota.name, self.product_quota.display_name)
        self.assertEqual(invoice_line_quota.quantity, 2)
        self.assertEqual(invoice_line_quota.price_unit, 35)
        self.assertEqual(invoice_line_quota.move_id, invoice_partner_02)
        self.assertTrue(invoice_line_quota.tax_ids)
        invoice_line_extra_p1 = invoice_partner_02.invoice_line_ids.filtered(
            lambda ln: ln.project_task_line_extra_id
            and ln.product_id == self.product_01)
        self.assertEqual(len(invoice_line_extra_p1), 1)
        self.assertEqual(
            invoice_line_extra_p1.name, self.product_01.display_name)
        self.assertEqual(invoice_line_extra_p1.quantity, 1)
        self.assertEqual(invoice_line_extra_p1.price_unit, 5)
        self.assertEqual(invoice_line_extra_p1.move_id, invoice_partner_02)
        self.assertTrue(invoice_line_extra_p1.tax_ids)
        invoice_line_extra_p2 = invoice_partner_02.invoice_line_ids.filtered(
            lambda ln: ln.project_task_line_extra_id
            and ln.product_id == self.product_02)
        self.assertEqual(len(invoice_line_extra_p2), 1)
        self.assertEqual(
            invoice_line_extra_p2.name, self.product_02.display_name)
        self.assertEqual(invoice_line_extra_p2.quantity, 2)
        self.assertEqual(invoice_line_extra_p2.price_unit, 10)
        self.assertEqual(invoice_line_extra_p2.move_id, invoice_partner_02)
        self.assertTrue(invoice_line_extra_p2.tax_ids)
        self.assertEqual(
            contract_partner_01.get_project_task_line_extra(),
            project_task.project_task_line_extra_ids)
        self.assertEqual(
            contract_partner_02.get_project_task_line_extra(),
            project_task.project_task_line_extra_ids)
        for contract in contracts:
            contract.recurring_create_invoice()
        self.assertEqual(
            len(project_task.project_task_line_extra_ids.mapped(
                'invoice_line_ids')), 4)
        invoices_partner_01 = contract_partner_01._get_related_invoices()
        self.assertEqual(len(invoices_partner_01), 2)
        invoices_partner_01 = invoices_partner_01.sorted('id')
        invoice_02_partner_01 = invoices_partner_01[1]
        self.assertEqual(len(invoice_02_partner_01.invoice_line_ids), 1)
        invoice_line_quota = invoice_02_partner_01.invoice_line_ids.filtered(
            lambda ln: ln.contract_line_id
            and ln.product_id == self.product_quota)
        self.assertEqual(len(invoice_line_quota), 1)
        self.assertEqual(
            invoice_line_quota.name, self.product_quota.display_name)
        self.assertEqual(invoice_line_quota.quantity, 1)
        self.assertEqual(invoice_line_quota.price_unit, 35)
        self.assertEqual(invoice_line_quota.move_id, invoice_02_partner_01)
        self.assertTrue(invoice_line_quota.tax_ids)
        invoices_partner_02 = contract_partner_02._get_related_invoices()
        self.assertEqual(len(invoices_partner_02), 2)
        invoices_partner_02 = invoices_partner_02.sorted('id')
        invoice_02_partner_02 = invoices_partner_02[1]
        self.assertEqual(len(invoice_02_partner_01.invoice_line_ids), 1)
        invoice_line_quota = invoice_02_partner_02.invoice_line_ids.filtered(
            lambda ln: ln.contract_line_id
            and ln.product_id == self.product_quota)
        self.assertEqual(len(invoice_line_quota), 1)
        self.assertEqual(
            invoice_line_quota.name, self.product_quota.display_name)
        self.assertEqual(invoice_line_quota.quantity, 2)
        self.assertEqual(invoice_line_quota.price_unit, 35)
        self.assertEqual(invoice_line_quota.move_id, invoice_02_partner_02)
        self.assertTrue(invoice_line_quota.tax_ids)
        self.assertEqual(
            contract_partner_01.get_project_task_line_extra(),
            project_task.project_task_line_extra_ids)
        self.assertEqual(
            contract_partner_02.get_project_task_line_extra(),
            project_task.project_task_line_extra_ids)

    def test_project_task_line_extra_date_to_invoice(self):
        contract_partner_01 = self.create_contract(
            self.partner_01, self.product_quota, 1)
        contract_partner_02 = self.create_contract(
            self.partner_02, self.product_quota, 2)
        self.assertTrue(contract_partner_01)
        self.assertEqual(contract_partner_01.partner_id, self.partner_01)
        self.assertEqual(
            contract_partner_01.invoice_partner_id, self.partner_01)
        contract_lines = contract_partner_01.contract_line_fixed_ids
        self.assertEqual(len(contract_lines), 1)
        self.assertEqual(contract_lines.product_id, self.product_quota)
        self.assertEqual(contract_lines.quantity, 1)
        self.assertEqual(contract_lines.price_unit, 35)
        project = self.create_project(self.partner_01)
        self.assertTrue(project)
        self.assertEqual(project.partner_id, self.partner_01)
        project.contract_id = contract_partner_01.id
        self.assertEqual(project.contract_id, contract_partner_01)
        partner_ids = [self.partner_01.id, self.partner_02.id]
        project_task = self.create_project_task(project, partner_ids)
        self.assertTrue(project_task)
        self.assertEqual(project_task.partner_id, self.partner_01)
        self.assertEqual(project_task.partner_ids.ids, partner_ids)
        today = datetime.now().date()
        future_date = today + timedelta(days=45)
        self.assertFalse(contract_partner_01.get_project_task_line_extra())
        self.assertFalse(contract_partner_02.get_project_task_line_extra())
        project_task.project_task_line_extra_ids = [
            (0, 0, {
                'product_id': self.product_01.id,
                'quantity': 1,
                'price_unit': self.product_01.list_price,
            }),
            (0, 0, {
                'product_id': self.product_02.id,
                'quantity': 2,
                'price_unit': self.product_02.list_price,
                'date_to_invoice': future_date,
            }),
        ]
        for line_extra in project_task.project_task_line_extra_ids:
            line_extra._onchange_product_id()
            self.assertEqual(line_extra.partner_ids.ids, partner_ids)
        self.assertFalse(
            project_task.project_task_line_extra_ids.mapped('invoice_line_ids')
        )
        contracts = self.env['contract.contract']
        contracts |= contract_partner_01
        contracts |= contract_partner_02
        for contract in contracts:
            contract.recurring_create_invoice()
        self.assertEqual(
            len(project_task.project_task_line_extra_ids.mapped(
                'invoice_line_ids')), 2)
        invoices_partner_01 = contract_partner_01._get_related_invoices()
        self.assertEqual(len(invoices_partner_01), 1)
        invoice_partner_01 = invoices_partner_01
        invoices_partner_02 = contract_partner_02._get_related_invoices()
        self.assertEqual(len(invoices_partner_02), 1)
        invoice_partner_02 = invoices_partner_02
        self.assertEqual(len(invoice_partner_01), 1)
        self.assertEqual(len(invoice_partner_01.invoice_line_ids), 2)
        invoice_line_quota = invoice_partner_01.invoice_line_ids.filtered(
            lambda ln: ln.contract_line_id
            and ln.product_id == self.product_quota)
        self.assertEqual(len(invoice_line_quota), 1)
        self.assertEqual(
            invoice_line_quota.name, self.product_quota.display_name)
        self.assertEqual(invoice_line_quota.quantity, 1)
        self.assertEqual(invoice_line_quota.price_unit, 35)
        self.assertEqual(invoice_line_quota.move_id, invoice_partner_01)
        self.assertTrue(invoice_line_quota.tax_ids)
        invoice_line_extra_p1 = invoice_partner_01.invoice_line_ids.filtered(
            lambda ln: ln.project_task_line_extra_id
            and ln.product_id == self.product_01)
        self.assertEqual(len(invoice_line_extra_p1), 1)
        self.assertEqual(
            invoice_line_extra_p1.name, self.product_01.display_name)
        self.assertEqual(invoice_line_extra_p1.quantity, 1)
        self.assertEqual(invoice_line_extra_p1.price_unit, 5)
        self.assertEqual(invoice_line_extra_p1.move_id, invoice_partner_01)
        self.assertTrue(invoice_line_extra_p1.tax_ids)
        invoice_line_extra_p2 = invoice_partner_01.invoice_line_ids.filtered(
            lambda ln: ln.project_task_line_extra_id
            and ln.product_id == self.product_02)
        self.assertEqual(len(invoice_line_extra_p2), 0)
        projects = self.env['project.project'].search([
            ('partner_id', '=', self.partner_02.id),
        ])
        self.assertFalse(projects)
        tasks = self.env['project.task'].search([
            ('partner_id', '=', self.partner_02.id),
        ])
        self.assertFalse(tasks)
        self.assertEqual(len(invoice_partner_02), 1)
        self.assertEqual(len(invoice_partner_02.invoice_line_ids), 2)
        invoice_line_quota = invoice_partner_02.invoice_line_ids.filtered(
            lambda ln: ln.contract_line_id
            and ln.product_id == self.product_quota)
        self.assertEqual(len(invoice_line_quota), 1)
        self.assertEqual(
            invoice_line_quota.name, self.product_quota.display_name)
        self.assertEqual(invoice_line_quota.quantity, 2)
        self.assertEqual(invoice_line_quota.price_unit, 35)
        self.assertEqual(invoice_line_quota.move_id, invoice_partner_02)
        self.assertTrue(invoice_line_quota.tax_ids)
        invoice_line_extra_p1 = invoice_partner_02.invoice_line_ids.filtered(
            lambda ln: ln.project_task_line_extra_id
            and ln.product_id == self.product_01)
        self.assertEqual(len(invoice_line_extra_p1), 1)
        self.assertEqual(
            invoice_line_extra_p1.name, self.product_01.display_name)
        self.assertEqual(invoice_line_extra_p1.quantity, 1)
        self.assertEqual(invoice_line_extra_p1.price_unit, 5)
        self.assertEqual(invoice_line_extra_p1.move_id, invoice_partner_02)
        self.assertTrue(invoice_line_extra_p1.tax_ids)
        invoice_line_extra_p2 = invoice_partner_02.invoice_line_ids.filtered(
            lambda ln: ln.project_task_line_extra_id
            and ln.product_id == self.product_02)
        self.assertEqual(len(invoice_line_extra_p2), 0)
        project_task_line_extra_p1 = (
            project_task.project_task_line_extra_ids.filtered(
                lambda ln: ln.product_id == self.product_01)
        )
        self.assertEqual(
            contract_partner_01.get_project_task_line_extra(),
            project_task_line_extra_p1)
        self.assertEqual(
            contract_partner_02.get_project_task_line_extra(),
            project_task_line_extra_p1)
        # Modifico 'recurring_next_date' sólo al contrato del partner 1 para
        # que, al volver a facturar, sólo se facture la línea extra del
        # producto 2 a este contrato, no al contrato del partner 2.
        contract_partner_01.recurring_next_date = today + timedelta(days=100)
        for contract in contracts:
            contract.recurring_create_invoice()
        self.assertEqual(
            len(project_task.project_task_line_extra_ids.mapped(
                'invoice_line_ids')), 3)
        invoices_partner_01 = contract_partner_01._get_related_invoices()
        self.assertEqual(len(invoices_partner_01), 2)
        invoices_partner_01 = invoices_partner_01.sorted('id')
        invoice_02_partner_01 = invoices_partner_01[1]
        self.assertEqual(len(invoice_02_partner_01.invoice_line_ids), 2)
        invoice_line_quota = invoice_02_partner_01.invoice_line_ids.filtered(
            lambda ln: ln.contract_line_id
            and ln.product_id == self.product_quota)
        self.assertEqual(len(invoice_line_quota), 1)
        self.assertEqual(
            invoice_line_quota.name, self.product_quota.display_name)
        self.assertEqual(invoice_line_quota.quantity, 1)
        self.assertEqual(invoice_line_quota.price_unit, 35)
        self.assertEqual(invoice_line_quota.move_id, invoice_02_partner_01)
        self.assertTrue(invoice_line_quota.tax_ids)
        invoice_line_extra_p2 = (
            invoice_02_partner_01.invoice_line_ids.filtered(
                lambda ln: ln.project_task_line_extra_id
                and ln.product_id == self.product_02))
        self.assertEqual(len(invoice_line_extra_p2), 1)
        self.assertEqual(
            invoice_line_extra_p2.name, self.product_02.display_name)
        self.assertEqual(invoice_line_extra_p2.quantity, 2)
        self.assertEqual(invoice_line_extra_p2.price_unit, 10)
        self.assertEqual(invoice_line_extra_p2.move_id, invoice_02_partner_01)
        self.assertTrue(invoice_line_extra_p2.tax_ids)
        invoices_partner_02 = contract_partner_02._get_related_invoices()
        self.assertEqual(len(invoices_partner_02), 2)
        invoices_partner_02 = invoices_partner_02.sorted('id')
        invoice_02_partner_02 = invoices_partner_02[1]
        self.assertEqual(len(invoice_02_partner_02.invoice_line_ids), 1)
        invoice_line_quota = invoice_02_partner_02.invoice_line_ids.filtered(
            lambda ln: ln.contract_line_id
            and ln.product_id == self.product_quota)
        self.assertEqual(len(invoice_line_quota), 1)
        self.assertEqual(
            invoice_line_quota.name, self.product_quota.display_name)
        self.assertEqual(invoice_line_quota.quantity, 2)
        self.assertEqual(invoice_line_quota.price_unit, 35)
        self.assertEqual(invoice_line_quota.move_id, invoice_02_partner_02)
        self.assertTrue(invoice_line_quota.tax_ids)
        self.assertEqual(
            contract_partner_01.get_project_task_line_extra(),
            project_task.project_task_line_extra_ids)
        self.assertEqual(
            contract_partner_02.get_project_task_line_extra(),
            project_task_line_extra_p1)

    def test_project_task_line_extra_date_to_invoice_several_tasks(self):
        contract = self.create_contract(self.partner_01, self.product_quota, 1)
        self.assertTrue(contract)
        self.assertEqual(contract.partner_id, self.partner_01)
        self.assertEqual(contract.invoice_partner_id, self.partner_01)
        contract_lines = contract.contract_line_fixed_ids
        self.assertEqual(len(contract_lines), 1)
        self.assertEqual(contract_lines.product_id, self.product_quota)
        self.assertEqual(contract_lines.quantity, 1)
        self.assertEqual(contract_lines.price_unit, 35)
        project = self.create_project(self.partner_01)
        self.assertTrue(project)
        self.assertEqual(project.partner_id, self.partner_01)
        project.contract_id = contract.id
        self.assertEqual(project.contract_id, contract)
        partner_ids = [self.partner_01.id]
        project_task_01 = self.create_project_task(project, partner_ids)
        self.assertTrue(project_task_01)
        self.assertEqual(project_task_01.partner_id, self.partner_01)
        self.assertEqual(project_task_01.partner_ids.ids, partner_ids)
        today = datetime.now().date()
        future_date = today + timedelta(days=45)
        self.assertFalse(contract.get_project_task_line_extra())
        project_task_01.project_task_line_extra_ids = [
            (0, 0, {
                'product_id': self.product_01.id,
                'quantity': 1,
                'price_unit': self.product_01.list_price,
            }),
            (0, 0, {
                'product_id': self.product_02.id,
                'quantity': 2,
                'price_unit': self.product_02.list_price,
                'date_to_invoice': future_date,
            }),
        ]
        for line_extra in project_task_01.project_task_line_extra_ids:
            line_extra._onchange_product_id()
        self.assertFalse(
            project_task_01.project_task_line_extra_ids.mapped(
                'invoice_line_ids')
        )
        project_task_02 = self.create_project_task(project, partner_ids)
        self.assertTrue(project_task_02)
        self.assertEqual(project_task_02.partner_id, self.partner_01)
        project_task_02.project_task_line_extra_ids = [
            (0, 0, {
                'product_id': self.product_01.id,
                'quantity': 10,
                'price_unit': self.product_01.list_price,
            }),
            (0, 0, {
                'product_id': self.product_02.id,
                'quantity': 20,
                'price_unit': self.product_02.list_price,
            }),
        ]
        for line_extra in project_task_02.project_task_line_extra_ids:
            line_extra._onchange_product_id()
        self.assertFalse(
            project_task_02.project_task_line_extra_ids.mapped(
                'invoice_line_ids'))
        contract.recurring_create_invoice()
        self.assertEqual(
            len(project_task_01.project_task_line_extra_ids.mapped(
                'invoice_line_ids')), 1)
        self.assertEqual(
            len(project_task_02.project_task_line_extra_ids.mapped(
                'invoice_line_ids')), 2)
        invoice = contract._get_related_invoices()
        self.assertEqual(len(invoice), 1)
        self.assertEqual(len(invoice.invoice_line_ids), 4)
        invoice_line_quota = invoice.invoice_line_ids.filtered(
            lambda ln: ln.contract_line_id
            and ln.product_id == self.product_quota)
        self.assertEqual(len(invoice_line_quota), 1)
        self.assertEqual(
            invoice_line_quota.name, self.product_quota.display_name)
        self.assertEqual(invoice_line_quota.quantity, 1)
        self.assertEqual(invoice_line_quota.price_unit, 35)
        self.assertEqual(invoice_line_quota.move_id, invoice)
        self.assertTrue(invoice_line_quota.tax_ids)
        invoice_line_extra_p1_qty1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.project_task_line_extra_id
            and ln.product_id == self.product_01
            and ln.quantity == 1)
        self.assertEqual(
            invoice_line_extra_p1_qty1.name, self.product_01.display_name)
        self.assertEqual(invoice_line_extra_p1_qty1.quantity, 1)
        self.assertEqual(invoice_line_extra_p1_qty1.price_unit, 5)
        self.assertEqual(invoice_line_extra_p1_qty1.move_id, invoice)
        self.assertTrue(invoice_line_extra_p1_qty1.tax_ids)
        invoice_line_extra_p1_qty10 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.project_task_line_extra_id
            and ln.product_id == self.product_01
            and ln.quantity == 10)
        self.assertEqual(len(invoice_line_extra_p1_qty10), 1)
        self.assertEqual(
            invoice_line_extra_p1_qty10.name, self.product_01.display_name)
        self.assertEqual(invoice_line_extra_p1_qty10.price_unit, 5)
        self.assertEqual(invoice_line_extra_p1_qty10.move_id, invoice)
        self.assertTrue(invoice_line_extra_p1_qty10.tax_ids)
        invoice_line_extra_p2_qty20 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.project_task_line_extra_id
            and ln.product_id == self.product_02
            and ln.quantity == 20)
        self.assertEqual(len(invoice_line_extra_p2_qty20), 1)
        self.assertEqual(
            invoice_line_extra_p2_qty20.name, self.product_02.display_name)
        self.assertEqual(invoice_line_extra_p2_qty20.price_unit, 10)
        self.assertEqual(invoice_line_extra_p2_qty20.move_id, invoice)
        self.assertTrue(invoice_line_extra_p2_qty20.tax_ids)
        project_task_line_extra_p1 = (
            project_task_01.project_task_line_extra_ids.filtered(
                lambda ln: ln.product_id == self.product_01)
        )
        self.assertEqual(len(project_task_line_extra_p1), 1)
        self.assertEqual(
            contract.get_project_task_line_extra(),
            project_task_line_extra_p1
            + project_task_02.project_task_line_extra_ids)
        contract.recurring_next_date = today + timedelta(days=100)
        contract.recurring_create_invoice()
        self.assertEqual(
            len(project_task_01.project_task_line_extra_ids.mapped(
                'invoice_line_ids')), 2)
        self.assertEqual(
            len(project_task_02.project_task_line_extra_ids.mapped(
                'invoice_line_ids')), 2)
        invoices = contract._get_related_invoices()
        self.assertEqual(len(invoices), 2)
        invoices = invoices.sorted('id')
        invoice_02 = invoices[1]
        self.assertNotEqual(invoice, invoice_02)
        invoice_line_extra_p1_qty1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.project_task_line_extra_id
            and ln.product_id == self.product_01
            and ln.quantity == 1)
        self.assertEqual(
            invoice_line_extra_p1_qty1.name, self.product_01.display_name)
        self.assertEqual(invoice_line_extra_p1_qty1.quantity, 1)
        self.assertEqual(invoice_line_extra_p1_qty1.price_unit, 5)
        self.assertEqual(invoice_line_extra_p1_qty1.move_id, invoice)
        self.assertTrue(invoice_line_extra_p1_qty1.tax_ids)
        invoice_line_extra_p1_qty10 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.project_task_line_extra_id
            and ln.product_id == self.product_01
            and ln.quantity == 10)
        self.assertEqual(len(invoice_line_extra_p1_qty10), 1)
        self.assertEqual(
            invoice_line_extra_p1_qty10.name, self.product_01.display_name)
        self.assertEqual(invoice_line_extra_p1_qty10.price_unit, 5)
        self.assertEqual(invoice_line_extra_p1_qty10.move_id, invoice)
        self.assertTrue(invoice_line_extra_p1_qty10.tax_ids)
        invoice_line_extra_p2_qty20 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.project_task_line_extra_id
            and ln.product_id == self.product_02
            and ln.quantity == 20)
        self.assertEqual(len(invoice_line_extra_p2_qty20), 1)
        self.assertEqual(
            invoice_line_extra_p2_qty20.name, self.product_02.display_name)
        self.assertEqual(invoice_line_extra_p2_qty20.price_unit, 10)
        self.assertEqual(invoice_line_extra_p2_qty20.move_id, invoice)
        self.assertTrue(invoice_line_extra_p2_qty20.tax_ids)
        self.assertEqual(len(invoice_02.invoice_line_ids), 2)
        invoice_line_quota = invoice_02.invoice_line_ids.filtered(
            lambda ln: ln.contract_line_id
            and ln.product_id == self.product_quota)
        self.assertEqual(len(invoice_line_quota), 1)
        self.assertEqual(
            invoice_line_quota.name, self.product_quota.display_name)
        self.assertEqual(invoice_line_quota.quantity, 1)
        self.assertEqual(invoice_line_quota.price_unit, 35)
        self.assertEqual(invoice_line_quota.move_id, invoice_02)
        self.assertTrue(invoice_line_quota.tax_ids)
        invoice_line_extra_p2_qty2 = invoice_02.invoice_line_ids.filtered(
            lambda ln: ln.project_task_line_extra_id
            and ln.product_id == self.product_02
            and ln.quantity == 2)
        self.assertEqual(len(invoice_line_extra_p2_qty2), 1)
        self.assertEqual(
            invoice_line_extra_p2_qty2.name, self.product_02.display_name)
        self.assertEqual(invoice_line_extra_p2_qty2.price_unit, 10)
        self.assertEqual(invoice_line_extra_p2_qty2.move_id, invoice_02)
        self.assertTrue(invoice_line_extra_p2_qty2.tax_ids)
        self.assertEqual(
            contract.get_project_task_line_extra(),
            project_task_01.project_task_line_extra_ids
            + project_task_02.project_task_line_extra_ids)

    def test_constraint_same_partner(self):
        contract = self.create_contract(self.partner_01, self.product_quota, 1)
        partner_02 = self.env['res.partner'].create({
            'name': 'Test partner 2',
        })
        project = self.create_project(partner_02)
        self.assertNotEqual(contract.partner_id, project.partner_id)
        with self.assertRaises(ValidationError) as result:
            project.contract_id = contract.id
        msg = 'The contract and the project must belong to the same partner.'
        self.assertIn(msg, result.exception.args[0])
        project.partner_id = self.partner_01.id
        project.contract_id = contract.id
        project.contract_id = False
