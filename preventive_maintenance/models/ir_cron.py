###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging
import traceback
from contextvars import ContextVar

from odoo import SUPERUSER_ID, api, fields, models

_logger = logging.getLogger(__name__)
_preventive_cron_context = ContextVar(
    'preventive_cron_context', default=None)
_MAX_TRACEBACK_LENGTH = 65536


class IrCron(models.Model):
    _inherit = 'ir.cron'

    def _preventive_cron_log_start(self, cron_id):
        try:
            with self.pool.cursor() as cursor:
                env = api.Environment(cursor, SUPERUSER_ID, {})
                return env['preventive.maintenance.cron.history'].create({
                    'cron_id': cron_id,
                    'state': 'running',
                }).id
        except Exception:
            _logger.exception('Could not start preventive cron history log')
            return None

    def _preventive_cron_log_end(self, history_id, state, error_traceback):
        if not history_id:
            return
        try:
            with self.pool.cursor() as cursor:
                env = api.Environment(cursor, SUPERUSER_ID, {})
                env['preventive.maintenance.cron.history'].browse(
                    history_id).write({
                        'state': state,
                        'date_end': fields.Datetime.now(),
                        'error_traceback': error_traceback,
                    })
        except Exception:
            _logger.exception('Could not finish preventive cron history log')

    def _callback(self, cron_name, server_action_id, job_id):
        history_id = self._preventive_cron_log_start(self.id or job_id)
        context = {'history_id': history_id, 'failed': False}
        token = _preventive_cron_context.set(context)
        try:
            result = super()._callback(cron_name, server_action_id, job_id)
        except Exception:
            context['failed'] = True
            self._preventive_cron_log_end(
                history_id, 'failed',
                traceback.format_exc()[-_MAX_TRACEBACK_LENGTH:])
            raise
        finally:
            if not context['failed']:
                self._preventive_cron_log_end(history_id, 'success', None)
            _preventive_cron_context.reset(token)
        return result

    def _handle_callback_exception(
            self, cron_name, server_action_id, job_id, job_exception):
        context = _preventive_cron_context.get()
        if context and not context['failed']:
            context['failed'] = True
            self._preventive_cron_log_end(
                context['history_id'], 'failed',
                traceback.format_exc()[-_MAX_TRACEBACK_LENGTH:])
        return super()._handle_callback_exception(
            cron_name, server_action_id, job_id, job_exception)

    def method_direct_trigger(self):
        for cron in self:
            history_id = cron._preventive_cron_log_start(cron.id)
            try:
                super(IrCron, cron).method_direct_trigger()
            except Exception:
                cron._preventive_cron_log_end(
                    history_id, 'failed',
                    traceback.format_exc()[-_MAX_TRACEBACK_LENGTH:])
                raise
            cron._preventive_cron_log_end(history_id, 'success', None)
        return True
