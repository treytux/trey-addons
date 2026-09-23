###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestSaleCostSimulatorImportBoM(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
        })
        self.pricelist = self.env['product.pricelist'].create({
            'name': 'Test pricelist',
        })
        self.product_main = self.env['product.product'].create({
            'name': 'Main product',
            'type': 'product',
        })
        self.product_component_one = self.env['product.product'].create({
            'name': 'Component one',
            'type': 'product',
        })
        self.product_component_two = self.env['product.product'].create({
            'name': 'Component two',
            'type': 'product',
        })
        self.bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_main.product_tmpl_id.id,
            'product_id': self.product_main.id,
            'product_uom_id': self.product_main.uom_id.id,
            'product_qty': 1,
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.product_component_one.id,
                    'product_qty': 2,
                    'product_uom_id': self.product_component_one.uom_id.id,
                }),
                (0, 0, {
                    'product_id': self.product_component_two.id,
                    'product_qty': 3,
                    'product_uom_id': self.product_component_two.uom_id.id,
                }),
            ],
        })
        self.simulator = self.env['sale.cost.simulator'].create({
            'ref': 'SALE-COST-IMPORT-BOM-001',
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
            'partner_data': self.partner.name,
        })
        self.parent = self.env['sale.cost.line'].create({
            'name': 'Existing Parent',
            'simulator_id': self.simulator.id,
            'pricelist_id': self.pricelist.id,
        })

    def test_onchange_bom_sets_line_name(self):
        wizard = self.env['sale.cost.import_bom'].new({
            'bom_id': self.bom.id,
        })
        wizard.onchange_bom_id()
        self.assertEqual(wizard.line_name, 'Main product')

    def test_button_accept_creates_group_and_component_lines(self):
        wizard = self.env['sale.cost.import_bom'].create({
            'simulator_id': self.simulator.id,
            'parent_id': self.parent.id,
            'bom_id': self.bom.id,
            'line_name': 'Imported group',
            'new_line': True,
        })
        wizard.button_accept()
        lines = self.env['sale.cost.line'].search([
            ('name', '=', 'Imported group'),
            ('parent_id', '=', self.parent.id),
        ])
        self.assertEqual(len(lines), 1)
        components = lines.child_ids.sorted('name')
        self.assertEqual(
            components.mapped('product_id'),
            (self.product_component_one | self.product_component_two).sorted(
                'name'))
        self.assertEqual(components.mapped('quantity'), [2.0, 3.0])
        self.assertEqual(
            components.mapped('pricelist_id.name')[0], 'Test pricelist')

    def test_button_accept_adds_components_to_existing_parent(self):
        wizard = self.env['sale.cost.import_bom'].create({
            'simulator_id': self.simulator.id,
            'parent_id': self.parent.id,
            'bom_id': self.bom.id,
            'new_line': False,
        })
        wizard.button_accept()
        self.assertEqual(len(self.parent.child_ids), 2)
        self.assertEqual(
            self.parent.child_ids.mapped('product_id'),
            self.product_component_one | self.product_component_two)
        self.assertEqual(self.parent.child_ids.mapped('quantity'), [2.0, 3.0])
