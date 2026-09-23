###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    chatgpt_api_key = fields.Char(
        string='ChatGPT API Key',
        config_parameter='chatgpt.api_key'
    )
    chatgpt_model = fields.Selection(
        [
            ('gpt-3.5-turbo', 'GPT-3.5 Turbo (Recommended, Balanced)'),
            ('gpt-3.5-turbo-0613', 'GPT-3.5 Turbo (0613 - Functions)'),
            ('gpt-3.5-turbo-16k', 'GPT-3.5 Turbo (16k - Extended Context)'),
            ('gpt-4', 'GPT-4 (More Capable, More Expensive)'),
            (
                'gpt-4-turbo-preview',
                'GPT-4 Turbo (Preview - Most Updated, Most Capable)'
            ),
        ],
        string='ChatGPT Model',
        config_parameter='chatgpt.default_model',
        default='gpt-3.5-turbo',
        help=(
            'Select the ChatGPT model to use for queries.\n'
            '• GPT-3.5 Turbo: balanced option in cost and performance, '
            'suitable for most use cases.\n'
            '• GPT-3.5 Turbo 16k: allows handling much longer input/output '
            'texts.\n'
            '• GPT-4: more advanced model, offers better results in complex '
            'tasks, but with higher cost and possibly stricter usage limits.\n'
            '• GPT-4 Turbo Preview: most updated and efficient version of '
            'GPT-4, recommended if available in your account.\n'
            'Note that the availability and limits of each model depend on '
            'your subscription and the access granted by OpenAI.'
        )
    )
