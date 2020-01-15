###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestContractBusinessUnit(TransactionCase):

    def setUp(self):
        super().setUp()
        unit_obj = self.env['product.business.unit']
        self.unit1 = unit_obj.create({'name': 'Business unit 1'})
        self.unit2 = unit_obj.create({'name': 'Business unit 2'})
        area_obj = self.env['product.business.area']
        self.area1a = area_obj.create({
            'name': 'Unit 1a',
            'unit_id': self.unit1.id,
        })
        self.area2a = area_obj.create({
            'name': 'Unit 2a',
            'unit_id': self.unit2.id,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })

    def test_contract_template(self):
        contract = self.env['contract.template'].create({
            'name': 'Contract template',
            'contract_type': 'sale',
            'area_id': self.area1a.id,
        })
        self.assertEquals(contract.unit_id, self.unit1)
        contract.area_id = self.area2a.id
        self.assertEquals(contract.unit_id, self.unit2)
        contract.unit_id = self.unit1.id
        self.assertEquals(bool(contract.area_id), False)

    def test_contract_contract(self):
        contract = self.env['contract.contract'].create({
            'name': 'Contract contract',
            'partner_id': self.partner.id,
            'contract_type': 'sale',
            'area_id': self.area1a.id,
        })
        self.assertEquals(contract.unit_id, self.unit1)
        contract.area_id = self.area2a.id
        self.assertEquals(contract.unit_id, self.unit2)
        contract.unit_id = self.unit1.id
        self.assertEquals(bool(contract.area_id), False)

    def test_product(self):
        contract = self.env['contract.template'].create({
            'name': 'Contract template 1',
            'contract_type': 'sale',
            'area_id': self.area1a.id,
        })
        product = self.env['product.product'].create({
            'type': 'service',
            'name': 'Test product',
            'is_contract': True,
            'area_id': self.area2a.id,
        })
        self.assertEquals(contract.unit_id, self.unit1)
        self.assertEquals(product.unit_id, self.unit2)
        product.contract_template_id = contract.id
        self.assertEquals(contract.unit_id, self.unit1)
        self.assertEquals(product.unit_id, contract.unit_id)
        self.assertEquals(product.area_id, contract.area_id)
        contract2 = self.env['contract.template'].create({
            'name': 'Contract template 2',
            'contract_type': 'sale',
            'unit_id': self.unit2.id,
        })
        product.contract_template_id = contract2.id
        self.assertEquals(contract2.unit_id, self.unit2)
        self.assertEquals(product.unit_id, contract2.unit_id)
        self.assertEquals(product.area_id, contract2.area_id)
        product.contract_template_id = contract.id
        self.assertEquals(product.unit_id, self.unit1)
        self.assertEquals(product.area_id, self.area1a)
        product.write({
            'is_contract': False,
            'area_id': self.area2a.id,
        })
        self.assertEquals(product.unit_id, self.unit2)
        self.assertEquals(product.area_id, self.area2a)
        product.contract_template_id = False
        self.assertEquals(product.unit_id, self.unit2)
        self.assertEquals(product.area_id, self.area2a)

    def test_product_set_contract_without_area(self):
        contract = self.env['contract.template'].create({
            'name': 'Contract template 1',
            'contract_type': 'sale',
            'unit_id': self.unit1.id,
        })
        product = self.env['product.product'].create({
            'type': 'service',
            'name': 'Test product',
            'is_contract': True,
            'area_id': self.area1a.id,
        })
        self.assertEquals(contract.unit_id, self.unit1)
        self.assertEquals(product.unit_id, self.unit1)
        product.contract_template_id = contract.id
        self.assertEquals(contract.unit_id, self.unit1)
        self.assertEquals(product.unit_id, self.unit1)
        self.assertEquals(product.area_id, self.area1a)
