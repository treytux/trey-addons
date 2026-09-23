###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.exceptions import UserError


class IrTranslationWizard(models.TransientModel):
    _name = 'ir.translation.wizard'
    _description = 'Translate Single Record'
    model_name = fields.Char(
        string='Model',
        required=True,
        readonly=True,
    )
    record_id = fields.Integer(
        string='Record ID',
        required=True,
        readonly=True,
    )
    source_lang = fields.Selection(
        selection='_get_languages',
        string='Source Language',
        required=True,
    )
    field_ids = fields.Many2many(
        comodel_name='ir.model.fields',
        string='Fields to Translate',
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
        default=False,
        help='Replace existing translations',
    )
    status_log = fields.Text(
        string='Status Log',
        readonly=True,
    )

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

    @api.onchange('model_name')
    def _onchange_model_name(self):
        self.field_ids = False

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if 'source_lang' in fields_list:
            defaults['source_lang'] = (self._get_default_source_lang())
        if 'model_name' in fields_list:
            defaults['model_name'] = self.env.context.get(
                'default_model_name',
                '')
        if 'record_id' in fields_list:
            defaults['record_id'] = self.env.context.get(
                'default_record_id',
                0)
        if defaults.get('model_name') and 'field_ids' in (
            fields_list
        ):
            model_name = defaults['model_name']
            translatable = self.env[
                'ir.translation.helper'
            ].get_translatable_fields(model_name)
            field_ids = self.env['ir.model.fields'].search([
                ('model', '=', model_name),
                ('name', 'in', [f[0] for f in translatable]),
            ]).ids
            defaults['field_ids'] = [(6, 0, field_ids)]
        return defaults

    def action_translate(self):
        self.ensure_one()
        if not self.field_ids:
            raise UserError('Please select at least one field.')
        if not self.language_ids:
            raise UserError('Please select at least one target language.')
        try:
            config = self.env['res.config.settings'].sudo()
            provider = config.get_translation_provider()
            record = self.env[self.model_name].browse(
                self.record_id)
            if not record.exists():
                raise UserError('Record not found.')
            field_names = self.field_ids.mapped('name')
            logs = []
            for lang in self.language_ids:
                summary = self.env[
                    'ir.translation.helper'
                ].translate_records_batch(
                    record,
                    field_names,
                    lang.code,
                    provider,
                    src_lang=self.source_lang,
                    overwrite=self.overwrite_existing)
                log_msg = (
                    f'Translated to {lang.name}: '
                    f'Success: {summary["successful"]}, '
                    f'Skipped: {summary["skipped"]}, '
                    f'Errors: {summary["errors"]}'
                )
                logs.append(log_msg)
            self.status_log = '\n'.join(logs)
        except Exception as e:
            raise UserError(f'Translation error: {str(e)}')
        return {'type': 'ir.actions.act_window_close'}
