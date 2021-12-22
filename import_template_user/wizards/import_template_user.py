###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class ImportTemplateUser(models.TransientModel):
    _name = 'import.template.user'
    _description = 'Template for import user file'

    def field_get_or_create(self, model, name, search_field, is_required):
        errors = []
        model_name = self.env[model]._description
        if not name:
            if is_required:
                errors.append(_('%s %s not found.') % (model_name, name))
            return None, errors
        model_obj = self.env[model]
        records = model_obj.search([
            (search_field, '=', name),
        ])
        if len(records) > 1:
            errors.append(_(
                'More than one %s found for %s.') % (model_name, name))
        if not records:
            if is_required:
                records = model_obj.create({
                    search_field: name,
                })
            else:
                errors.append(_('%s %s not found.') % (model_name, name))
                return None, errors
        return records[0].id, errors

    def check_required_fields(self, required_fields, data):
        errors = []
        msg = _('The \'%s\' field is required.')
        for field in required_fields:
            required_condition = (
                field not in data or data[field] is None or data[field] == 0.0
                or data[field] == '')
            if required_condition:
                errors.append(msg % field)
        return errors

    def check_relational_fields(self, fields, data):
        required_fields = []
        errors = []
        for field in fields:
            if field in ['name', 'login'] and data[field] == '':
                required_fields.append(field)
        return errors + self.check_required_fields(required_fields, data)

    def import_file(self, simulation=True):
        def _add_errors(errors):
            for error in errors:
                if error != [] and error[1] != [] and error[1] != [[]]:
                    wizard.error(error[0], error[1][0])
        wizard = self._context.get('wizard')
        wizard.line_ids.unlink()
        df = wizard.dataframe_get()
        wizard.dataframe_required_columns(
            df, ['name', 'login', 'user_type:', 'lang'])
        wizard.total_rows = len(df)
        user_obj = self.env['res.users']
        all_errors = []
        orm_errors = False
        for index, row in df.iterrows():
            wizard.savepoint('import_template_user')
            row_index = index + 2
            wizard.step(index + 1, 'Import "%s".' % row['name'])
            data, errors = wizard.get_data_row(self, 'res.users', df, row)
            for error in errors:
                all_errors.append((row_index, [error]))
            data, errors = wizard.parser('res.users', data)
            for error in errors:
                all_errors.append((row_index, [error]))
            errors = self.check_relational_fields(
                ['name', 'login'], data)
            for error in errors:
                all_errors.append((row_index, [error]))
            partner = self.env['res.partner'].search([
                ('email', '=', row['login']),
            ], limit=1)
            if partner:
                data['partner_id'] = partner.id
            user_type = row.get('user_type:')
            if user_type:
                if user_type == 'user':
                    group_id = self.env.ref('base.group_user').id
                else:
                    group_id = self.env.ref('base.group_portal').id
                data['groups_id'] = [(6, 0, [group_id])]
            if simulation:
                wizard.rollback('import_template_user')
                continue
            row_error = any([
                e for e in all_errors if e[0] == row_index and e[1] != []
                and e[1] != [[]]])
            if row_error:
                wizard.rollback('import_template_user')
                continue
            users = user_obj.search([
                ('login', '=', data['login']),
            ])
            try:
                if users:
                    users.write(data)
                else:
                    users = users.create(data)
                wizard.release('import_template_user')
            except Exception as e:
                orm_errors = True
                all_errors.append((row_index, [e]))
                wizard.rollback('import_template_user')
        _add_errors(all_errors)
        return not orm_errors
