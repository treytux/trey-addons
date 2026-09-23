###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import logging
import traceback

from odoo import _, api, fields, models, tools
from odoo.tools.safe_eval import safe_eval

_log = logging.getLogger(__name__)


class WebsiteWooLog(models.Model):
    _name = 'website.woo.log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Website Woocommerce log'
    order = 'date_start desc'

    website_id = fields.Many2one(
        comodel_name='website',
        string='Website',
        required=True,
    )
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
        default='',
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
    def rollback(self, website):
        if tools.config.get('test_enable'):
            return self
        data = self._convert_to_write(self._cache)
        self.env.cr.rollback()
        log = self.create(data)
        log.warn('Rollback!')
        return log

    def add_id(self, id):
        self.ensure_one()
        ids = safe_eval(self.res_ids)
        self.res_ids = str(ids)

    def action_view_records(self):
        ids = safe_eval(self.res_ids)
        model = self.env[self.res_model]
        return {
            'name': model._description,
            'view_type': 'form',
            'view_mode': 'tree,form,',
            'res_model': self.res_model,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', ids)],
        }

    def info(self, text):
        self.ensure_one()
        self.description += '%s<br/>' % text
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
        _log.error(text)
        self.activity_schedule(
            summary=_('Errors when %s') % self.name,
            act_type_xmlid='mail.mail_activity_data_warning',
            user_id=(
                self.website_id.salesperson_id.id
                if self.website_id.salesperson_id else self.env.user.id),
            note=text,
            date_deadline=fields.Date.today(),
        )

    def finish(self, description=''):
        self.ensure_one()
        dt = fields.Datetime.now()
        description = '<p>%s</p>' % description
        self.write({
            'date_finish': dt,
            'elapsed': str(dt - self.date_start),
            'description': self.description + description,
        })

    def attach(self, name, content, mimetype='application/json'):
        self.ensure_one()
        self.env['ir.attachment'].create({
            'name': name,
            'datas': base64.b64encode(content.encode()),
            'datas_fname': name,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': mimetype,
        })
