###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression


class IrTranslationBulkWizard(models.TransientModel):
    _name = 'ir.translation.bulk.wizard'
    _description = 'Bulk Translate Records'
    model_name = fields.Selection(
        selection='_get_models',
        string='Model',
        required=True,
    )
    model_has_company = fields.Boolean(
        string='Model Has Company',
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
        readonly=True,
        help='Only records belonging to this company are considered when the '
             'selected model has a company field.',
    )
    source_lang = fields.Selection(
        selection='_get_languages',
        string='Source Language',
        required=True,
    )
    field_ids = fields.Many2many(
        comodel_name='ir.model.fields',
        string='Fields to Translate',
        required=True,
        help='Select which fields to translate',
        domain="[('model', '=', model_name), ('translate', '=', True), "
               "'|', ('model', 'not in', "
               "['product.category', 'product.public.category']), "
               "('name', '=', 'name')]",
    )
    language_ids = fields.Many2many(
        comodel_name='res.lang',
        string='Target Languages',
        required=True,
        help='Languages to translate to',
    )
    overwrite_existing = fields.Boolean(
        string='Overwrite Existing Translations',
        help='Replace existing translations',
    )
    filter_type = fields.Selection(
        selection=[
            ('all', 'All records'),
            ('domain', 'Custom domain'),
            ('selected', 'Selected records'),
            ('translation_needed', 'Objects with fields to translate'),
        ],
        default='all',
        required=True,
        string='Filter Type',
    )
    selected_record_ids = fields.Char(
        string='Selected Record IDs',
        help='Comma-separated list of record IDs (internal)',
    )
    domain = fields.Text(
        string='Domain Filter',
        help='Odoo domain expression (used if Custom domain '
             'selected)',
        default='[]',
    )
    status_log = fields.Text(
        string='Status Log',
        readonly=True,
    )
    error_log = fields.Text(
        string='Translation Errors',
        readonly=True,
    )
    total_records_processed = fields.Integer(
        string='Records Processed',
        readonly=True,
    )
    candidate_count = fields.Integer(
        string='Objects Found',
        readonly=True,
    )
    search_done = fields.Boolean(
        string='Search Completed',
        readonly=True,
    )
    failed_translation_data = fields.Text(
        string='Failed Translations',
        readonly=True,
    )

    @api.model
    def _get_models(self):
        return [
            ('product.template', _('Product Template')),
            ('product.product', _('Product Variant')),
            ('product.public.category', _('Product Category')),
            ('website.page', _('Website Page')),
            ('blog.post', _('Blog Post Pages')),
            ('res.partner', _('Partner')),
        ]

    @api.model
    def _get_languages(self):
        langs = self.env['res.lang'].search([])
        return [(lang.code, lang.name) for lang in langs]

    @api.model
    def _get_default_source_lang(self):
        if self.env.user.lang:
            return self.env.user.lang
        lang = self.env['res.lang'].search([], limit=1)
        return lang.code if lang else None

    def _format_bulk_status_log(
            self, total_records, total_fields, total_languages,
            language_results, error_details,
            include_errors=True):
        final_log = [
            _('Bulk Translation Complete'),
            _('Total Records: %s') % total_records,
            _('Total Fields: %s') % total_fields,
            _('Total Languages: %s') % total_languages,
            _('Results:'),
        ]
        for language_name, summary in language_results:
            final_log.extend([
                f'{language_name}:',
                _('Success: %s') % summary['successful'],
                _('Skipped: %s') % summary['skipped'],
                _('Errors: %s') % summary['errors'],
            ])
        if include_errors and error_details:
            final_log.append('')
            final_log.append(_('Errors:'))
            final_log.extend(error_details)
        return '\n'.join(final_log)

    @api.onchange('model_name')
    def _onchange_model_name(self):
        self.field_ids = False
        self.model_has_company = bool(
            self.model_name and 'company_id'
            in self.env[self.model_name]._fields)
        self._reset_translation_search()

    @api.onchange(
        'source_lang', 'field_ids', 'language_ids', 'filter_type', 'company_id')
    def _onchange_translation_search_values(self):
        self._reset_translation_search()

    def _reset_translation_search(self):
        self.candidate_count = 0
        self.search_done = False
        if self.filter_type == 'translation_needed':
            self.selected_record_ids = False

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if 'source_lang' in fields_list:
            defaults['source_lang'] = (self._get_default_source_lang())
        active_ids = self.env.context.get('active_ids', [])
        active_model = self.env.context.get('active_model', '')
        if active_ids and active_model:
            defaults['model_name'] = active_model
            defaults['selected_record_ids'] = ','.join(
                str(id_) for id_ in active_ids)
            defaults['filter_type'] = 'selected'
        elif 'model_name' in fields_list:
            if 'default_model_name' in self.env.context:
                defaults['model_name'] = (
                    self.env.context['default_model_name']
                )
        if 'selected_record_ids' in fields_list:
            selected_ids = self.env.context.get('selected_record_ids', [])
            if selected_ids and 'filter_type' not in defaults:
                defaults['selected_record_ids'] = ','.join(
                    str(id_) for id_ in selected_ids)
                defaults['filter_type'] = 'selected'
        if 'model_has_company' in fields_list:
            model_name = defaults.get('model_name')
            defaults['model_has_company'] = bool(
                model_name and 'company_id'
                in self.env[model_name]._fields)
        if 'company_id' in fields_list:
            defaults['company_id'] = self.env.company.id
        return defaults

    def _get_company_domain(self):
        self.ensure_one()
        if not self.company_id or not self.model_name:
            return []
        model = self.env[self.model_name]
        if 'company_id' not in model._fields:
            return []
        return [('company_id', '=', self.company_id.id)]

    def action_translate_bulk(self):
        self.ensure_one()
        if not self.field_ids:
            raise UserError('Please select at least one field.')
        if not self.language_ids:
            raise UserError('Please select at least one target language.')
        try:
            if self.filter_type == 'domain':
                try:
                    domain = eval(self.domain or '[]')
                except Exception as e:
                    raise UserError(f'Invalid domain syntax: {str(e)}')
                records = self.env[self.model_name].search(
                    expression.AND([domain, self._get_company_domain()]))
            elif self.filter_type in ('selected', 'translation_needed'):
                try:
                    record_ids = [
                        int(id_)
                        for id_ in self.selected_record_ids.split(',')
                        if id_.strip()
                    ]
                    records = self.env[self.model_name].browse(record_ids)
                    records = records.exists()
                    company_domain = self._get_company_domain()
                    if company_domain:
                        records = records.filtered_domain(company_domain)
                except (ValueError, AttributeError) as e:
                    raise UserError(f'Invalid selected records: {str(e)}')
            else:
                records = self.env[self.model_name].search(
                    self._get_company_domain())
            if not records:
                raise UserError('No records found to translate.')
            config = self.env['res.config.settings'].sudo()
            provider = config.get_translation_provider()
            field_names = self.field_ids.mapped('name')
            error_details = []
            language_results = []
            failed_translations = []
            for lang in self.language_ids:
                summary = self.env[
                    'ir.translation.helper'
                ].translate_records_batch(
                    records,
                    field_names,
                    lang.code,
                    provider,
                    src_lang=self.source_lang,
                    overwrite=self.overwrite_existing)
                error_details.extend(summary['error_messages'])
                failed_translations.extend(
                    dict(item, dest_lang=lang.code)
                    for item in summary['error_items'])
                language_results.append((lang.name, summary))
            self.status_log = self._format_bulk_status_log(
                len(records), len(field_names), len(self.language_ids),
                language_results, error_details,
                include_errors=False)
            self.error_log = (
                '\n'.join(error_details) if error_details else False)
            self.total_records_processed = len(records)
            self.failed_translation_data = (
                json.dumps(failed_translations)
                if failed_translations else False)
        except UserError:
            raise
        except Exception as e:
            self.status_log = f'Error: {str(e)}'
            self.error_log = f'Error: {str(e)}'
            raise UserError(f'Translation error: {str(e)}')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ir.translation.bulk.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_find_records_needing_translation(self):
        self.ensure_one()
        if self.filter_type != 'translation_needed':
            raise UserError(
                _('This action is only available for the translation filter.'))
        if not self.field_ids:
            raise UserError(_('Please select at least one field.'))
        if not self.language_ids:
            raise UserError(_('Please select at least one target language.'))
        records = self.env[self.model_name].search(
            self._get_company_domain())
        field_names = self.field_ids.mapped('name')
        target_langs = self.language_ids.mapped('code')
        records = self.env[
            'ir.translation.helper'
        ].find_records_needing_translation(
            records,
            field_names,
            target_langs,
            src_lang=self.source_lang)
        self.selected_record_ids = ','.join(
            str(record.id) for record in records)
        self.candidate_count = len(records)
        self.total_records_processed = 0
        self.search_done = True
        self.status_log = _(
            'Objects found with fields requiring translation: %s'
        ) % len(records)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ir.translation.bulk.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_retry_failed_translations(self):
        self.ensure_one()
        if not self.failed_translation_data:
            raise UserError(_('There are no failed translations to retry.'))
        try:
            failed_translations = json.loads(self.failed_translation_data)
        except (TypeError, ValueError) as e:
            raise UserError(
                _('Invalid failed translation data: %s') % e)
        config = self.env['res.config.settings'].sudo()
        provider = config.get_translation_provider()
        helper = self.env['ir.translation.helper']
        remaining = []
        successful = 0
        skipped = 0
        retry_errors = []
        for item in failed_translations:
            record = self.env[self.model_name].browse(
                item['record_id']).exists()
            if not record:
                remaining.append(item)
                retry_errors.append(
                    _('%(record)s.%(field)s: record not found') % {
                        'record': item['record_id'],
                        'field': item['field_name'],
                    }
                )
                continue
            result = helper.translate_field_for_record(
                record, item['field_name'], item['dest_lang'], provider,
                src_lang=self.source_lang, overwrite=self.overwrite_existing)
            if result['success']:
                successful += 1
            elif 'skipping' in result['message']:
                skipped += 1
            else:
                remaining.append(item)
                retry_errors.append(
                    f'{item["record_id"]}.{item["field_name"]}: '
                    f'{result["message"]}')
        self.failed_translation_data = (
            json.dumps(remaining) if remaining else False)
        retry_log = [
            _('Retry Failed Translations'),
            _('Successful: %s') % successful,
            _('Skipped: %s') % skipped,
            _('Errors: %s') % len(remaining),
        ]
        if retry_errors:
            retry_log.extend(['', _('Errors:')] + retry_errors)
        self.status_log = '%s\n\n%s' % (
            self.status_log or '', '\n'.join(retry_log))
        self.error_log = '\n'.join(retry_errors) if retry_errors else False
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ir.translation.bulk.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
