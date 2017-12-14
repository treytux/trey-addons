# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import http
from openerp.http import request
import werkzeug.utils
import logging
_log = logging.getLogger(__name__)


class Home(http.Controller):

    @http.route('/web/activate', type='http', auth="none")
    def web_activate(self, redirect=None, email=None, **kw):
        env = request.env
        # Comprobar si hay algun partner con este correo en el sistema
        partners = env['res.partner'].sudo().search([('email', '=', email)])
        if not partners.exists():
            # No existe ninguna empresa ni contacto con este correo
            # Derivar a otra pagina?
            return None

        # Si existe el partner, hay que comprobar si existe ya el usuario
        # registrado con este correo
        users = env['res.users'].sudo().search([('login', '=', email)])
        if users.exists():
            # Ya existe el usuario registrado
            # Derivar a otra pagina?
            return None

        # Crear un usuario copia de del usuario publico
        user_model, user_id = env['ir.model.data'].get_object_reference(
            'base', 'public_user')
        public_user = env['res.users'].browse(user_id)
        public_user.sudo().copy({
            'active': True,
            'login': email,
            'partner_id': partners[0].id})
        if redirect is not None:
            return werkzeug.utils.redirect('%s' % redirect)
        else:
            return werkzeug.utils.redirect('/')
