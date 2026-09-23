###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import fields, models
from odoo.exceptions import UserError

from .deepl_provider import DeepLProvider
from .googletrans_provider import GoogletransProvider

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    translation_provider = fields.Selection(
        selection=[
            ('googletrans', 'Google Translate'),
            ('deepl', 'DeepL'),
        ],
        config_parameter='ir_translation_auto_translation.provider',
        default='googletrans',
    )
    translation_timeout = fields.Integer(
        config_parameter='ir_translation_auto_translation.timeout',
        default=10,
        help='Request timeout in seconds',
    )
    translation_deepl_api_key = fields.Char(
        string='DeepL API Key',
        config_parameter='ir_translation_auto_translation.deepl_api_key',
        password=True,
        help='API key used to access DeepL Translation API',
    )
    translation_retries = fields.Integer(
        config_parameter='ir_translation_auto_translation.retries',
        default=3,
        help='Number of retry attempts on failure',
    )
    translation_batch_size_chars = fields.Integer(
        config_parameter=(
            'ir_translation_auto_translation.batch_size_chars'
        ),
        default=5000,
        help='Max characters per batch request',
    )
    translation_sleep_between_calls_ms = fields.Integer(
        config_parameter=(
            'ir_translation_auto_translation.'
            'sleep_between_calls_ms'
        ),
        default=100,
        help='Milliseconds to wait between API calls',
    )
    translation_overwrite_existing = fields.Boolean(
        config_parameter=(
            'ir_translation_auto_translation.overwrite_existing'
        ),
        default=False,
        help='Default: overwrite existing translations in wizard',
    )

    def _get_translation_config(self):
        param = self.env['ir.config_parameter'].sudo()
        return {
            'timeout': param.get_param(
                'ir_translation_auto_translation.timeout',
                '10'
            ),
            'retries': param.get_param(
                'ir_translation_auto_translation.retries',
                '3'
            ),
            'batch_size_chars': param.get_param(
                'ir_translation_auto_translation.batch_size_chars',
                '5000'
            ),
            'sleep_between_calls_ms': param.get_param(
                'ir_translation_auto_translation.sleep_between_calls_ms',
                '100'
            ),
            'deepl_api_key': param.get_param(
                'ir_translation_auto_translation.deepl_api_key',
                ''),
        }

    def get_translation_provider(self):
        param = self.env['ir.config_parameter'].sudo()
        provider_code = param.get_param(
            'ir_translation_auto_translation.provider',
            'googletrans')
        config = self._get_translation_config()
        if provider_code == 'googletrans':
            provider = GoogletransProvider(config)
            _logger.info('Translation provider selected: %s', provider.code)
            return provider
        if provider_code == 'deepl':
            provider = DeepLProvider(config)
            _logger.info('Translation provider selected: %s', provider.code)
            return provider
        raise UserError(
            f'Unknown translation provider: {provider_code}')
