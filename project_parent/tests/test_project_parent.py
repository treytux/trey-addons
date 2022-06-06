###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProjectParent(TransactionCase):

    def test_project_parent(self):
        parent = self.env['project.project'].create({
            'name': 'Project parent',
        })
        child = self.env['project.project'].create({
            'name': 'Project test',
            'parent_id': parent.id,
        })
        self.assertEquals(child.parent_id, parent)
