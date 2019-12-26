# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.osv import orm, fields


class ResPartner(orm.Model):
    _inherit = 'res.partner'

    def _display_name_compute(self, cr, uid, ids, *args, **kwargs):
        context = kwargs.get('context')
        return dict(self.name_get(cr, uid, ids, context=context))

    _display_name_store_triggers = {
        'res.partner': (
            lambda self, cr, uid, ids, context=None:
            self.search(cr, uid, [('id', 'child_of', ids)]),
            ['parent_id', 'is_company', 'name', 'comercial'], 10)
    }

    _columns = {
        'display_name': fields.function(
            _display_name_compute,
            type='char',
            string='Name',
            store=_display_name_store_triggers
        ),
    }
