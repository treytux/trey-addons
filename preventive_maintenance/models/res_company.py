###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import datetime
import json
import logging
import os
from inspect import signature

from odoo import api, fields, models
from odoo.addons.preventive_maintenance import slow_query_logger

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model
    def run_cron_history(self, days, max_records):
        if not isinstance(days, int) or days <= 0:
            raise ValueError('days must be a positive integer.')
        if not isinstance(max_records, int) or max_records <= 0:
            raise ValueError('max_records must be a positive integer.')
        History = self.env['preventive.maintenance.cron.history'].sudo()
        cutoff = fields.Datetime.now() - datetime.timedelta(days=days)
        rows = History.search([
            ('date_start', '>=', cutoff),
        ], order='date_start desc, id desc', limit=max_records)
        by_state = {}
        by_cron = {}
        executions = []
        for row in rows:
            by_state[row.state] = by_state.get(row.state, 0) + 1
            cron_name = row.cron_id.name or str(row.cron_id.id)
            cron_data = by_cron.setdefault(cron_name, {
                'executions': 0,
                'failed': 0,
                'duration_sec': 0.0,
            })
            cron_data['executions'] += 1
            cron_data['duration_sec'] += row.duration_sec or 0.0
            if row.state == 'failed':
                cron_data['failed'] += 1
            executions.append({
                'id': row.id,
                'cron_id': row.cron_id.id,
                'cron_name': cron_name,
                'server': row.server_name,
                'started': fields.Datetime.to_string(row.date_start),
                'ended': fields.Datetime.to_string(row.date_end)
                if row.date_end else None,
                'duration_sec': row.duration_sec,
                'state': row.state,
                'error_traceback': row.error_traceback
                if row.state == 'failed' else None,
            })
        report = {
            'model': 'preventive.maintenance.cron.history',
            'generated_at': datetime.datetime.utcnow().isoformat() + 'Z',
            'period_days': days,
            'cutoff': fields.Datetime.to_string(cutoff),
            'max_records': max_records,
            'truncated': len(rows) == max_records,
            'read_only': True,
            'summary': {
                'executions_returned': len(rows),
                'by_state': by_state,
                'failed_executions': by_state.get('failed', 0),
                'by_cron': by_cron,
            },
            'executions': executions,
        }
        log = self._log_cron_history(report, rows.ids, days)
        report['log_id'] = log.id
        return report

    @api.model
    def run_cron_analysis(self, days, max_records):
        return self.run_cron_history(days=days, max_records=max_records)

    @api.model
    def run_slow_query_history(self, days, max_records):
        if not isinstance(days, int) or days <= 0:
            raise ValueError('days must be a positive integer.')
        if not isinstance(max_records, int) or max_records <= 0:
            raise ValueError('max_records must be a positive integer.')
        slow_query_logger.flush_pending()
        History = self.env['preventive.maintenance.slow.query.history'].sudo()
        cutoff = fields.Datetime.now() - datetime.timedelta(days=days)
        rows = History.search([
            ('date_last', '>=', cutoff),
        ], order='max_duration_ms desc, date_last desc, id desc',
            limit=max_records)
        by_query = {}
        dropped_events = 0
        buckets = []
        for row in rows:
            if row.is_overflow:
                dropped_events += row.occurrence_count
                continue
            query = by_query.setdefault(row.query_id, {
                'query_id': row.query_id,
                'occurrences': 0,
                'total_duration_ms': 0.0,
                'min_duration_ms': row.min_duration_ms,
                'max_duration_ms': row.max_duration_ms,
                'first_seen': fields.Datetime.to_string(row.date_first),
                'last_seen': fields.Datetime.to_string(row.date_last),
                'servers': set(),
            })
            query['occurrences'] += row.occurrence_count
            query['total_duration_ms'] += row.total_duration_ms
            query['min_duration_ms'] = min(
                query['min_duration_ms'], row.min_duration_ms)
            query['max_duration_ms'] = max(
                query['max_duration_ms'], row.max_duration_ms)
            query['first_seen'] = min(
                query['first_seen'], fields.Datetime.to_string(row.date_first))
            query['last_seen'] = max(
                query['last_seen'], fields.Datetime.to_string(row.date_last))
            query['servers'].add(row.server_name)
            buckets.append({
                'id': row.id,
                'query_id': row.query_id,
                'bucket_start': fields.Datetime.to_string(row.bucket_start),
                'first_seen': fields.Datetime.to_string(row.date_first),
                'last_seen': fields.Datetime.to_string(row.date_last),
                'occurrences': row.occurrence_count,
                'min_duration_ms': row.min_duration_ms,
                'max_duration_ms': row.max_duration_ms,
                'total_duration_ms': row.total_duration_ms,
                'server': row.server_name,
            })
        queries = []
        for query in by_query.values():
            query['mean_duration_ms'] = (
                query['total_duration_ms'] / query['occurrences'])
            query['servers'] = sorted(query['servers'])
            queries.append(query)
        queries.sort(key=lambda item: item['total_duration_ms'], reverse=True)
        report = {
            'model': 'preventive.maintenance.slow.query.history',
            'generated_at': datetime.datetime.utcnow().isoformat() + 'Z',
            'period_days': days,
            'cutoff': fields.Datetime.to_string(cutoff),
            'max_records': max_records,
            'truncated': len(rows) == max_records,
            'read_only': True,
            'query_text_stored': False,
            'summary': {
                'buckets_returned': len(buckets),
                'query_ids_returned': len(queries),
                'occurrences_returned': sum(
                    query['occurrences'] for query in queries),
                'dropped_events_returned': dropped_events,
            },
            'queries': queries,
            'buckets': buckets,
        }
        log = self._log_slow_query_history(report, rows.ids, days)
        report['log_id'] = log.id
        return report

    @api.model
    def run_slow_query_analysis(self, days, max_records):
        return self.run_slow_query_history(days=days, max_records=max_records)

    def _log_slow_query_history(self, report, history_ids, days):
        Log = self.env['ir.model.log'].sudo()
        log = Log.create({
            'name': 'Slow query history (last %s days)' % days,
            'res_model': 'preventive.maintenance.slow.query.history',
            'res_ids': str(history_ids),
            'is_preventive_maintenance': True,
            'type': 'slow_query_history',
        })
        try:
            log.attach(
                'slow_query_history.json',
                json.dumps(report, ensure_ascii=False, indent=2, default=str),
                'application/json')
            log.finish('Slow query history analysis completed successfully')
        except Exception as exc:
            log.exception('Slow query history analysis export failed', exc)
            log.finish('Slow query history analysis completed with errors')
        return log

    @api.model
    def cleanup_slow_query_history(self, retention_days, batch_size):
        return self.env['preventive.maintenance.slow.query.history'].cleanup(
            retention_days=retention_days, batch_size=batch_size)

    def _log_cron_history(self, report, history_ids, days):
        Log = self.env['ir.model.log'].sudo()
        log = Log.create({
            'name': 'Cron history analysis (last %s days)' % days,
            'res_model': 'preventive.maintenance.cron.history',
            'res_ids': str(history_ids),
            'is_preventive_maintenance': True,
            'type': 'cron_history',
        })
        try:
            log.attach(
                'cron_history_analysis.json',
                json.dumps(report, ensure_ascii=False, indent=2, default=str),
                'application/json')
            log.finish('Cron history analysis completed successfully')
        except Exception as exc:
            log.exception('Cron history analysis export failed', exc)
            log.finish('Cron history analysis completed with errors')
        return log

    @api.model
    def run_records_integrity(
        self, *, companies, max_groups, max_ids_per_group,
            fuzzy_name_threshold):
        database_scope = False
        companies = self._preventive_maintenance_companies(companies)
        config = {
            'max_groups': max_groups,
            'max_ids_per_group': max_ids_per_group,
            'fuzzy_name_threshold': fuzzy_name_threshold,
        }
        self._validate_config(config)
        return self._run_report(
            '_run_audit', companies, config, database_scope,
            report_type='records_integrity')

    @api.model
    def run_storage_usage(
        self, *, companies, inactive_limit, large_attachment_limit,
            max_size_tables, max_growth_tables, growth_period):
        database_scope = False
        companies = self._preventive_maintenance_companies(companies)
        config = {
            'inactive_limit': inactive_limit,
            'large_attachment_limit': large_attachment_limit,
            'max_size_tables': max_size_tables,
            'max_growth_tables': max_growth_tables,
            'growth_period': growth_period,
        }
        self._validate_config(config)
        return self._run_report(
            '_storage_run_report', companies, config, database_scope,
            report_type='storage')

    @api.model
    def run_tables_by_size(self, *, companies, max_size_tables):
        database_scope = False
        companies = self._preventive_maintenance_companies(companies)
        config = {'max_size_tables': max_size_tables}
        self._validate_config(config)
        return self._run_report(
            '_tables_by_size_report', companies, config, database_scope,
            report_type='storage')

    @api.model
    def run_tables_by_growth(
            self, *, companies, max_growth_tables, growth_period):
        companies = self._preventive_maintenance_companies(companies)
        config = {
            'max_growth_tables': max_growth_tables,
            'growth_period': growth_period,
        }
        self._validate_config(config)
        return self._run_report(
            '_tables_by_growth_report', companies, config, False,
            report_type='storage')

    @api.model
    def run_inactive_models(self, *, companies, inactive_limit):
        companies = self._preventive_maintenance_companies(companies)
        config = {'inactive_limit': inactive_limit}
        self._validate_config(config)
        return self._run_report(
            '_inactive_models_report', companies, config, False,
            report_type='storage')

    @api.model
    def run_large_attachments(self, *, companies, large_attachment_limit):
        companies = self._preventive_maintenance_companies(companies)
        config = {'large_attachment_limit': large_attachment_limit}
        self._validate_config(config)
        return self._run_report(
            '_large_attachments_report', companies, config, False,
            report_type='storage')

    @api.model
    def run_disconnected_attachments(self, *, companies):
        companies = self._preventive_maintenance_companies(companies)
        config = {}
        return self._run_report(
            '_disconnected_attachments_report', companies, config, False,
            report_type='storage')

    @api.model
    def _validate_config(self, config):
        if any(value is None for value in config.values()):
            raise ValueError(
                'All maintenance configuration values are required.')
        if any(
            not isinstance(value, int) or value <= 0
            for name, value in config.items()
                if name != 'fuzzy_name_threshold'):
            raise ValueError(
                'Count, limit and period values must be positive integers.')
        threshold = config.get('fuzzy_name_threshold')
        if threshold is not None and not 0 <= threshold <= 1:
            raise ValueError('fuzzy_name_threshold must be between 0 and 1.')

    @api.model
    def _preventive_maintenance_companies(self, companies=None):
        if companies is None:
            return self
        if not hasattr(companies, 'ids'):
            raise TypeError('companies must be a res.company recordset.')
        requested_ids = set(companies.ids)
        companies = companies.exists()
        if set(companies.ids) != requested_ids:
            raise ValueError('One or more requested companies do not exist.')
        return companies

    def _run_report(
            self, function_name, companies, config, database_scope=False,
            report_type='other'):
        scopes = (
            [self.browse()] if database_scope else list(companies)
            + [self.browse()])
        results = []
        for company in scopes:
            report_env = self.env
            if not company and not database_scope:
                report_env = self.with_context(
                    preventive_maintenance_shared_only=True).env
            scoped_self = self.with_context(
                preventive_maintenance_config=config)
            result = getattr(scoped_self, function_name)(
                report_env, companies=company)
            results.append(self._log_maintenance_result(
                company, result, report_type=report_type))
        return results

    def _log_maintenance_result(self, company, result, report_type='other'):
        Log = self.env['ir.model.log'].sudo()
        name = 'Maintenance report' + ((
            ' for %s' % company.name) if company else '')
        log = Log.create({
            'name': name,
            'res_model': 'res.company' if company else False,
            'res_ids': str(company.ids) if company else '[]',
            'is_preventive_maintenance': True,
            'type': report_type,
        })
        try:
            log.attach(
                'maintenance_report.json',
                json.dumps(result, ensure_ascii=False, indent=2, default=str),
                'application/json')
            log.finish('Maintenance report completed successfully')
        except Exception as exc:
            log.exception('Maintenance report export failed', exc)
            log.finish('Maintenance report completed with errors')
        return result

    def _config(self):
        config = self.env.context.get('preventive_maintenance_config')
        if not config:
            raise ValueError('Maintenance configuration was not provided.')
        return config

    def _field(self, model, name):
        return model._fields.get(name)

    def _audit_company(self, env):
        company_id = env.context.get('preventive_maintenance_company_id')
        if not company_id:
            return None
        return env['res.company'].browse(company_id).exists()

    def _shared_only(self, env):
        return bool(env.context.get('preventive_maintenance_shared_only'))

    def _company_domain(self, model):
        company = self._audit_company(model.env)
        if self._shared_only(model.env) and self._field(model, 'company_id'):
            return [('company_id', '=', False)]
        if not company or not self._field(model, 'company_id'):
            return []
        return [
            '|', ('company_id', '=', False), ('company_id', '=', company.id)]

    def _company_sql_scope(self, env, model_name, alias=''):
        company = self._audit_company(env)
        model = self._model(env, model_name)
        if model is None or not self._field(model, 'company_id'):
            return '', ()
        if self._shared_only(env):
            prefix = '%s.' % alias if alias else ''
            return ' AND %scompany_id IS NULL' % prefix, ()
        if not company:
            return '', ()
        prefix = '%s.' % alias if alias else ''
        return (
            ' AND (%scompany_id IS NULL OR %scompany_id = %%s)'
            % (prefix, prefix), (company.id,))

    def _active(self, model):
        return self._company_domain(model) + ([
            ('active', '=', True),
        ] if self._field(model, 'active') else [])

    def _add(
            self, report, check, severity, model, message, ids=None, **values):
        row = {
            'check': check,
            'severity': severity,
            'model': model,
            'message': message,
        }
        if ids:
            row['record_ids'] = ids[: self._config()['max_ids_per_group']]
            row['record_count'] = len(ids)
            row['record_ids_truncated'] = len(ids) > self._config()[
                'max_ids_per_group']
        row.update(values)
        report.append(row)

    def _sql(self, env, query, params=()):
        env.cr.execute(query, params)
        return env.cr.dictfetchall()

    def _warning(self, report, check, model, message, **values):
        self._add(report, check, 'warning', model, message, **values)

    def _model(self, env, model_name):
        try:
            return env[model_name].sudo()
        except KeyError:
            return None

    def _missing_active_models(self, env, model_names):
        missing = []
        for model_name in model_names:
            model = self._model(env, model_name)
            if model is not None and not self._field(model, 'active'):
                missing.append(model_name)
        return missing

    def _add_query_issue(
        self, env, report, query, params, check, severity, model, message,
            **values):
        scope, scope_params = self._company_sql_scope(env, model)
        scope_join = ''
        scoped_matches = 'matches'
        if scope:
            scope_join = '''
            , scoped_matches AS (
                SELECT matches.id
                FROM matches
                JOIN %s AS scoped_record ON scoped_record.id = matches.id
                WHERE TRUE %s
            )
            ''' % (
                self._model(env, model)._table,
                scope.replace('company_id', 'scoped_record.company_id'),
            )
            scoped_matches = 'scoped_matches'
        aggregate = (
            '''
            WITH matches AS (
                SELECT DISTINCT id
                FROM (
            '''
            + query
            + '''
                ) raw
            )
            '''
            + scope_join
            + '''
            , sample AS (
                SELECT id
                FROM '''
            + scoped_matches
            + '''
                ORDER BY id
                LIMIT %s
            )
            SELECT count(*) AS total_count,
                COALESCE(
                    (SELECT array_agg(id) FROM sample),
                    ARRAY[]::integer[]
                ) AS ids
            FROM '''
            + scoped_matches
            + '''
            '''
        )
        rows = self._sql(
            env, aggregate, tuple(params) + scope_params
            + (self._config()['max_ids_per_group'],))
        if not rows or not rows[0]['total_count']:
            return
        self._add(
            report, check, severity, model, message, rows[0]['ids'],
            record_count=rows[0]['total_count'], **values)

    def _duplicates(self, model, fields, report, check, message):
        fields = [
            name
            for name in fields
            if self._field(model, name) and self._field(model, name).store
        ]
        if not fields:
            return
        domain = self._active(model) + [(name, '!=', False) for name in fields]
        kwargs = {
            'fields': fields + ['id:count'],
            'groupby': fields,
            'lazy': False,
            'limit': self._config()['max_groups'],
        }
        try:
            if 'having' in signature(model.read_group).parameters:
                kwargs['having'] = [('__count', '>', 1)]
            groups = model.read_group(domain, **kwargs)
        except TypeError:
            kwargs.pop('having', None)
            groups = model.read_group(domain, **kwargs)
        for group in groups:
            count = group.get('__count', group.get('id_count', 0))
            if count < 2:
                continue
            values = {}
            group_domain = list(self._active(model))
            for name in fields:
                value = group.get(name)
                values[name] = value[0] if isinstance(value, tuple) else value
                group_domain.append((name, '=', values[name]))
            ids = model.search(
                group_domain, order='id',
                limit=self._config()['max_ids_per_group'] + 1).ids
            self._add(
                report, check, 'high', model._name, message, ids,
                fields=fields, values=values, count=count)
            if len(report) >= self._config()['max_groups']:
                break

    def _partner_role_conditions(self, partner, alias='p'):
        return [
            '%s.%s > 0' % (alias, field_name)
            for field_name in ('customer_rank', 'supplier_rank')
            if (
                self._field(partner, field_name)
                and self._field(partner, field_name).store
            )
        ]

    def _contacts(self, env, report):
        partner = env['res.partner'].sudo()
        partner_scope, partner_scope_params = self._company_sql_scope(
            env, 'res.partner')
        for field, check, message in ((
                'email', 'contact.email_duplicate',
                'Active contacts share a normalized email.'),):
            for row in self._sql(
                env,
                '''
                SELECT
                    lower(regexp_replace(%s, '\\s+', ' ', 'g')) normalized,
                    array_agg(id ORDER BY id) ids,
                    count(*) count
                FROM res_partner
                WHERE
                    active IS TRUE
                    %s
                    AND %s IS NOT NULL
                    AND btrim(%s) <> ''
                GROUP BY normalized
                HAVING count(*) > 1
                ORDER BY count(*) DESC
                LIMIT %%s
                    '''
                % (field, partner_scope, field, field),
                    partner_scope_params + (self._config()['max_groups'],)):
                self._add(
                    report, check,
                    'high' if field == 'email' else 'medium', 'res.partner',
                    message, row['ids'], normalized=row['normalized'],
                    count=row['count'])
        for row in self._sql(
            env,
            '''
            SELECT
                lower(regexp_replace(name, '\\s+', ' ', 'g')) normalized,
                parent_id,
                array_agg(id ORDER BY id) ids,
                count(*) count
            FROM res_partner
            WHERE
                active IS TRUE
                %s
                AND name IS NOT NULL
                AND btrim(name) <> ''
            GROUP BY normalized, parent_id
            HAVING count(*) > 1
            ORDER BY count(*) DESC
            LIMIT %%s
                ''' % partner_scope,
                partner_scope_params + (self._config()['max_groups'],)):
            self._add(
                report, 'contact.name_duplicate', 'medium', 'res.partner',
                'Active contacts share a normalized name under the same '
                'parent.', row['ids'], normalized=row['normalized'],
                parent_id=row['parent_id'], count=row['count'])
        for row in self._sql(
            env,
            '''
            SELECT
                regexp_replace(p.phone, '[^0-9+]', '', 'g') AS normalized_phone,
                array_agg(id ORDER BY id) AS ids,
                count(*) AS count
            FROM res_partner p
            WHERE
                p.active IS TRUE
                %s
                AND p.phone IS NOT NULL
                AND btrim(p.phone) <> ''
                AND NOT EXISTS (
                    SELECT 1
                    FROM res_partner parent
                    WHERE parent.id = p.parent_id
                        AND regexp_replace(parent.phone, '[^0-9+]', '', 'g')
                            = regexp_replace(p.phone, '[^0-9+]', '', 'g')
                )
            GROUP BY normalized_phone
            HAVING count(*) > 1
            ORDER BY count(*) DESC
            LIMIT %%s
                '''
            % partner_scope,
                partner_scope_params + (self._config()['max_groups'],)):
            self._add(
                report, 'contact.phone_duplicate', 'medium', 'res.partner',
                'Active contacts share a normalized phone.', row['ids'],
                normalized_phone=row['normalized_phone'], count=row['count'])
        self._add_query_issue(
            env, report,
            '''
            SELECT id
            FROM res_partner
            WHERE
                active IS TRUE
                AND type = 'contact'
                AND (name IS NULL OR btrim(name) = '')
            ''',
            (),
            'contact.name_missing',
            'high',
            'res.partner',
            'Active contact has no name.')
        roles = self._partner_role_conditions(partner)
        if roles and all(
            self._field(partner, x) for x in ('parent_id', 'vat', 'email')
        ):
            self._add_query_issue(
                env, report,
                '''
                SELECT p.id
                FROM res_partner p
                JOIN
                    res_partner parent
                    ON parent.id = p.parent_id
                WHERE
                    p.active IS TRUE
                    AND parent.active IS TRUE
                    AND btrim(COALESCE(parent.vat, '')) <> ''
                    AND (%s)
                    AND btrim(COALESCE(p.email, '')) = ''
                '''
                % ' OR '.join(roles),
                (),
                'contact.child_email_missing',
                'medium',
                'res.partner',
                'Customer/supplier child has no email while parent has VAT.')
        self._add_query_issue(
            env, report,
            '''
            SELECT p.id
            FROM res_partner p
            JOIN
                res_partner parent
                ON parent.id = p.parent_id
            WHERE
                p.active IS TRUE
                AND parent.active IS TRUE
                AND p.company_id IS DISTINCT FROM parent.company_id
            ''',
            (),
            'contact.parent_company_mismatch',
            'high',
            'res.partner',
            'Contact company differs from its parent company.')
        if roles and self._field(partner, 'vat') and self._field(
                partner, 'country_id'):
            self._add_query_issue(
                env, report,
                '''
                SELECT p.id
                FROM res_partner p
                WHERE
                    p.active IS TRUE
                    AND ({})
                    AND btrim(COALESCE(p.vat, '')) <> ''
                    AND p.country_id IS NULL
                '''.format(
                    ' OR '.join(roles)
                ),
                (),
                'contact.fiscal_country_missing',
                'medium',
                'res.partner',
                'Customer/supplier with VAT has no fiscal country.')
        elif not roles:
            self._warning(
                report, 'contact.role_fields_unavailable', 'res.partner',
                'Customer/supplier role fields are unavailable; '
                'role-dependent contact checks were skipped.')

        if not self._sql(
                env, "SELECT 1 FROM pg_extension WHERE extname='pg_trgm'"):
            self._add(
                report, 'contact.fuzzy_name_unavailable', 'warning',
                'res.partner',
                'pg_trgm is not installed; fuzzy matching was not run.')
            return
        a_scope, a_scope_params = self._company_sql_scope(
            env, 'res.partner', 'a')
        b_scope, b_scope_params = self._company_sql_scope(
            env, 'res.partner', 'b')
        for row in self._sql(
            env,
            '''
            SELECT
                a.id left_id,
                b.id right_id,
                similarity(
                    lower(regexp_replace(a.name, '\\s+', ' ', 'g')),
                    lower(regexp_replace(b.name, '\\s+', ' ', 'g'))
                ) score
            FROM
                res_partner a
                JOIN res_partner b ON b.id > a.id
            WHERE
                a.active IS TRUE
                AND b.active IS TRUE
                {a_scope}
                {b_scope}
                AND a.name IS NOT NULL
                AND b.name IS NOT NULL
                AND a.parent_id IS NOT DISTINCT FROM b.parent_id
                AND lower(regexp_replace(a.name, '\\s+', ' ', 'g')) %%
                    lower(regexp_replace(b.name, '\\s+', ' ', 'g'))
                AND similarity(lower(regexp_replace(a.name, '\\s+', ' ', 'g')),
                    lower(regexp_replace(b.name, '\\s+', ' ', 'g'))) >= %s
            ORDER BY score DESC LIMIT %s
            '''.format(
                a_scope=a_scope, b_scope=b_scope
            ), a_scope_params + b_scope_params
            + (self._config()['fuzzy_name_threshold'],
               self._config()['max_groups'])):
            self._add(
                report, 'contact.fuzzy_name_duplicate', 'medium',
                'res.partner',
                'Active contacts have highly similar normalized names.', [
                    row['left_id'],
                    row['right_id'],
                ],
                similarity=float(row['score']))

    def _products(self, env, report):
        template = env['product.template'].sudo()
        variant = env['product.product'].sudo()
        self._duplicates(
            template,
            ['name'],
            report,
            'product.name_duplicate',
            'Active product templates share a name.')
        code_fields = [
            x for x in ('default_code', 'internal_code', 'internal_reference')
            if self._field(template, x)
        ]
        for code_field in code_fields:
            self._duplicates(
                template, [code_field], report, 'product.reference_duplicate',
                'Active product templates share an internal reference.')
        self._duplicates(
            variant, ['default_code'], report, 'product.reference_duplicate',
            'Active variants share an internal reference.')
        fields = [
            x
            for x in ('name', 'categ_id', 'uom_id', 'uom_po_id', 'list_price')
            if self._field(template, x)
        ]
        clauses = [
            (
                "btrim(COALESCE(name->>'en_US', '')) = ''" if x == 'name'
                else '%s IS NULL' % x)
            for x in fields
        ]
        if clauses:
            self._add_query_issue(
                env, report,
                'SELECT id FROM product_template WHERE active IS TRUE AND (%s)'
                % ' OR '.join(clauses),
                (),
                'product.required_field_missing',
                'high',
                'product.template',
                'Active template lacks a key field.',
                fields=fields)
        company = self._audit_company(env)
        price_company_join = (
            'CROSS JOIN res_company company' if not company else '')
        price_company_condition = (
            'cost.company_id = company.id' if not company
            else 'cost.company_id = %s')
        price_params = () if not company else (company.id,)
        self._add_query_issue(
            env, report,
            '''
            SELECT p.id
            FROM product_product p
            JOIN
                product_template t
                ON t.id = p.product_tmpl_id
            %s
            WHERE
                p.active IS TRUE
                AND t.active IS TRUE
                AND NOT EXISTS (
                    SELECT 1
                    FROM ir_property cost
                    WHERE cost.name = 'standard_price'
                        AND cost.res_id = 'product.product,' || p.id::text
                        AND %s
                        AND cost.value_float IS NOT NULL
                )
                AND NOT EXISTS (
                    SELECT 1
                    FROM ir_property cost
                    WHERE cost.name = 'standard_price'
                        AND cost.res_id = 'product.product,' || p.id::text
                        AND cost.company_id IS NULL
                        AND cost.value_float IS NOT NULL
                )
            '''
            % (price_company_join, price_company_condition), price_params,
            'product.standard_price_missing',
            'high',
            'product.product',
            'Active variant has no company-dependent standard price.',
            fields=['standard_price'])
        self._add_query_issue(
            env, report,
            '''
            SELECT p.id
            FROM product_product p
            JOIN
                product_template t
                ON t.id = p.product_tmpl_id
            WHERE
                p.active IS TRUE
                AND t.active IS TRUE
                AND btrim(COALESCE(p.default_code, '')) = ''
                AND btrim(COALESCE(t.default_code, '')) = ''
            ''',
            (),
            'product.variant_reference_missing',
            'medium',
            'product.product',
            'Variant and parent template both have empty internal reference.')
        self._add_query_issue(
            env, report,
            '''
            SELECT p.id
            FROM product_product p
            JOIN
                product_template t
                ON t.id = p.product_tmpl_id
            WHERE
                p.active IS TRUE
                AND t.active IS TRUE
                AND btrim(COALESCE(p.default_code, '')) <> ''
                AND p.default_code = t.default_code
            ''',
            (),
            'product.variant_template_reference_collision',
            'high',
            'product.product',
            'Variant reference matches its parent template reference.')
        self._add_query_issue(
            env, report,
            '''
            SELECT p.id
            FROM product_product p
            JOIN
                product_template t
                ON t.id = p.product_tmpl_id
            WHERE
                p.active IS TRUE
                AND t.active IS TRUE
                AND btrim(COALESCE(p.default_code, '')) <> ''
                AND EXISTS (
                    SELECT 1
                    FROM product_product x
                    WHERE x.active IS TRUE
                        AND x.id <> p.id
                        AND x.default_code = p.default_code
                        AND x.product_tmpl_id <> p.product_tmpl_id
                )
            ''',
            (),
            'product.cross_template_reference_duplicate',
            'high',
            'product.product',
            'Variant reference is reused by another template.')
        for row in self._sql(
            env,
            '''
            WITH variant_attrs AS (
                SELECT
                    p.id,
                    p.product_tmpl_id,
                    COALESCE(
                        string_agg(av.id::text, ',' ORDER BY av.id), ''
                    ) AS attrs
                FROM product_product p
                LEFT JOIN product_variant_combination rel
                    ON rel.product_product_id = p.id
                LEFT JOIN product_template_attribute_value av
                    ON av.id = rel.product_template_attribute_value_id
                WHERE p.active IS TRUE
                GROUP BY p.id, p.product_tmpl_id
            )
            SELECT
                va.product_tmpl_id,
                va.attrs,
                array_agg(va.id ORDER BY va.id) ids,
                count(*) count
            FROM variant_attrs va
            JOIN
                product_template t
                ON t.id = va.product_tmpl_id
            WHERE t.active IS TRUE
            GROUP BY va.product_tmpl_id, va.attrs
            HAVING count(*) > 1
            LIMIT %s
                ''', (self._config()['max_groups'],)):
            self._add(
                report, 'product.variant_duplicate', 'high', 'product.product',
                'Variants share the same template and attribute values.',
                row['ids'], product_tmpl_id=row['product_tmpl_id'],
                attributes=row['attrs'], count=row['count'])

    def _relationships(self, env, report):
        self._add_query_issue(
            env, report,
            '''
            SELECT p.id
            FROM product_product p
            JOIN
                product_template t
                ON t.id = p.product_tmpl_id
            WHERE
                p.active IS TRUE
                AND t.active IS TRUE
                AND EXISTS (
                    SELECT 1
                    FROM stock_route_product pr
                    JOIN stock_route r
                        ON r.id = pr.route_id
                    WHERE pr.product_id = p.id
                        AND r.active IS TRUE
                        AND r.name->>'en_US' ILIKE %s
                )
                AND NOT EXISTS (
                    SELECT 1
                    FROM product_supplierinfo s
                    WHERE s.product_id = p.id
                        OR s.product_tmpl_id = p.product_tmpl_id
                )
            ''',
            ('%route_by%',),
            'product.route_without_supplier',
            'medium',
            'product.product',
            'Product route contains route_by but has no supplier.')
        self._add_query_issue(
            env, report,
            '''
            SELECT p.id
            FROM product_template p
            JOIN
                uom_uom sale
                ON sale.id = p.uom_id
            JOIN
                uom_uom purchase
                ON purchase.id = p.uom_po_id
            WHERE
                p.active IS TRUE
                AND sale.category_id <> purchase.category_id
            ''',
            (),
            'product.uom_category_mismatch',
            'high',
            'product.template',
            'Sales and purchase UoMs have different categories; '
            'no valid conversion exists.')
        self._add_query_issue(
            env, report,
            '''
            SELECT
                p.id, av.id value_id,
                a.id attribute_id
            FROM product_product p
            JOIN
                product_template t
                ON t.id = p.product_tmpl_id
            JOIN
                product_variant_combination rel
                ON rel.product_product_id = p.id
            JOIN
                product_template_attribute_value av
                ON av.id = rel.product_template_attribute_value_id
            JOIN
                product_attribute a
                ON a.id = av.attribute_id
            WHERE
                p.active IS TRUE
                AND t.active IS TRUE
                AND NOT EXISTS (
                    SELECT 1
                    FROM product_template_attribute_line l
                    WHERE l.product_tmpl_id = t.id
                        AND l.attribute_id = a.id
                )
            ''',
            (),
            'product.variant_attribute_integrity',
            'high',
            'product.product',
            'Variant attribute is not declared on its parent template.')

    def _supplier_dates(self, env, report):
        self._add_query_issue(
            env, report,
            '''
            SELECT id
            FROM product_supplierinfo
            WHERE date_start IS NOT NULL
                AND date_end IS NOT NULL
                AND date_end < date_start
            ''',
            (),
            'product.supplier_dates_invalid',
            'medium',
            'product.supplierinfo',
            'Supplier information has an end date before its start date.')

    def _run_check(self, env, report, check_name, function, model_names):
        missing_models = [
            name for name in model_names if self._model(env, name) is None]
        if missing_models:
            self._warning(
                report, 'audit.capability', ','.join(missing_models),
                'Check skipped because required model(s) are not installed.',
                audit_check=check_name, missing_models=missing_models)
            return
        missing_active = self._missing_active_models(env, model_names)
        if missing_active:
            self._warning(
                report, 'audit.active_field_missing', ','.join(missing_active),
                'Check skipped because archived-record filtering cannot be '
                'guaranteed.', audit_check=check_name,
                missing_active_fields=missing_active)
            return
        try:
            with env.cr.savepoint():
                function(env, report)
        except Exception as error:
            _logger.exception('Integrity check %s failed', check_name)
            self._warning(
                report, 'audit.check_failed', 'audit',
                'Check failed and was skipped; remaining checks continued.',
                audit_check=check_name, error_type=type(error).__name__,
                error=str(error))

    def _run_audit(self, env, company=None, companies=None):
        company = companies if companies is not None else company
        if company and len(company) != 1:
            raise ValueError('run_audit expects one company per scope.')
        if company:
            env = (
                env['res.company']
                .with_context(preventive_maintenance_company_id=company.id)
                .env)
        report = []
        checks = (
            ('contacts', self._contacts, ('res.partner',)),
            ('products', self._products, (
                'product.template', 'product.product')),
            ('relationships', self._relationships, (
                'product.product', 'product.template', 'uom.uom',
                'stock.route'),),
            ('supplier_dates', self._supplier_dates, ('product.supplierinfo',)),
        )
        for check_name, function, model_names in checks:
            self._run_check(env, report, check_name, function, model_names)
        severities = {}
        for row in report:
            severities[row['severity']] = severities.get(
                row['severity'], 0) + 1
        duplicate_reports = {
            'contacts': [
                row for row in report
                if row['check'].startswith('contact.')
                and 'duplicate' in row['check']],
            'products': [
                row for row in report
                if row['check'].startswith('product.')
                and 'duplicate' in row['check']],
        }
        return {
            'model': 'record_report.check',
            'odoo_version': '16.0',
            'generated_at': datetime.datetime.utcnow().isoformat() + 'Z',
            'scope': {
                'type': 'company'
                if company
                else ('shared' if self._shared_only(env) else 'database'),
                'company_id': company.id if company else None,
                'company_name': company.name if company else None,
            },
            'read_only': True,
            'archived_records_excluded': True,
            'sample_size': self._config()['max_ids_per_group'],
            'summary': {
                'findings': len(report),
                'by_severity': severities,
            },
            'duplicate_reports': duplicate_reports,
            'checks': report,
        }

    def _inactive_models(self, env):
        result = []
        model_registry = env['ir.model'].sudo().search([], order='model')
        for model_record in model_registry:
            model = self._model(env, model_record.model)
            if (
                model is None
                or model._abstract
                or not model._auto
                or not self._field(model, 'active')
            ):
                continue
            try:
                with env.cr.savepoint():
                    inactive_count = model.search_count(
                        self._company_domain(model) + [
                            ('active', '=', False),
                        ])
                    if inactive_count < self._config()['inactive_limit']:
                        continue
                    result.append({
                        'model': model._name,
                        'inactive_count': inactive_count,
                    })
            except Exception:
                _logger.exception(
                    'Could not inspect inactive records in %s',
                    model_record.model)
        return result

    def _attachment_data(self, attachment, **values):
        data = {
            'id': attachment.id,
            'name': attachment.name,
            'file_size': attachment.file_size,
            'file_size_mb': self._size_mb(attachment.file_size),
            'res_model': attachment.res_model or None,
            'res_id': attachment.res_id or None,
        }
        data.update(values)
        return data

    def _attachment_file_exists(self, attachment):
        if attachment.type != 'binary' or not attachment.store_fname:
            return True
        try:
            return os.path.exists(
                attachment._full_path(attachment.store_fname))
        except (AttributeError, OSError):
            return True

    def _attachment_report(self, env, include_large):
        attachment_model = env['ir.attachment'].sudo()
        attachment_domain = self._company_domain(attachment_model)
        categories = {
            'duplicate_attachments': [],
            'large_attachments': [],
            'attachments_missing_model': [],
            'disconnected_attachments': [],
            'url_only_attachments': [],
            'attachments_with_broken_reference': [],
            'attachments_missing_file': [],
        }
        url_attachments = attachment_model.search(
            attachment_domain + [('type', '=', 'url'), ], order='id')
        categories['url_only_attachments'] = [
            self._attachment_data(attachment, url=attachment.url)
            for attachment in url_attachments
        ]
        if include_large:
            categories['large_attachments'] = [
                self._attachment_data(attachment)
                for attachment in attachment_model.search(
                    attachment_domain + [
                        ('type', '=', 'binary'),
                        ('file_size', '>=', (
                            self._config()['large_attachment_limit'])),
                    ], order='id')]
        duplicate_groups = attachment_model.read_group(
            attachment_domain
            + [
                ('type', '=', 'binary'),
            ],
            ['name', 'res_model', 'res_id', 'id:count'],
            ['name', 'res_model', 'res_id'], lazy=False)
        for group in duplicate_groups:
            count = group.get('id_count', group.get('__count', 0))
            if count < 2:
                continue
            name = group.get('name')
            res_model = group.get('res_model')
            res_id = group.get('res_id')
            attachments = attachment_model.search(
                attachment_domain + [
                    ('type', '=', 'binary'),
                    ('name', '=', name),
                    ('res_model', '=', res_model),
                    ('res_id', '=', res_id),
                ],
                order='id')
            categories['duplicate_attachments'].append({
                'name': name,
                'res_model': res_model,
                'res_id': res_id,
                'count': count,
                'file_size': attachments[0].file_size
                if attachments else 0,
                'attachments': [
                    self._attachment_data(attachment)
                    for attachment in attachments],
            })
        registered_models = set(
            env['ir.model'].sudo().search([]).mapped('model'))
        rows = attachment_model.search(
            attachment_domain + [('type', '=', 'binary'), ], order='id')
        grouped = {}
        for attachment in rows:
            if not self._attachment_file_exists(attachment):
                categories['attachments_missing_file'].append(
                    self._attachment_data(attachment, reason='file_not_found'))
            if not attachment.res_model and not attachment.res_id:
                categories['disconnected_attachments'].append(
                    self._attachment_data(attachment))
                continue
            if attachment.res_model not in registered_models:
                categories['attachments_missing_model'].append(
                    self._attachment_data(attachment))
                continue
            if not attachment.res_id:
                categories['attachments_with_broken_reference'].append(
                    self._attachment_data(attachment, reason='missing_res_id'))
                continue
            grouped.setdefault(attachment.res_model, []).append(attachment)
        for model_name, attachments in grouped.items():
            try:
                with env.cr.savepoint():
                    target = self._model(env, model_name)
                    if target is None:
                        raise ValueError(
                            'model is not available in the registry')
                    existing_ids = set(
                        target.browse(
                            [attachment.res_id for attachment in attachments]
                        ).exists().ids)
            except Exception:
                _logger.exception(
                    'Could not validate attachment references in %s',
                    model_name)
                continue
            categories['attachments_with_broken_reference'].extend(
                self._attachment_data(attachment, reason='record_not_found')
                for attachment in attachments
                if attachment.res_id not in existing_ids)
        return categories

    def _table_catalog(self, env):
        env.cr.execute(
            '''
            SELECT
                namespace.nspname AS schema_name,
                relation.relname AS table_name,
                relation.oid,
                pg_total_relation_size(relation.oid) AS size_bytes,
                pg_total_relation_size(relation.oid)
                    - pg_relation_size(relation.oid)
                    AS external_size_bytes,
                EXISTS (
                    SELECT 1 FROM pg_attribute a
                    WHERE a.attrelid = relation.oid
                        AND a.attname = 'company_id'
                        AND a.attnum > 0
                        AND NOT a.attisdropped
                ) AS has_company,
                EXISTS (
                    SELECT 1 FROM pg_attribute a
                    WHERE a.attrelid = relation.oid
                        AND a.attname = 'create_date'
                        AND a.attnum > 0 AND NOT a.attisdropped
                        AND a.atttypid IN (
                            'date'::regtype, 'timestamp'::regtype,
                            'timestamptz'::regtype)
                ) AS has_create_date,
                format('%I.%I', namespace.nspname, relation.relname)
            FROM pg_catalog.pg_class relation
            JOIN pg_catalog.pg_namespace namespace
              ON namespace.oid = relation.relnamespace
            WHERE relation.relkind = 'r'
              AND namespace.nspname NOT IN ('pg_catalog', 'information_schema')
        ''')
        return [
            dict(zip((
                'schema_name', 'table_name', 'oid', 'size_bytes',
                'external_size_bytes', 'has_company', 'has_create_date',
                'qualified_table'), row)) for row in env.cr.fetchall()]

    def _table_size_report(self, env, tables, companies=None):
        if not companies and not self._shared_only(env):
            tables = sorted(
                tables, key=lambda row: (
                    -row['size_bytes'], row['table_name']))
            return [{
                'table': row['table_name'],
                'size_mb': self._size_mb(row['size_bytes']),
                'external_size_mb': self._size_mb(
                    row['external_size_bytes']),
                'size_bytes': row['size_bytes'],
                'external_size_bytes': row['external_size_bytes'],
            } for row in tables[: self._config()['max_size_tables']]]
        company_ids = (
            [company.id for company in companies] if companies else [])
        params = []
        parts = []
        for row in tables:
            if not row['has_company']:
                if self._shared_only(env):
                    parts.append('SELECT %s, %s, %s' % ('%s', '%s', '%s'))
                    params.extend([
                        row['table_name'],
                        row['size_bytes'],
                        row['external_size_bytes'],
                    ])
                continue
            if self._shared_only(env):
                parts.append(
                    '''SELECT %s, COALESCE(SUM(pg_column_size(t)), 0), 0
                    FROM %s t WHERE t.company_id IS NULL'''
                    % ('%s', row['qualified_table']))
                params.append(row['table_name'])
            else:
                parts.append(
                    '''SELECT %s, COALESCE(SUM(pg_column_size(t)), 0), 0
                    FROM %s t WHERE t.company_id = %%s'''
                    % ('%s', row['qualified_table']))
                params.extend([row['table_name'], company_ids[0]])
        if not parts:
            return []
        env.cr.execute(' UNION ALL '.join(parts), tuple(params))
        result = [{
            'table': table,
            'size_mb': self._size_mb(size),
            'external_size_mb': self._size_mb(external),
            'size_bytes': size,
            'external_size_bytes': external,
        } for table, size, external in env.cr.fetchall()]
        return sorted(result, key=lambda row: (
            -row['size_bytes'], row['table']))[
                : self._config()['max_size_tables']]

    def _table_growth_report(self, env, tables, companies=None):
        tables = [row for row in tables if row['has_create_date']]
        if not tables:
            return []
        parts = []
        params = []
        for row in tables:
            company_filter = ''
            if companies and row['has_company']:
                company_filter = ' AND t.company_id = %s'
            elif self._shared_only(env) and row['has_company']:
                company_filter = ' AND t.company_id IS NULL'
            parts.append(
                '''SELECT %s, COUNT(*),
                COALESCE(SUM(pg_column_size(t)), 0), %s
                FROM %s t
                WHERE t.create_date >= NOW() - (%s * INTERVAL '1 month')%s'''
                % ('%s', '%s', row['qualified_table'], '%s', company_filter))
            params.extend([
                row['table_name'],
                row['size_bytes'],
                self._config()['growth_period'],
            ])
            if companies and row['has_company']:
                params.append(companies[0].id)
        try:
            try:
                with env.cr.savepoint():
                    env.cr.execute(' UNION ALL '.join(parts), tuple(params))
                    rows = env.cr.fetchall()
            except Exception:
                raise
        except Exception:
            _logger.exception('Could not calculate table growth')
            return []
        growth = [{
            'table': table,
            'records_added': count,
            'record_size_mb': self._size_mb(record_size),
            'table_size_mb': self._size_mb(table_size),
            'record_size_bytes': record_size,
            'table_size_bytes': table_size,
        } for table, count, record_size, table_size in rows]
        growth.sort(key=lambda row: (-row['records_added'], row['table']))
        return growth[: self._config()['max_growth_tables']]

    def _size_mb(self, size):
        return '%.2f MB' % (float(size or 0) / (1024 * 1024))

    def _storage_run_report(self, env, company=None, companies=None):
        company = companies if companies is not None else company
        if company and len(company) != 1:
            raise ValueError('run_report expects one company per scope.')
        if company:
            env = env['res.company'].with_context(
                preventive_maintenance_company_id=company.id).env
        tables = self._table_catalog(env)
        inactive_models = self._inactive_models(env)
        attachment_report = self._attachment_report(env, True)
        table_sizes = self._table_size_report(
            env, tables, companies=company if company else None)
        table_growth = self._table_growth_report(
            env, tables, companies=company if company else None)
        return {
            'generated_at': datetime.datetime.utcnow().isoformat() + 'Z',
            'scope': {
                'type': 'company'
                if company
                else ('shared' if self._shared_only(env) else 'database'),
                'company_id': company.id if company else None,
                'company_name': company.name if company else None,
                'database_metrics_included': (
                    not bool(company) and not self._shared_only(env)),
            },
            'read_only': True,
            'inactive_limit': self._config()['inactive_limit'],
            'inactive_models': inactive_models,
            'large_attachment_limit': self._config()['large_attachment_limit'],
            'large_attachment_limit_mb': (
                self._size_mb(self._config()['large_attachment_limit'])),
            'num_max_size_tables': self._config()['max_size_tables'],
            'table_sizes': table_sizes,
            'max_growth_tables': self._config()['max_growth_tables'],
            'growth_period_months': self._config()['growth_period'],
            'table_growth': table_growth,
            **attachment_report,
            'summary': {
                'models': len(inactive_models),
                'tables': len(table_sizes),
                'growth_tables': len(table_growth),
                **{
                    name: len(value) for name,
                    value in attachment_report.items()},
            },
        }

    def _tables_by_size_report(self, env, company=None, companies=None):
        company = companies if companies is not None else company
        if company and len(company) != 1:
            raise ValueError(
                'run_tables_by_size expects one company per scope.')
        if company:
            env = env['res.company'].with_context(
                preventive_maintenance_company_id=company.id).env
            tables = self._table_catalog(env)
            table_sizes = self._table_size_report(
                env, tables, companies=company if company else None)
        return {
            'generated_at': datetime.datetime.utcnow().isoformat() + 'Z',
            'scope': {
                'type': 'company'
                if company
                else ('shared' if self._shared_only(env) else 'database'),
                'company_id': company.id if company else None,
                'company_name': company.name if company else None,
            },
            'read_only': True,
            'max_size_tables': self._config()['max_size_tables'],
            'table_sizes': table_sizes,
            'summary': {'tables': len(table_sizes)},
        }

    def _tables_by_growth_report(self, env, company=None, companies=None):
        company = companies if companies is not None else company
        if company and len(company) != 1:
            raise ValueError(
                'run_tables_by_growth expects one company per scope.')
        if company:
            env = env['res.company'].with_context(
                preventive_maintenance_company_id=company.id).env
        tables = self._table_catalog(env)
        table_growth = self._table_growth_report(
            env, tables, companies=company if company else None)
        return {
            'generated_at': datetime.datetime.utcnow().isoformat() + 'Z',
            'scope': {
                'type': 'company'
                if company
                else ('shared' if self._shared_only(env) else 'database'),
                'company_id': company.id if company else None,
                'company_name': company.name if company else None,
            },
            'read_only': True,
            'max_growth_tables': self._config()['max_growth_tables'],
            'growth_period_months': self._config()['growth_period'],
            'table_growth': table_growth,
            'summary': {'growth_tables': len(table_growth)},
        }

    def _inactive_models_report(self, env, company=None, companies=None):
        company = companies if companies is not None else company
        if company and len(company) != 1:
            raise ValueError(
                'run_inactive_models expects one company per scope.')
        if company:
            env = env['res.company'].with_context(
                preventive_maintenance_company_id=company.id).env
        inactive_models = self._inactive_models(env)
        return {
            'generated_at': datetime.datetime.utcnow().isoformat() + 'Z',
            'scope': {
                'type': 'company'
                if company
                else ('shared' if self._shared_only(env) else 'database'),
                'company_id': company.id if company else None,
                'company_name': company.name if company else None,
            },
            'read_only': True,
            'inactive_limit': self._config()['inactive_limit'],
            'inactive_models': inactive_models,
            'summary': {'models': len(inactive_models)},
        }

    def _attachment_category_report(
            self, env, category, company=None, companies=None):
        company = companies if companies is not None else company
        if company and len(company) != 1:
            raise ValueError(
                'Attachment reports expect one company per scope.')
        if company:
            env = env['res.company'].with_context(
                preventive_maintenance_company_id=company.id).env
        categories = self._attachment_report(env, False)
        return {
            'generated_at': datetime.datetime.utcnow().isoformat() + 'Z',
            'scope': {
                'type': 'company'
                if company
                else ('shared' if self._shared_only(env) else 'database'),
                'company_id': company.id if company else None,
                'company_name': company.name if company else None,
            },
            'read_only': True,
            category: categories[category],
            'summary': {category: len(categories[category])},
        }

    def _large_attachments_report(self, env, company=None, companies=None):
        return self._attachment_category_report(
            env, 'large_attachments', company, companies)

    def _disconnected_attachments_report(
            self, env, company=None, companies=None):
        company = companies if companies is not None else company
        if company and len(company) != 1:
            raise ValueError(
                'Attachment reports expect one company per scope.')
        if company:
            env = env['res.company'].with_context(
                preventive_maintenance_company_id=company.id).env
        categories = self._attachment_report(env, True)
        disconnected = categories['disconnected_attachments']
        disconnected += categories['attachments_missing_model']
        disconnected += categories['attachments_with_broken_reference']
        disconnected += categories['attachments_missing_file']
        return {
            'generated_at': datetime.datetime.utcnow().isoformat() + 'Z',
            'scope': {
                'type': 'company'
                if company
                else ('shared' if self._shared_only(env) else 'database'),
                'company_id': company.id if company else None,
                'company_name': company.name if company else None,
            },
            'read_only': True,
            'disconnected_attachments': disconnected,
            'summary': {'disconnected_attachments': len(disconnected)},
        }
