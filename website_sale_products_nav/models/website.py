# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models


class Website(models.Model):
    _inherit = 'website'

    @api.multi
    def pager(self, url, total, page=1, step=30, scope=5, url_args=None):
        res = super(Website, self).pager(
            url, total, page=page, step=step, scope=scope, url_args=url_args)
        res['total'] = int(total)
        return res
