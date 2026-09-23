###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models
from odoo.exceptions import ValidationError


class EmployeeTransferWizard(models.TransientModel):
    _name = 'employee.transfer.wizard'
    _description = 'Wizard to transfer employees to another company'

    _FIELD_NAMES = {
        'name',
        'active',
        'department_id',
        'job_id',
        'work_phone',
        'mobile_phone',
        'work_email',
        'image_1920',
        'address_home_id',
        'bank_account_id',
        'lang',
        'km_home_work',
        'certificate',
        'study_field',
        'study_school',
        'visa_no',
        'permit_no',
        'visa_expire',
        'work_permit_expiration_date',
        'has_work_permit',
        'marital',
        'children',
        'emergency_contact',
        'emergency_phone',
        'country_id',
        'identification_id',
        'passport_id',
        'gender',
        'birthday',
        'place_of_birth',
        'country_of_birth',
        'employee_type',
        'user_id',
        'a3nom_company',
        'a3nom_code',
        'pin',
        'barcode',
        'hourly_cost',
        'mobility_card',
        'badge_ids',
    }

    employee_ids = fields.Many2many(
        comodel_name='hr.employee',
        string='Employees to Transfer',
        required=True,
    )
    target_company_id = fields.Many2one(
        comodel_name='res.company',
        string='Target Company',
        required=True,
    )
    additional_field_ids = fields.Many2many(
        comodel_name='ir.model.fields',
        string='Additional Fields',
        domain=[
            ('model_id.model', '=', 'hr.employee'),
            ('store', '=', True),
            ('ttype', 'not in', ['one2many', 'reference']),
        ],
        help='Select extra fields to copy.',
    )
    archive_option = fields.Boolean(
        string='Archive option',
        default=True,
        help='Mark this check to archive the original employees.',
    )

    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        active_ids = self.env.context.get('active_ids') or []
        if (
                active_ids and 'employee_ids'
                in fields_list
                and not defaults.get('employee_ids')):
            defaults['employee_ids'] = [(6, 0, active_ids)]
        return defaults

    def action_transfer_employees(self):
        self.ensure_one()
        transferred_employee_ids = []
        additional_field_names = self.additional_field_ids.mapped('name')
        target_employee_env = self.env['hr.employee'].with_company(
            self.target_company_id).with_context(
                allowed_company_ids=[self.target_company_id.id],
                company_id=self.target_company_id.id)
        for employee in self.employee_ids:
            employee_data = self._get_employee_data_for_copy(
                employee, additional_field_names)
            source_user_id = employee.user_id.id if employee.user_id else False
            if source_user_id:
                employee_data['user_id'] = source_user_id
                employee.write({
                    'user_id': False,
                })
            new_employee = target_employee_env.create(employee_data)
            if self.archive_option:
                employee.write({
                    'active': False,
                })
            transferred_employee_ids.append(new_employee.id)
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Transferred Employees'),
            'res_model': 'hr.employee',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', transferred_employee_ids)],
        }
        return action

    def _get_employee_data_for_copy(
            self, employee, additional_field_names=None):
        allowed_fields = (
            self._FIELD_NAMES | set(additional_field_names or [])
        ) & set(employee._fields)
        vals = employee.read(list(allowed_fields))[0]
        for field_name, value in list(vals.items()):
            field = employee._fields.get(field_name)
            if not field:
                continue
            if field.type == 'many2one' and isinstance(value, (list, tuple)):
                vals[field_name] = value[0]
            elif field.type == 'many2many' and isinstance(value, list):
                vals[field_name] = [(6, 0, value)]
        vals['company_id'] = self.target_company_id.id
        vals.pop('parent_id', None)
        vals.pop('coach_id', None)
        existing = self.env['hr.employee'].sudo().search([
            ('name', '=', vals.get('name')),
            ('company_id', '=', self.target_company_id.id),
        ])
        if existing:
            raise ValidationError(
                _('An employee with the name \'%s\' already exists '
                  'in the target company.') % vals.get('name'))
        return vals
