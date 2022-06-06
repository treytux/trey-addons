###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestMaintenanceEquipmentCertification(TransactionCase):

    def setUp(self):
        super().setUp()
        self.equipment = self.env['maintenance.equipment'].create({
            'name': 'Test equipment',
        })
        self.user_demo = self.env.ref('base.user_demo')
        self.assertTrue(self.equipment)

    def test_user_permissions(self):
        with self.assertRaises(AccessError):
            self.equipment.sudo(self.user_demo).write({
                'name': 'Test equipment rename',
            })
        self.user_demo.write({
            'groups_id': [(6, 0, [self.env.ref(
                'maintenance.group_equipment_manager').id])],
        })
        self.equipment.sudo(self.user_demo).write({
            'name': 'Test equipment rename',
        })
        self.assertEquals(self.equipment.name, 'Test equipment rename')
