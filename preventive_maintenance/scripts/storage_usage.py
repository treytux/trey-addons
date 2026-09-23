###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import argparse
import datetime
import json
import logging
from pathlib import Path

_logger = logging.getLogger(__name__)

INNACTIVE_LIMIT = 100
LARGE_ATTACHMENT_LIMIT = 5 * 1024 * 1024
NUM_MAX_SIZE_TABLES = 10
REPORT_FILENAME = 'storage_usage.json'


def _field(model, name):
    return model._fields.get(name)


def _model(env, model_name):
    try:
        return env[model_name].sudo()
    except (KeyError, TypeError):
        return None


def _inactive_models(env):
    result = []
    model_registry = env['ir.model'].sudo().search([], order='model')
    for model_record in model_registry:
        model = _model(env, model_record.model)
        if model is None or not _field(model, 'active'):
            continue
        try:
            with env.cr.savepoint():
                inactive_count = model.search_count([
                    ('active', '=', False),
                ])
                if inactive_count < INNACTIVE_LIMIT:
                    continue
                result.append({
                    'model': model._name,
                    'inactive_count': inactive_count,
                })
        except Exception:
            _logger.exception(
                'Could not inspect inactive records in %s', model_record.model)
    return result


def _attachment_data(attachment, **values):
    data = {
        'id': attachment.id,
        'name': attachment.name,
        'file_size': attachment.file_size,
        'res_model': attachment.res_model or None,
        'res_id': attachment.res_id or None,
    }
    data.update(values)
    return data


def _attachment_report(env):
    attachment_model = env['ir.attachment'].sudo()
    categories = {
        'duplicate_attachments': [],
        'large_attachments': [],
        'attachments_missing_model': [],
        'disconnected_attachments': [],
        'url_only_attachments': [],
        'attachments_with_broken_reference': [],
    }
    url_attachments = attachment_model.search([
        ('type', '=', 'url'),
    ], order='id')
    categories['url_only_attachments'] = [
        _attachment_data(attachment, url=attachment.url)
        for attachment in url_attachments
    ]
    categories['large_attachments'] = [
        _attachment_data(attachment)
        for attachment in attachment_model.search([
            ('type', '=', 'binary'),
            ('file_size', '>=', LARGE_ATTACHMENT_LIMIT),
        ], order='id')
    ]
    duplicate_groups = attachment_model.read_group([
        ('type', '=', 'binary'),
        ('checksum', '!=', False),
    ], ['checksum', 'id:count'], ['checksum'], lazy=False)
    for group in duplicate_groups:
        count = group.get('id_count', group.get('__count', 0))
        if count < 2:
            continue
        checksum = group.get('checksum')
        attachments = attachment_model.search([
            ('checksum', '=', checksum),
        ], order='id')
        categories['duplicate_attachments'].append({
            'checksum': checksum,
            'count': count,
            'file_size': attachments[0].file_size if attachments else 0,
            'attachments': [
                _attachment_data(attachment)
                for attachment in attachments
            ],
        })
    registered_models = set(
        env['ir.model'].sudo().search([]).mapped('model'))
    rows = attachment_model.search([
        ('type', '=', 'binary'),
    ], order='id')
    grouped = {}
    for attachment in rows:
        if not attachment.res_model and not attachment.res_id:
            categories['disconnected_attachments'].append(
                _attachment_data(attachment))
            continue
        if attachment.res_model not in registered_models:
            categories['attachments_missing_model'].append(
                _attachment_data(attachment))
            continue
        if not attachment.res_id:
            categories['attachments_with_broken_reference'].append(
                _attachment_data(attachment, reason='missing_res_id'))
            continue
        grouped.setdefault(attachment.res_model, []).append(attachment)
    for model_name, attachments in grouped.items():
        try:
            with env.cr.savepoint():
                target = _model(env, model_name)
                if target is None:
                    raise ValueError('model is not available in the registry')
                existing_ids = set(target.browse([
                    attachment.res_id for attachment in attachments
                ]).exists().ids)
        except Exception:
            _logger.exception(
                'Could not validate attachment references in %s', model_name)
            continue
        categories['attachments_with_broken_reference'].extend(
            _attachment_data(attachment, reason='record_not_found')
            for attachment in attachments
            if attachment.res_id not in existing_ids
        )
    return categories


def _table_size_report(env):
    env.cr.execute(
        '''
        SELECT
            relname AS table,
            pg_size_pretty(pg_total_relation_size(relid)) AS size,
            pg_size_pretty(
                pg_total_relation_size(relid) - pg_relation_size(relid)
            ) AS external_size
        FROM pg_catalog.pg_statio_user_tables
        ORDER BY pg_total_relation_size(relid) DESC
        LIMIT %s
        ''',
        (NUM_MAX_SIZE_TABLES,)
    )
    return [
        {
            'table': table,
            'size': size,
            'external_size': external_size,
        }
        for table, size, external_size in env.cr.fetchall()
    ]


def run_report(env):
    inactive_models = _inactive_models(env)
    attachment_report = _attachment_report(env)
    table_sizes = _table_size_report(env)
    return {
        'generated_at': datetime.datetime.utcnow().isoformat() + 'Z',
        'read_only': True,
        'inactive_limit': INNACTIVE_LIMIT,
        'inactive_models': inactive_models,
        'large_attachment_limit': LARGE_ATTACHMENT_LIMIT,
        'num_max_size_tables': NUM_MAX_SIZE_TABLES,
        'table_sizes': table_sizes,
        **attachment_report,
        'summary': {
            'models': len(inactive_models),
            'tables': len(table_sizes),
            **{
                name: len(value) for name, value in attachment_report.items()
            },
        },
    }


def main(env):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--json', action='store_true')
    parser.parse_known_args()
    result = run_report(env)
    output = json.dumps(result, ensure_ascii=False, default=str, indent=2)
    output_path = Path(__file__).resolve().with_name(REPORT_FILENAME)
    output_path.write_text(output + '\n', encoding='utf-8')
    _logger.info('Unused records report:\n%s', output)
    print(output)
    print('JSON report saved to: %s' % output_path)
    return result


odoo_env = globals().get('env')
if odoo_env is not None:
    main(odoo_env)
