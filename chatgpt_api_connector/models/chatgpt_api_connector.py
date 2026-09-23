###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

import openai
from odoo import _, models
from odoo.exceptions import UserError
from openai import (APIError, AuthenticationError, ConflictError,
                    NotFoundError, PermissionDeniedError, RateLimitError,
                    UnprocessableEntityError)

_logger = logging.getLogger(__name__)


class ChatGPTApiConnector(models.AbstractModel):
    _name = 'chatgpt.api.connector'
    _description = 'API Connector for ChatGPT (OpenAI)'

    def _get_api_key(self):
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'chatgpt.api_key')
        if not api_key or api_key == 'PASTE_YOUR_OPENAI_API_KEY_HERE':
            raise UserError(
                _('Missing ChatGPT API key. Configure it in System Settings '
                  '(technical name: chatgpt.api_key).')
            )
        return api_key

    def chat_completion(
            self, prompt, model=None, temperature=0.3, max_tokens=1500,
            system_message_content=None):
        api_key = self._get_api_key()
        client = openai.OpenAI(api_key=api_key)
        used_model = model
        if not used_model:
            used_model = self.env['ir.config_parameter'].sudo().get_param(
                'chatgpt.default_model', 'gpt-3.5-turbo')
        if system_message_content is None:
            system_message_content = _(
                'You are a highly efficient technical support assistant for '
                'Odoo. You will be provided with the description of an Odoo '
                'task and the conversation history related to it. Your goal '
                'is to analyze this information and provide a concise and '
                'actionable solution or next steps to resolve the task. '
                'Focus on practical advice.')
        messages = [
            {'role': 'system', 'content': system_message_content},
            {'role': 'user', 'content': prompt}
        ]
        _logger.info(
            'Sending request to OpenAI. Model: {used_model}, Max Tokens: '
            '{max_tokens}, Temp: {temperature}')
        try:
            response = client.chat.completions.create(
                model=used_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            content = response.choices[0].message.content.strip()
            _logger.info(
                'Received response from OpenAI. Length: {len(content)}')
            return content
        except AuthenticationError as e:
            _logger.error('OpenAI API Authentication Error: {str(e)}')
            raise UserError(_(
                'OpenAI API Authentication Failed. Please check your API Key. '
                'Error: %s') % str(e))
        except PermissionDeniedError as e:
            _logger.error('OpenAI API Permission Denied Error: {str(e)}')
            raise UserError(_(
                'OpenAI API Permission Denied. Please check your API Key´s '
                'permissions. Error: %s') % str(e))
        except NotFoundError as e:
            _logger.error(
                'OpenAI API Not Found Error (e.g., model not found): '
                '{str(e)}')
            raise UserError(_(
                'OpenAI Resource Not Found (e.g., model specified might not '
                'exist or is mistyped). Error: %s') % str(e))
        except RateLimitError as e:
            _logger.error('OpenAI API Rate Limit Exceeded: {str(e)}')
            raise UserError(_(
                'OpenAI API Rate Limit Exceeded. Please try again later or '
                'check your plan. Error: %s') % str(e))
        except ConflictError as e:
            _logger.error('OpenAI API Conflict Error: {str(e)}')
            raise UserError(_('OpenAI API Conflict Error: %s') % str(e))
        except UnprocessableEntityError as e:
            _logger.error('OpenAI API Unprocessable Entity Error: {str(e)}')
            raise UserError(_(
                'OpenAI API Unprocessable Entity (e.g. invalid request '
                'parameters): %s') % str(e))
        except APIError as e:
            _logger.error('OpenAI API General Error: {str(e)}')
            raise UserError(_('General OpenAI API Error: %s') % str(e))
        except Exception as e:
            _logger.error(
                'Unexpected error during ChatGPT API call: {str(e)} (Type: '
                '{type(e)})')
            error_detail = str(e)
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                error_detail = e.response.text
            raise UserError(_(
                'An unexpected error occurred while contacting ChatGPT: %s') %
                error_detail)
