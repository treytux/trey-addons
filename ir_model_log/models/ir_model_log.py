###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import logging
import traceback

from odoo import _, api, fields, models, tools
from odoo.tools.safe_eval import safe_eval

_log = logging.getLogger(__name__)


class IrModelLog(models.Model):
    _name = 'ir.model.log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Ir Model Log'
    _order = 'date_start desc'

    name = fields.Char(
        string='Operation',
        required=True,
    )
    date_start = fields.Datetime(
        string='Date start',
        default=fields.Datetime.now,
        required=True,
    )
    date_finish = fields.Datetime(
        string='Date finish',
    )
    elapsed = fields.Char(
        string='Elapsed',
    )
    description = fields.Text(
        string='Description',
    )
    res_model = fields.Char(
        string='Model',
    )
    res_ids = fields.Char(
        string='Ids list serialized',
        default='[]',
    )
    res_ids_count = fields.Integer(
        string='Records count',
        compute='_compute_res_ids_count',
    )

    @api.depends('res_ids')
    def _compute_res_ids_count(self):
        for log in self:
            ids = safe_eval(log.res_ids)
            log.res_ids_count = len(ids)

    @api.model
    def get_or_create_log(self, vals):
        domain = [(k, '=', v) for k, v in vals.items()]
        log = self.search(domain, limit=1, order='id DESC')
        if log.exists():
            return log
        return self.create(vals)

    def add_id(self, id):
        self.ensure_one()
        ids = safe_eval(self.res_ids)
        ids.append(id)
        self.res_ids = str(ids)

    def action_view_records(self):
        ids = safe_eval(self.res_ids)
        model = self.env[self.res_model]
        return {
            'name': model._description,
            'view_mode': 'tree,form',
            'res_model': self.res_model,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', ids)],
        }

    def info(self, text):
        self.ensure_one()
        if self.description:
            self.description = f'{self.description}{text}<br/>'
        else:
            self.description = f'{text}<br/>'
        _log.info(text)

    def warn(self, text):
        self.ensure_one()
        self.description += '%s<br/>' % text
        _log.warning(text)

    def exception(self, text, exception):
        trace = ''.join(traceback.format_tb(exception.__traceback__))
        trace = trace.replace('\n', '<br/>')
        text = '<strong>%s</strong><br/>%s' % (text, trace)
        self.error(text)

    def error(self, text):
        self.ensure_one()
        self.description += '%s<br/>' % text
        self.activity_schedule(
            summary=_('Errors when %s') % self.name,
            act_type_xmlid='mail.mail_activity_data_warning',
            user_id=self.env.user.id,
            note=text,
            date_deadline=fields.Date.today(),
        )
        _log.error(text)

    def rollback(self, force=False):
        self.ensure_one()
        if tools.config.get('test_enable') and not force:
            return self
        log_data = self.copy_data()[0]
        log_id = self.id
        website_id = log_data.get('website_id')
        if not tools.config.get('test_enable'):
            self.env.cr.rollback()
        log = self.browse(log_id)
        if not log.exists():
            if website_id and not self.env['website'].browse(website_id).exists():
                log_data['website_id'] = False
            log = self.create(log_data)
        else:
            log.write(log_data)
        if not tools.config.get('test_enable'):
            self.env.cr.commit()
        return log

    def finish(self, description=''):
        self.ensure_one()
        dt = fields.Datetime.now()
        description = '<p>%s</p>' % description
        self.write({
            'date_finish': dt,
            'elapsed': str(dt - self.date_start),
            'description': (self.description or '') + description,
        })

    def attach(self, name, content, mimetype='application/json'):
        if isinstance(content, bytes) and content.startswith(b'UEs'):
            encoded_content = content
        elif hasattr(content, 'read'):
            encoded_content = base64.b64encode(content.read())
        else:
            if isinstance(content, str):
                encoded_content = base64.b64encode(content.encode('utf-8'))
            else:
                encoded_content = base64.b64encode(content)

        self.ensure_one()
        self.env['ir.attachment'].create({
            'name': name,
            'datas': encoded_content,
            'store_fname': name,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': mimetype,
        })
