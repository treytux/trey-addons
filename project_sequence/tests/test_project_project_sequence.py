###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProjectProjectSequence(TransactionCase):

    def test_project_sequence(self):
        sequence = self.env.ref('project_sequence.project_sequence')
        self.assertTrue(sequence)
        number = sequence.number_next_actual
        project_obj = self.env['project.project']
        project = project_obj.create({
            'name': 'Project test',
        })
        self.assertEquals(project.code, 'PR%s' % str(number).zfill(6))
        sequence.number_next_actual *= 10
        number2 = sequence.number_next_actual
        vals = project_obj.default_get(project_obj._fields.keys())
        vals['name'] = 'Project test'
        project = project_obj.create(vals)
        self.assertEquals(project.code, 'PR%s' % str(number2).zfill(6))
        sequence.number_next_actual = number + 1
        project_1 = project_obj.create({
            'name': 'Project test',
        })
        project_2 = project_obj.create({
            'name': 'Project test',
        })
        code_1 = int(project_1.code.replace('PR', ''))
        code_2 = int(project_2.code.replace('PR', ''))
        self.assertEquals(code_1 + 1, code_2)
