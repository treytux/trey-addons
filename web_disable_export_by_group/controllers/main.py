# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import http
from openerp.http import request


class WebDisableExportByGroup(http.Controller):

    @http.route('/web/export/user_allowed', type='json', auth="user")
    def user_allowed(self, model):
        '''If current user belong to the 'Allow export' group, return True.'''
        cr, uid, context = request.env.args
        user = request.env['res.users'].browse(uid)
        user_allowed = False
        allow_group_model, allow_group_id = request.env[
            'ir.model.data'].get_object_reference(
                'web_disable_export_by_group', 'group_allow_export')
        if allow_group_id in user.groups_id.ids:
            user_allowed = True
        return user_allowed
