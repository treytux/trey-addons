###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import ast

from odoo import api, models


class SpreadsheetEnv(models.Model):
    _name = 'spreadsheet.env'
    _description = 'Spreadsheet Environment Functions'

    @api.model
    def _parse_domain(self, domain_str):
        if not domain_str:
            return []
        if isinstance(domain_str, list):
            return domain_str
        try:
            domain = ast.literal_eval(domain_str)
            if isinstance(domain, list):
                return domain
        except (ValueError, SyntaxError):
            pass
        return []

    @api.model
    def _validate_model_field(self, model_name, field_name):
        if model_name not in self.env:
            return False, 'Model %s not found' % model_name
        model = self.env[model_name]
        if field_name not in model._fields:
            return (
                False,
                'Field %s not found in model %s' % (field_name, model_name)
            )
        field = model._fields[field_name]
        if field.type not in ('integer', 'float', 'monetary'):
            return (
                False, 'Field %s is not a numeric field' % field_name
            )
        return True, None

    @api.model
    def _aggregate_field(self, func, alias, model_name, field_name,
                         domain_str='[]'):
        valid, error = self._validate_model_field(model_name, field_name)
        if not valid:
            return {'value': 0, 'error': error}
        domain = self._parse_domain(domain_str)
        try:
            Model = self.env[model_name].sudo()
            query = Model._search(domain)
            query.order = None
            query_str, params = query.select(
                '%s(%s) AS %s' % (func, field_name, alias))
            self.env.cr.execute(query_str, params)
            result = self.env.cr.dictfetchone()
            return {'value': result[alias] or 0, 'error': None}
        except Exception as e:
            return {'value': 0, 'error': str(e)}

    @api.model
    def spreadsheet_env_sum(self, args_list):
        return [
            self._aggregate_field(
                'SUM', 'total', args[0], args[1],
                args[2] if len(args) > 2 else '[]',
            )
            for args in args_list
        ]

    @api.model
    def spreadsheet_env_avg(self, args_list):
        return [
            self._aggregate_field(
                'AVG', 'average', args[0], args[1],
                args[2] if len(args) > 2 else '[]',
            )
            for args in args_list
        ]

    @api.model
    def spreadsheet_env_count(self, args_list):
        results = []
        for args in args_list:
            model_name = args[0]
            domain_str = args[1] if len(args) > 1 else '[]'
            if model_name not in self.env:
                results.append({
                    'value': 0,
                    'error': 'Model %s not found' % model_name,
                })
                continue
            domain = self._parse_domain(domain_str)
            try:
                count = self.env[model_name].sudo().search_count(domain)
                results.append({'value': count, 'error': None})
            except Exception as e:
                results.append({'value': 0, 'error': str(e)})
        return results

    @api.model
    def spreadsheet_env_min(self, args_list):
        return [
            self._aggregate_field(
                'MIN', 'minimum', args[0], args[1],
                args[2] if len(args) > 2 else '[]',
            )
            for args in args_list
        ]

    @api.model
    def spreadsheet_env_max(self, args_list):
        return [
            self._aggregate_field(
                'MAX', 'maximum', args[0], args[1],
                args[2] if len(args) > 2 else '[]',
            )
            for args in args_list
        ]
