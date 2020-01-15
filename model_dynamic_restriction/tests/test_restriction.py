###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestRestriction(TransactionCase):

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()
        partner_obj = self.env['res.partner']
        if hasattr(partner_obj.create, 'origin'):
            partner_obj._revert_method('create')
        if hasattr(partner_obj.write, 'origin'):
            partner_obj._revert_method('write')
        if hasattr(partner_obj.unlink, 'origin'):
            partner_obj._revert_method('unlink')

    def create_restriction(self, cwu=111, field_name=None,
                           condition='required', value=None):
        model = self.env.ref('base.model_res_partner')
        cwu = str(cwu).zfill(3)
        restriction = self.env['ir.model.restriction'].create({
            'name': 'Partner test',
            'model_id': model.id,
            'to_create': int(cwu[0]),
            'to_write': int(cwu[1]),
            'to_unlink': int(cwu[2]),
        })
        if not field_name:
            return restriction
        field = model.field_id.filtered(lambda f: f.name == field_name)
        if isinstance(value, (int, float)):
            value_type = 'number'
        else:
            value_type = 'str'
        self.env['ir.model.restriction.line'].create({
            'restriction_id': restriction.id,
            'field_id': field.id,
            'condition': condition,
            'value_%s' % value_type: value,
        })
        return restriction

    def get_restriction_line(self):
        return self.create_restriction(
            cwu=111, field_name='comment', condition='required').line_ids[0]

    def test_path_methods(self):
        partner_obj = self.env['res.partner']
        self.assertFalse(hasattr(partner_obj.create, 'origin'))
        self.assertFalse(hasattr(partner_obj.write, 'origin'))
        self.assertFalse(hasattr(partner_obj.unlink, 'origin'))
        restriction = self.create_restriction(cwu=111)
        self.assertTrue(hasattr(partner_obj.create, 'origin'))
        self.assertTrue(hasattr(partner_obj.write, 'origin'))
        self.assertTrue(hasattr(partner_obj.unlink, 'origin'))
        partner = partner_obj.create(dict(name='Partner test'))
        self.assertEquals(partner.name, 'Partner test')
        restriction.to_unlink = False
        self.assertTrue(hasattr(partner_obj.create, 'origin'))
        self.assertTrue(hasattr(partner_obj.write, 'origin'))
        self.assertFalse(hasattr(partner_obj.unlink, 'origin'))
        restriction.unlink()
        self.assertFalse(hasattr(partner_obj.create, 'origin'))
        self.assertFalse(hasattr(partner_obj.write, 'origin'))
        self.assertFalse(hasattr(partner_obj.unlink, 'origin'))

    def test_restriction_check_required(self):
        line = self.get_restriction_line()
        self.assertFalse(line.check_required('', None, {}, False)[0])
        self.assertTrue(line.check_required('', None, {}, 'test')[0])
        line.restriction_id.unlink()

    def test_restriction_check_number_str_min(self):
        line = self.get_restriction_line()
        line.value_number = 5
        self.assertFalse(line.check_number_str_min('', None, {}, False)[0])
        self.assertFalse(line.check_number_str_min('', None, {}, 1234)[0])
        self.assertFalse(line.check_number_str_min('', None, {}, '1234')[0])
        self.assertTrue(line.check_number_str_min('', None, {}, '12345')[0])
        self.assertTrue(line.check_number_str_min('', None, {}, '123456')[0])
        self.assertTrue(line.check_number_str_min('', None, {}, 123456)[0])
        line.restriction_id.unlink()

    def test_restriction_check_number_str_max(self):
        line = self.get_restriction_line()
        line.value_number = 5
        self.assertTrue(line.check_number_str_max('', None, {}, False)[0])
        self.assertTrue(line.check_number_str_max('', None, {}, 1234)[0])
        self.assertTrue(line.check_number_str_max('', None, {}, '1234')[0])
        self.assertTrue(line.check_number_str_max('', None, {}, '12345')[0])
        self.assertFalse(line.check_number_str_max('', None, {}, '123456')[0])
        self.assertFalse(line.check_number_str_max('', None, {}, 123456)[0])
        line.restriction_id.unlink()

    def test_restriction_check_number_min(self):
        line = self.get_restriction_line()
        line.value_number = 5
        self.assertFalse(line.check_number_min('', None, {}, False)[0])
        self.assertFalse(line.check_number_min('', None, {}, 4)[0])
        self.assertTrue(line.check_number_min('', None, {}, 5)[0])
        self.assertTrue(line.check_number_min('', None, {}, 6)[0])
        line.restriction_id.unlink()

    def test_restriction_check_number_max(self):
        line = self.get_restriction_line()
        line.value_number = 5
        self.assertTrue(line.check_number_max('', None, {}, False)[0])
        self.assertTrue(line.check_number_max('', None, {}, 4)[0])
        self.assertTrue(line.check_number_max('', None, {}, 5)[0])
        self.assertFalse(line.check_number_max('', None, {}, 6)[0])
        line.restriction_id.unlink()

    def test_restriction_check_str_formula(self):
        line = self.get_restriction_line()
        line.value_str = 'result = bool(value == 5)'
        self.assertTrue(line.check_str_formula('', None, {}, 5)[0])
        self.assertFalse(line.check_str_formula('', None, {}, 4)[0])
        line.value_str = 'bool(value == 5)'
        self.assertFalse(line.check_str_formula('', None, {}, 5)[0])
        line.restriction_id.unlink()

    def test_restriction_method_required(self):
        restriction = self.create_restriction(
            cwu=100, field_name='comment', condition='required')
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'Partner test',
                'comment': False,
            })
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'comment': 'Partner comment test',
        })
        partner.comment = False
        self.assertFalse(hasattr(partner.write, 'origin'))
        restriction.to_write = True
        self.assertTrue(hasattr(partner.write, 'origin'))
        partner.comment = 'Partner comment test'
        with self.assertRaises(ValidationError):
            partner.write(dict(comment=False))
        restriction.write(dict(to_write=False, to_unlink=True))
        partner.comment = False
        with self.assertRaises(ValidationError):
            partner.unlink()
        restriction.to_unlink = False
        partner.comment = False
        partner.unlink()
        restriction.unlink()

    def test_restriction_methods_number_str_min(self):
        restriction = self.create_restriction(
            cwu=100, field_name='comment', condition='number_str_min', value=5)
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'Partner test',
                'comment': '1234',
            })
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'comment': '12345',
        })
        partner.comment = False
        restriction.to_write = True
        partner.comment = '12345'
        with self.assertRaises(ValidationError):
            partner.write(dict(comment=False))
        restriction.write(dict(to_write=False, to_unlink=True))
        partner.comment = False
        with self.assertRaises(ValidationError):
            partner.unlink()
        restriction.to_write = False
        partner.comment = '12345'
        partner.unlink()
        restriction.unlink()

    def test_restriction_methods_number_str_max(self):
        restriction = self.create_restriction(
            cwu=100, field_name='comment', condition='number_str_max', value=5)
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'Partner test',
                'comment': '123456',
            })
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'comment': '12345',
        })
        partner.comment = False
        restriction.to_write = True
        partner.comment = '12345'
        with self.assertRaises(ValidationError):
            partner.write(dict(comment='123456'))
        restriction.write(dict(to_write=False, to_unlink=True))
        partner.comment = '123456'
        with self.assertRaises(ValidationError):
            partner.unlink()
        restriction.to_write = False
        partner.comment = False
        partner.unlink()
        restriction.unlink()

    def test_restriction_methods_number_min(self):
        restriction = self.create_restriction(
            cwu=100, field_name='color', condition='number_min', value=5)
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'Partner test',
                'color': 4,
            })
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'color': 5,
        })
        partner.color = False
        restriction.to_write = True
        partner.color = 5
        with self.assertRaises(ValidationError):
            partner.write(dict(color=False))
        restriction.write(dict(to_write=False, to_unlink=True))
        partner.color = False
        with self.assertRaises(ValidationError):
            partner.unlink()
        restriction.to_write = False
        partner.color = 5
        partner.unlink()
        restriction.unlink()

    def test_restriction_methods_number_max(self):
        restriction = self.create_restriction(
            cwu=100, field_name='color', condition='number_max', value=5)
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'Partner test',
                'color': 6,
            })
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'color': 5,
        })
        partner.color = False
        restriction.to_write = True
        partner.color = 5
        with self.assertRaises(ValidationError):
            partner.write(dict(color=6))
        restriction.write(dict(to_write=False, to_unlink=True))
        partner.color = 6
        with self.assertRaises(ValidationError):
            partner.unlink()
        restriction.to_write = False
        partner.color = False
        partner.unlink()
        restriction.unlink()

    def test_domain(self):
        restriction = self.create_restriction(
            cwu=100, field_name='color', condition='number_max', value=5)
        restriction.domain = '[("color", "=", 5)]'
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'Partner test',
                'color': 6,
            })
        restriction.domain = '[("color", "!=", 5)]'
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'color': 5,
        })
        restriction.to_write = True
        with self.assertRaises(ValidationError):
            partner.write(dict(color=6))
        restriction.write(dict(to_write=False, to_unlink=True))
        partner.color = 6
        with self.assertRaises(ValidationError):
            partner.unlink()
        partner.color = 5
        partner.unlink()
        restriction.unlink()

    def test_group(self):
        restriction = self.create_restriction(
            cwu=100, field_name='color', condition='number_max', value=5)
        restriction.domain = '[("color", "=", 5)]'
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'Partner test',
                'color': 6,
            })
        group = self.env['res.groups'].create({
            'name': 'Dynamic restriction test group',
        })
        group.users = self.env.user.ids
        restriction.group_ids = [(6, 0, group.ids)]
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'Partner test',
                'color': 6,
            })
        group.users = [(6, 0, [])]
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'color': 6,
        })
        partner.unlink()
        restriction.unlink()

    def test_errors(self):
        restriction = self.create_restriction(
            cwu=100, field_name='color', condition='number_max', value=5)
        restriction.line_ids[0].user_error_message = 'XxTest errorxX'
        try:
            self.env['res.partner'].create({
                'name': 'Partner test',
                'color': 6,
            })
        except ValidationError as e:
            self.assertIn('XxTest errorxX', e.name)
        restriction.unlink()
