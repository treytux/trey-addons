# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, fields, _, exceptions
import logging
_log = logging.getLogger(__name__)


class WarningMessaging(models.Model):
    _inherit = 'warning.messaging'

    @api.multi
    def send_mail_without_template(self, email_to, action):
        """ Send a mail without template to email address indicated in
        'email_to' with action values."""
        cr, uid, context = self.env.args

        # 1 - Crear objeto mail.message (mail_message_id)
        email_from = self.env['ir.mail_server'].search(
            [('active', '=', True)])
        if not email_from:
            raise exceptions.Warning(_(
                'Not exist any mail in active state, the email can not sent.'))

        data_msg = {
            'subject': action.email_subject or '',
            'type': 'email',
            'email_from': email_from.smtp_user,
            'attachment_ids': [(6, 0, [attach.id for attach in
                                action.email_attachment_ids])]
        }
        mail_message = self.env['mail.message'].create(data_msg)

        # 2 - Crear objeto mail.mail (mail_id) y asignarle el mail_message_id
        mail_mail = self.env['mail.mail']
        data_mail = {
            'mail_message_id': mail_message.id,
            'body_html': action.email_body_html or '',
            'email_to': email_to
        }
        mail = mail_mail.create(data_mail)

        # 3 - Llamar a funcion send con ids = mail.id
        # Hay que llamar a send con la api antigua
        self.pool.get('mail.mail').send(cr, uid, [mail.id])

        return True

    @api.one
    def do_send_email_without_templ(self, objs, action):
        """ Send a email without template with action values."""
        try:
            for obj in objs:
                if hasattr(obj, 'message_post'):
                    email_to = obj.partner_id and obj.partner_id.email\
                        or None
                    # Enviar correo
                    self.send_mail_without_template(email_to, action)

                    # Notificar en el registro que se ha enviado el
                    # correo
                    partner_ids = [
                        obj.user_id and obj.user_id.partner_id and
                        obj.user_id.partner_id.id] or []
                    body = _('Mail sent to partner from warning \'%s\'.'
                             % self.name)
                    obj.with_context(
                        mail_post_autofollow=False).message_post(
                        body=body, partner_ids=partner_ids)
                else:
                    _log.error('%s model don\'t inherit mail.message, '
                               'not message sended.' % self.model_id.model)
            return True
        except Exception as e:
            _log.error('I can\'t to send the message for warning "%s": %s'
                       % (self.name, e))
            return False

    @api.one
    def do_send_email_with_templ(self, objs, action):
        """ Send a email with template defined in action."""
        try:
            for obj in objs:
                if hasattr(obj, 'message_post'):
                    # Para que funcione el envio de correos, la llamada
                    # debe ser con la antigua api
                    cr, uid, context = self.env.args
                    self.pool.get('email.template').send_mail(
                        cr, uid, action.email_tmpl_id.id, obj.id,
                        force_send=True, raise_exception=True,
                        context=context)

                    # Notificar en el registro que se ha enviado el
                    # correo
                    partner_ids = [
                        obj.user_id and obj.user_id.partner_id and
                        obj.user_id.partner_id.id] or []
                    body = _('Mail sent to partner from warning \'%s\'.'
                             % self.name)
                    obj.with_context(
                        mail_post_autofollow=False).message_post(
                        body=body, partner_ids=partner_ids)
                else:
                    _log.error('%s model don\'t inherit mail.message, '
                               'not message sended.' % self.model_id.model)
            return True
        except Exception as e:
            _log.error('I can\'t to send the message for warning "%s": %s'
                       % (self.name, e))
            return False


class WarningAction(models.Model):
    _inherit = 'warning.action'

    email_tmpl_id = fields.Many2one(
        comodel_name='email.template',
        string='Email Template')
    email_subject = fields.Char(
        string='Email subject')
    email_body_html = fields.Char(
        string='Email body html')
    email_attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        relation='warning_mess_attach_rel',
        column1='warning_mess_id',
        column2='attachment_id')

    @api.model
    def _setup_fields(self):
        """Anadir valores a campo selection."""
        res = super(WarningAction, self)._setup_fields()

        options = [
            ('send_email_with_templ', 'Send email with template'),
            ('send_email_without_templ', 'Send email without template')
        ]
        for option in options:
            if 'ttype' in self._fields and \
               option not in self._fields['ttype'].selection:
                    self._fields['ttype'].selection.append(option)
        return res

    @api.model
    def create(self, data):
        # Si la accion es de tipo correo con plantilla, comprobar que el
        # modelo de la plantilla coincide con el modelo del aviso
        if 'ttype' in data and data['ttype'] == 'send_email_with_templ':
            # Comprobar si la accion tiene asignada plantilla.
            # Si es asi, obtener el modelo de la accion y comprararlo con el
            # modelo del aviso
            if 'email_tmpl_id' in data and 'warning_id' in data:
                email_tmpl = self.env['email.template'].browse(
                    data['email_tmpl_id'])
                warning_msg = self.env['warning.messaging'].browse(
                    data['warning_id'])
                if email_tmpl.model_id != warning_msg.model_id:
                    raise exceptions.Warning(
                        _('You must select an email template with the same '
                          'model of the current warning.'))
        return super(WarningAction, self).create(data)

    @api.multi
    def write(self, vals):
        res = super(WarningAction, self).write(vals)
        if not res:
            return res
        else:
            # Si la accion es de tipo correo con plantilla, comprobar que el
            # modelo de la plantilla coincide con el modelo del aviso
            if self.ttype == 'send_email_with_templ' and\
               self.email_tmpl_id.model_id != self.warning_id.model_id:
                raise exceptions.Warning(
                    _('You must select an email template with the same model '
                      'of the current warning.'))
