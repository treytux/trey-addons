###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import argparse
import datetime
import json
import logging
from inspect import signature
from pathlib import Path

_logger = logging.getLogger(__name__)
MAX_GROUPS = 500
MAX_IDS_PER_GROUP = 200
FUZZY_NAME_THRESHOLD = 0.88
REPORT_FILENAME = 'records_integrity_report.json'


def _field(model, name):
    return model._fields.get(name)


def _active(model):
    return [('active', '=', True)] if _field(model, 'active') else []


def _add(report, check, severity, model, message, ids=None, **values):
    row = {
        'check': check,
        'severity': severity,
        'model': model,
        'message': message,
    }
    if ids:
        row['record_ids'] = ids[:MAX_IDS_PER_GROUP]
        row['record_count'] = len(ids)
        row['record_ids_truncated'] = len(ids) > MAX_IDS_PER_GROUP
    row.update(values)
    report.append(row)


def _sql(env, query, params=()):
    env.cr.execute(query, params)
    return env.cr.dictfetchall()


def _warning(report, check, model, message, **values):
    _add(report, check, 'warning', model, message, **values)


def _model(env, model_name):
    try:
        return env[model_name].sudo()
    except KeyError:
        return None


def _missing_active_models(env, model_names):
    missing = []
    for model_name in model_names:
        model = _model(env, model_name)
        if model is not None and not _field(model, 'active'):
            missing.append(model_name)
    return missing


def _add_query_issue(
        env, report, query, params, check, severity, model, message, **values):
    aggregate = (
        '''
        WITH matches AS (
            SELECT DISTINCT id
            FROM (
        '''
        + query
        + '''
            ) raw
        ), sample AS (
            SELECT id
            FROM matches
            ORDER BY id
            LIMIT %s
        )
        SELECT count(*) AS total_count,
            COALESCE(
                (SELECT array_agg(id) FROM sample),
                ARRAY[]::integer[]
            ) AS ids
        FROM matches
        ''')
    rows = _sql(env, aggregate, tuple(params) + (MAX_IDS_PER_GROUP,))
    if not rows or not rows[0]['total_count']:
        return
    _add(
        report, check, severity, model, message, rows[0]['ids'],
        record_count=rows[0]['total_count'], **values)


def _duplicates(model, fields, report, check, message):
    fields = [
        name for name in fields if _field(model, name)
        and _field(model, name).store]
    if not fields:
        return
    domain = _active(model) + [(name, '!=', False) for name in fields]
    kwargs = {
        'fields': fields + ['id:count'],
        'groupby': fields,
        'lazy': False,
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
        group_domain = list(_active(model))
        for name in fields:
            value = group.get(name)
            values[name] = value[0] if isinstance(value, tuple) else value
            group_domain.append((name, '=', values[name]))
        ids = model.search(
            group_domain, order='id', limit=MAX_IDS_PER_GROUP + 1
        ).ids
        _add(report, check, 'high', model._name, message, ids, fields=fields,
             values=values, count=count)
        if len(report) >= MAX_GROUPS:
            break


def _contacts(env, report):
    partner = env['res.partner'].sudo()
    for field, check, message in (
        ('email', 'contact.email_duplicate',
         'Active contacts share a normalized email.'),
        ('name', 'contact.name_duplicate',
         'Active contacts share a normalized name.')):
        for row in _sql(
            env,
            '''
            SELECT
                lower(regexp_replace(%s, '\\s+', ' ', 'g')) normalized,
                array_agg(id ORDER BY id) ids,
                count(*) count
            FROM res_partner
            WHERE
                active IS TRUE
                AND %s IS NOT NULL
                AND btrim(%s) <> ''
            GROUP BY normalized
            HAVING count(*) > 1
            ORDER BY count(*) DESC
            LIMIT %%s
                ''' % (field, field, field), (MAX_GROUPS,)):
            _add(report, check, 'high' if field == 'email' else 'medium',
                 'res.partner', message, row['ids'],
                 normalized=row['normalized'], count=row['count'])
    for row in _sql(
        env,
        '''
        SELECT
            regexp_replace(phone, '[^0-9+]', '', 'g') AS normalized_phone,
            array_agg(id ORDER BY id) AS ids,
            count(*) AS count
        FROM res_partner
        WHERE
            active IS TRUE
            AND phone IS NOT NULL
            AND btrim(phone) <> ''
        GROUP BY normalized_phone
        HAVING count(*) > 1
        ORDER BY count(*) DESC
        LIMIT %s
            ''', (MAX_GROUPS,)):
        _add(
            report, 'contact.phone_duplicate', 'medium', 'res.partner',
            'Active contacts share a normalized phone.', row['ids'],
            normalized_phone=row['normalized_phone'], count=row['count'])
    _add_query_issue(
        env, report,
        '''
        SELECT id
        FROM res_partner
        WHERE
            active IS TRUE
            AND (name IS NULL OR btrim(name) = '')
        ''', (), 'contact.name_missing', 'high', 'res.partner',
        'Active contact has no name.')
    roles = []
    if _field(partner, 'customer_rank'):
        roles.append('p.customer_rank > 0')
    if _field(partner, 'supplier_rank'):
        roles.append('p.supplier_rank > 0')
    if roles and all(_field(partner, x) for x in ('parent_id', 'vat', 'email')):
        _add_query_issue(
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
            ''' % ' OR '.join(roles), (), 'contact.child_email_missing',
            'medium', 'res.partner',
            'Customer/supplier child has no email while its parent has VAT.')
    _add_query_issue(
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
        ''', (), 'contact.parent_company_mismatch', 'high', 'res.partner',
        'Contact company differs from its parent company.')
    if _field(partner, 'vat') and _field(partner, 'country_id'):
        _add_query_issue(
            env, report,
            '''
            SELECT id
            FROM res_partner
            WHERE
                active IS TRUE
                AND (customer_rank > 0 OR supplier_rank > 0)
                AND btrim(COALESCE(vat, '')) <> ''
                AND country_id IS NULL
            ''', (), 'contact.fiscal_country_missing', 'medium', 'res.partner',
            'Customer/supplier with VAT has no fiscal country.')

    if not _sql(env, "SELECT 1 FROM pg_extension WHERE extname='pg_trgm'"):
        _add(
            report, 'contact.fuzzy_name_unavailable', 'warning', 'res.partner',
            'pg_trgm is not installed; fuzzy matching was not run.')
        return
    for row in _sql(
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
            AND a.name IS NOT NULL
            AND b.name IS NOT NULL
            AND lower(regexp_replace(a.name, '\\s+', ' ', 'g')) %%
                lower(regexp_replace(b.name, '\\s+', ' ', 'g'))
            AND similarity(lower(regexp_replace(a.name, '\\s+', ' ', 'g')),
                lower(regexp_replace(b.name, '\\s+', ' ', 'g'))) >= %s
        ORDER BY score DESC LIMIT %s
            ''', (FUZZY_NAME_THRESHOLD, MAX_GROUPS)):
        _add(
            report, 'contact.fuzzy_name_duplicate', 'medium', 'res.partner',
            'Active contacts have highly similar normalized names.',
            [
                row['left_id'],
                row['right_id'],
            ], similarity=float(row['score']))


def _products(env, report):
    template = env['product.template'].sudo()
    variant = env['product.product'].sudo()
    _duplicates(
        template, ['name'], report, 'product.name_duplicate',
        'Active product templates share a name.')
    code_fields = [
        x for x in ('default_code', 'internal_code', 'internal_reference')
        if _field(template, x)]
    for code_field in code_fields:
        _duplicates(
            template, [code_field], report, 'product.reference_duplicate',
            'Active product templates share an internal reference.')
    _duplicates(
        variant, ['default_code'], report, 'product.reference_duplicate',
        'Active variants share an internal reference.')
    fields = [
        x for x in ('name', 'categ_id', 'uom_id', 'uom_po_id', 'list_price')
        if _field(template, x)]
    clauses = [
        ('btrim(COALESCE(name->>\'en_US\', \'\')) = \'\'' if x == 'name'
         else '%s IS NULL' % x) for x in fields]
    if clauses:
        _add_query_issue(
            env, report,
            'SELECT id FROM product_template WHERE active IS TRUE AND (%s)'
            % ' OR '.join(clauses), (), 'product.required_field_missing',
            'high', 'product.template', 'Active template lacks a key field.',
            fields=fields)
    _add_query_issue(
        env, report,
        '''
        SELECT p.id
        FROM product_product p
        JOIN
            product_template t
            ON t.id = p.product_tmpl_id
        CROSS JOIN res_company company
        WHERE
            p.active IS TRUE
            AND t.active IS TRUE
            AND NOT EXISTS (
                SELECT 1
                FROM ir_property cost
                WHERE cost.name = 'standard_price'
                    AND cost.res_id = 'product.product,' || p.id::text
                    AND cost.company_id = company.id
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
        ''', (), 'product.standard_price_missing', 'high', 'product.product',
        'Active variant has no company-dependent standard price.',
        fields=['standard_price'])
    _add_query_issue(
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
        ''', (), 'product.variant_reference_missing', 'medium',
        'product.product',
        'Variant and parent template both have an empty internal reference.')
    _add_query_issue(
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
        ''', (), 'product.variant_template_reference_collision', 'high',
        'product.product',
        'Variant reference matches its parent template reference.')
    _add_query_issue(
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
        ''', (), 'product.cross_template_reference_duplicate', 'high',
        'product.product', 'Variant reference is reused by another template.')
    for row in _sql(
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
            ''', (MAX_GROUPS,)):
        _add(report, 'product.variant_duplicate', 'high', 'product.product',
             'Variants share the same template and attribute values.',
             row['ids'], product_tmpl_id=row['product_tmpl_id'],
             attributes=row['attrs'], count=row['count'])


def _relationships(env, report):
    _add_query_issue(
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
        ''', ('%route_by%',), 'product.route_without_supplier', 'medium',
        'product.product',
        'Product route contains route_by but has no supplier.')
    _add_query_issue(
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
        ''', (), 'product.uom_category_mismatch', 'high', 'product.template',
        'Sales and purchase UoMs have different categories; '
        'no valid conversion exists.')
    _add_query_issue(
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
        ''', (), 'product.variant_attribute_integrity', 'high',
        'product.product',
        'Variant attribute is not declared on its parent template.')


def _supplier_dates(env, report):
    _add_query_issue(
        env, report,
        '''
        SELECT id
        FROM product_supplierinfo
        WHERE date_start IS NOT NULL
            AND date_end IS NOT NULL
            AND date_end < date_start
        ''', (), 'product.supplier_dates_invalid', 'medium',
        'product.supplierinfo',
        'Supplier information has an end date before its start date.')


CHECKS = (
    ('contacts', _contacts, ('res.partner',)),
    ('products', _products, ('product.template', 'product.product')),
    ('relationships', _relationships, (
        'product.product', 'product.template', 'uom.uom', 'stock.route')),
    ('supplier_dates', _supplier_dates, ('product.supplierinfo',)))


def _run_check(env, report, check_name, function, model_names):
    missing_models = [
        name for name in model_names if _model(env, name) is None]
    if missing_models:
        _warning(
            report, 'audit.capability', ','.join(missing_models),
            'Check skipped because required model(s) are not installed.',
            audit_check=check_name, missing_models=missing_models)
        return
    missing_active = _missing_active_models(env, model_names)
    if missing_active:
        _warning(
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
        _warning(
            report, 'audit.check_failed', 'audit',
            'Check failed and was skipped; remaining checks continued.',
            audit_check=check_name, error_type=type(error).__name__,
            error=str(error))


def run_audit(env):
    report = []
    for check_name, function, model_names in CHECKS:
        _run_check(env, report, check_name, function, model_names)
    severities = {}
    for row in report:
        severities[row['severity']] = severities.get(row['severity'], 0) + 1
    return {
        'model': 'record_report.check',
        'odoo_version': '16.0',
        'generated_at': datetime.datetime.utcnow().isoformat() + 'Z',
        'read_only': True,
        'archived_records_excluded': True,
        'sample_size': MAX_IDS_PER_GROUP,
        'summary': {
            'findings': len(report),
            'by_severity': severities,
        },
        'checks': report,
    }


def main(env):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--json', action='store_true')
    parser.parse_known_args()
    result = run_audit(env)
    output = json.dumps(result, ensure_ascii=False, default=str, indent=2)
    output_path = Path(__file__).resolve().with_name(REPORT_FILENAME)
    output_path.write_text(output + '\n', encoding='utf-8')
    _logger.info('Data integrity audit:\n%s', output)
    print(output)
    print('JSON report saved to: %s' % output_path)
    return result


odoo_env = globals().get('env')
if odoo_env is not None:
    main(odoo_env)
