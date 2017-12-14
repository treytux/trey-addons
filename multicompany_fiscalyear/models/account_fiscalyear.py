# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2014-Today Trey, Kilobytes de Soluciones <www.trey.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
###############################################################################
from openerp import models, api


class AccountFiscalYear(models.Model):
    _inherit = 'account.fiscalyear'

    @api.multi
    def name_get(self):
        if isinstance(self.ids, (list, tuple)) and not len(self.ids):
            return []
        result = []

        for fiscalyear in self:
            name = "%s-%s" % (fiscalyear.name,
                              fiscalyear.company_id.name or '')
            result.append((fiscalyear.id, " %s" % (name or '')))
        return result


class AccountPeriod(models.Model):
    _inherit = 'account.period'

    @api.multi
    def name_get(self):
        if isinstance(self.ids, (list, tuple)) and not len(self.ids):
            return []
        result = []
        for period in self:
            name = "%s-%s" % (period.name,
                              period.company_id.name or '')
            result.append((period.id, " %s" % (name or '')))
        return result
