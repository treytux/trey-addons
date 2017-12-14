# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api
import logging
_log = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'

    mailchimp_id = fields.Char(
        string='Mailchimp Identificator',
        readonly=True,
        help="Unique identificator (leid)"
    )

    @api.model
    def create(self, data):
        partner = super(Partner, self).create(data)
        if not partner:
            return partner

        mailch_obj = self.env['mailchimp.config']
        mailchimp_config = mailch_obj.getConfiguration()
        if not mailchimp_config:
            return partner
        else:
            # Comprobar si hay que exportar los datos
            if mailch_obj.checkExportData(partner):
                # Obtener los valores de las lineas de mapeo de la config
                vals = {m.field_mailchimp: data.get(m.field_odoo, '')
                        for m in mailchimp_config.map_line_ids}
                # Crear el suscriptor
                res = mailch_obj.createSubscriptor(data['email'], vals)
                # Guardar el id del registro creado en mailchimp
                partner.mailchimp_id = res['leid']
        return partner

    @api.one
    def write(self, vals):
        # Almacenar el correo antes de guardar por si lo borran
        old_email = self.email
        res = super(Partner, self).write(vals)
        if not res:
            return res
        mailch_obj = self.env['mailchimp.config']
        mailchimp_config = mailch_obj.getConfiguration()
        if not mailchimp_config:
            return res
        else:
            # Obtener los datos
            data_updated = {
                m.field_mailchimp: getattr(self, m.field_odoo)
                for m in mailchimp_config.map_line_ids
                if hasattr(self, m.field_odoo)}

            # Si estaba sincronizado con mailchimp y ahora borran el correo
            # => ELIMINAR
            if self.mailchimp_id and not mailch_obj.checkExportData(self):
                # Eliminar suscriptor
                mailch_obj.deleteSubscriptor(self.mailchimp_id)
                # Borrar el id de mailchimp
                self.write({'mailchimp_id': ''})

            # Si NO estaba sincronizado y ahora añaden correo => CREAR
            elif not self.mailchimp_id and mailch_obj.checkExportData(self):
                # Crear suscriptor
                d = mailch_obj.createSubscriptor(self.email, data_updated)
                # Guardar el id de mailchimp
                self.write({'mailchimp_id': d['leid']})

            # Si estaba sincronizado y ahora cambian datos => ACTUALIZAR
            elif self.mailchimp_id and mailch_obj.checkExportData(self):
                # Si cambian el correo, lo añadimos a los datos a cambiar
                if old_email != self.email:
                    data_updated['new-email'] = self.email

                # Antes de actualizar, comprobamos que el suscriptor existe en
                # mailchimp, es decir, que no lo hayan borrado desde alli, ya
                # que si lo han borrado, habra que crearlo de nuevo.
                if mailch_obj.existLeid(self.mailchimp_id):
                    # Actualizar suscriptor
                    mailch_obj.updateSubscriptor(
                        self.mailchimp_id, data_updated)
                else:
                    # Crear suscriptor
                    mailch_obj.createSubscriptor(self.email, data_updated)
        return res

    @api.multi
    def unlink(self):
        delete_subs = False
        mailch_obj = self.env['mailchimp.config']

        # Guardar el id antes de eliminar el registro
        old_mailchimp_id = self.mailchimp_id

        # Comprobar si hay que exportar los datos
        if mailch_obj.checkExportData(self):
            delete_subs = True

        # Eliminar el partner
        res = super(Partner, self).unlink()

        # Si el partner se ha eliminado correctamente, comprobamos si hay que
        # eliminar el subscriptor. De esta manera, si el partner no se elimina
        # por alguna razon, no eliminamos el subcriptor
        if delete_subs:
            # Eliminar suscriptor
            mailch_obj.deleteSubscriptor(old_mailchimp_id)
        return res
