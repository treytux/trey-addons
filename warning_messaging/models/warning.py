# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import api, models, fields, exceptions
import logging

_log = logging.getLogger(__name__)


class WarningCondition(models.Model):
    _name = 'warning.condition'
    _description = 'Warning condition'

    name = fields.Char(
        string='Name',
        required=True)
    warning_id = fields.Many2one(
        comodel_name='warning.messaging',
        string='Warning message')
    model_id = fields.Many2one(
        related='warning_id.model_id',
        comodel_name='ir.model',
        string='Model',
        required=True)
    field_id = fields.Many2one(
        comodel_name='ir.model.fields',
        string='Field',
        required=True)
    condition = fields.Selection([
        ('=', 'equal'),
        ('!=', 'not equal'),
        ('>', 'more than'),
        ('=>', 'more or equal than'),
        ('<', 'less than'),
        ('=<', 'less or equal than'),
        ('in', 'in'),
        ('not in', 'not in'),
        ('like', 'contains'),
        ('not like', 'not contains')],
        string='Condition',
        required=True)
    value = fields.Char(
        string='Value',
        required=True)

    # Obtiene los campos del modelo 'model_id'
    @api.model
    def get_fields(self):
        re = []
        if self.model_id:
            return [(f.name, f.field_description)
                    for f in self.model_id.field_id]
        return re


class WarningAction(models.Model):
    _name = 'warning.action'
    _description = 'Warning action'

    name = fields.Char(
        string='Name',
        required=True)
    ttype = fields.Selection([
        ('send_msg', 'Send alert message')],
        string='Type',
        required=True)
    active = fields.Boolean(
        string='Active',
        default=True)
    warning_id = fields.Many2one(
        comodel_name='warning.messaging',
        string='Warning message')


class WarningMessaging(models.Model):
    _name = 'warning.messaging'
    _description = 'Warning messaging'

    name = fields.Char(
        string='Name',
        required=True)
    model_id = fields.Many2one(
        comodel_name='ir.model',
        string='Model',
        required=True)
    cron_id = fields.Many2one(
        comodel_name='ir.cron',
        string='Cron Job',
        readonly=True,
        help="Scheduled Action associated.")
    body = fields.Text(
        string='Body',
        translate=True,
        required=True,
        help="Text to include in the message sent.")
    state = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive')],
        string='State',
        default='inactive',
        readonly=True)
    condition_ids = fields.One2many(
        comodel_name='warning.condition',
        inverse_name='warning_id',
        string='Conditions',
        help="Conditions to be met the object registers.")
    action_ids = fields.One2many(
        comodel_name='warning.action',
        inverse_name='warning_id',
        string='Actions',
        help="Actions to be executed if the condition are met.")

    # Activar el aviso:
    # Comprueba si ya tiene una accion planificada asociada.
    # Si la tiene, la activa
    # Si no la tiene, crea una nueva y se la asigna al aviso
    @api.one
    def to_active(self):
        # Si no tiene una accion planificada asociada, la crea
        if not self.cron_id:
            # Crear la accion planificada
            cron = self.env['ir.cron'].create({
                'name': self.name,
                'model': 'warning.messaging',
                'function': 'action_execute',
                'user_id': self.create_uid.id,
                'numbercall': -1,
                'nextcall': self.create_date,
                'priority': 6,
                # Por defecto, ejecutar el cron una vez a la hora
                'interval_number': 1,
                'interval_type': 'hours',
                'active': True
            })

            # Asignar los argumentos al cron:
            # [<aviso_id>, {'active_id': <cron_id>}]
            cron.args = [self.id, {'active_id': cron.id}]

            # Asignar el cron creado al aviso
            self.cron_id = cron.id

        # Si ya tiene una asignada, la activa
        else:
            self.cron_id.active = True

        self.state = 'active'
        return True

    # Desactivar el aviso: desactiva el aviso y la accion planificada asociada
    @api.one
    def to_inactive(self):
        self.state = 'inactive'
        if self.cron_id:
            self.cron_id.active = False
        return True

    @api.one
    def action_execute(self):
        domain = []
        for cond in self.condition_ids:
            try:
                cmd = ('import time', 'import datetime', cond.value)
                value = eval('\n'.join(cmd))
                domain.append((cond.field_id.name,
                               cond.condition,
                               value))
            except Exception as e:
                raise exceptions.Warning(
                    'Warning %s has an error in condition '
                    'value %s: %s'
                    % (self.name, cond.value, e))

        model_obj = self.env[self.model_id.model]
        objs = model_obj.search(domain)
        if objs:
            for action in self.action_ids:
                if action.active is True:
                    method = 'do_%s' % action.ttype
                    if hasattr(self, method):
                        fnc = getattr(self, method)
                        fnc(objs, action)
                    else:
                        _log.error('Unknow action type %s for '
                                   'warning %s' % (action.ttype, self.name))
        else:
            _log.error('Warning "%s" not satisfied conditions' % (self.name))

    @api.one
    def do_send_msg(self, objs, action):
        try:
            for obj in objs:
                if hasattr(obj, 'message_post'):
                    obj.with_context(mail_post_autofollow=False).message_post(
                        body=self.body)
                else:
                    _log.error('%s model don\'t inherit mail.message, '
                               'not message sended.' % self.model_id.model)
            return True
        except Exception as e:
            _log.error('I can\'t to send the message for warning "%s": %s'
                       % (self.name, e))
            return False
