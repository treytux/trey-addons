# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
# For ignore PEP8 error for self undefined, this script is for odoo shell
if 'self' not in globals():
    self = None

model = self.env['res.partner']
self.env.add_todo(model._fields['display_name'], model.search([]))
model.recompute()
self.commit()
