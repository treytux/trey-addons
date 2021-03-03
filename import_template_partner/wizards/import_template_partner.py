###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class ImportTemplatePartner(models.TransientModel):
    _name = 'import.template.partner'
    _description = 'Template for import partner file'

    def parse_float(self, value):
        try:
            return int(value)
        except Exception:
            return value

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

    def parent_id_get_or_create(self, parent_name):
        return self.field_get_or_create(
            'res.partner', parent_name, 'name', False)

    def city_id_get_or_create(self, name):
        return self.field_get_or_create('res.city', name, 'name', False)

    def state_id_get_or_create(self, name):
        return self.field_get_or_create(
            'res.country.state', name, 'name', False)

    def zip_id_get_or_create(self, name):
        name = self.parse_float(name)
        return self.field_get_or_create('res.city.zip', name, 'name', False)

    def country_id_get_or_create(self, name):
        return self.field_get_or_create('res.country', name, 'name', False)

    def commission_get_or_create(self, name):
        return self.field_get_or_create('sale.commission', name, 'name', False)

    def user_id_get_or_create(self, name):
        return self.field_get_or_create('res.users', name, 'name', False)

    def invoice_group_method_id_get_or_create(self, name):
        return self.field_get_or_create(
            'sale.invoice.group.method', name, 'name', False)

    def property_payment_term_id_get_or_create(self, name):
        return self.field_get_or_create(
            'account.payment.term', name, 'name', False)

    def property_supplier_payment_term_id_get_or_create(self, name):
        return self.field_get_or_create(
            'account.payment.term', name, 'name', False)

    def customer_payment_mode_id_get_or_create(self, name):
        return self.field_get_or_create(
            'account.payment.mode', name, 'name', False)

    def supplier_payment_mode_id_get_or_create(self, name):
        return self.field_get_or_create(
            'account.payment.mode', name, 'name', False)

    def property_product_pricelist_get_or_create(self, name):
        return self.field_get_or_create(
            'product.pricelist', name, 'name', False)

    def supplier_pricelist_id_get_or_create(self, name):
        return self.field_get_or_create(
            'product.pricelist.purchase', name, 'name', False)

    def property_account_position_id_get_or_create(self, name):
        return self.field_get_or_create(
            'account.fiscal.position', name, 'name', False)

    def credit_policy_id_get_or_create(self, name):
        return self.field_get_or_create(
            'credit.control.policy', name, 'name', False)

    def payment_responsible_id_get_or_create(self, name):
        return self.field_get_or_create('res.users', name, 'name', False)

    def category_line_get(self, df, row):
        errors = []
        cols = [c for c in df.columns if c.startswith('category_id:')]
        if not cols:
            return None, None
        if len(cols) > 1:
            errors.append(_(
                'More than one column found with name \'category_id:\'; there '
                'should be only one.'))
            return None, errors
        if not row[cols[0]]:
            return None, errors
        res = []
        name_categs = [v.strip() for v in row[cols[0]].split(';')]
        for name_categ in name_categs:
            categs = self.env['res.partner.category'].search([
                ('name', '=', name_categ),
            ])
            if categs:
                res.append(categs[0].id)
            else:
                errors.append(_(
                    'Partner category (tag) %s not found.') % name_categ)
        return res, errors

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
            error_msg = _(
                'Option \'%s\' for \'%s\' does not exist. You must '
                'choose a valid value.' % (data[field], field))
            if field == 'name':
                if data[field] == '':
                    required_fields.append('name')
            elif field == 'company_type':
                if data[field] is False:
                    required_fields.append('company_type')
                    errors.append(error_msg)
                if data[field] == 'company':
                    required_fields.append('vat')
                else:
                    continue
            elif field == 'agent':
                if data[field] is True:
                    required_fields.append('commission')
                    required_fields.append('agent_type')
                    required_fields.append('settlement')
                else:
                    continue
        errors += self.check_required_fields(required_fields, data)
        return errors

    def get_default_values(self, data, fields):
        partner_obj = self.env['res.partner']
        for field in fields:
            if data[field] is None:
                data[field] = partner_obj._fields[field].default(self)
        return data

    def import_file(self, simulation=True):
        def _add_errors(errors):
            for error in errors:
                if error != [] and error[1] != [] and error[1] != [[]]:
                    wizard.error(error[0], error[1][0])

        wizard = self._context.get('wizard')
        wizard.line_ids.unlink()
        df = wizard.dataframe_get()
        wizard.dataframe_required_columns(df, ['company_type', 'name'])
        wizard.total_rows = len(df)
        partner_obj = self.env['res.partner']
        all_errors = []
        orm_errors = False
        for index, row in df.iterrows():
            wizard.savepoint('import_template_partner')
            row_index = index + 2
            wizard.step(index + 1, 'Import "%s".' % row['name'])
            data, errors = wizard.get_data_row(self, 'res.partner', df, row)
            for error in errors:
                all_errors.append((row_index, [error]))
            data = self.get_default_values(data, ['agent_type', 'settlement'])
            data, errors = wizard.parser('res.partner', data)
            for error in errors:
                all_errors.append((row_index, [error]))
            errors = self.check_relational_fields(
                ['name', 'company_type'], data)
            for error in errors:
                all_errors.append((row_index, [error]))
            category_lines, errors = self.category_line_get(df, row)
            for error in errors:
                all_errors.append((row_index, [error]))
            if simulation:
                wizard.rollback('import_template_partner')
                continue
            data['category_id'] = (
                category_lines
                and [(6, 0, [categ for categ in category_lines])] or None)
            row_error = any([
                e for e in all_errors if e[0] == row_index and e[1] != []
                and e[1] != [[]]])
            if row_error:
                wizard.rollback('import_template_partner')
                continue
            partners = partner_obj.search([
                ('name', '=', data['name']),
                ('parent_id', '=', data['parent_id']),
            ])
            try:
                if partners:
                    partners.write(data)
                    partners._onchange_zip_id()
                else:
                    partners = partners.create(data)
                    partners._onchange_zip_id()
                wizard.release('import_template_partner')
            except Exception as e:
                orm_errors = True
                all_errors.append((row_index, [e]))
                wizard.rollback('import_template_partner')
        _add_errors(all_errors)
        return not orm_errors
