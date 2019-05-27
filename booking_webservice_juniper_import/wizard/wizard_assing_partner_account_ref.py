# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _
import base64
import logging
_log = logging.getLogger(__name__)


try:
    import xlrd
except ImportError:
    _log.debug(_(
        'Library xlrd not installed. Install it with: sudo pip install xlrd'))
    xlrd = None


class WizardAssingPartnerAccountRef(models.TransientModel):
    _name = 'wizard.assing.partner.account.ref'

    name = fields.Char(
        string='name')
    ffile = fields.Binary(
        string='File xml',
        filters='*.xml',
        required=True)

    @api.multi
    def assing_partner_account_ref(self, ffile):
        if not self.ffile:
            return False
        book = xlrd.open_workbook(file_contents=ffile)
        sheet = book.sheet_by_index(0)
        partner_obj = self.env['res.partner']
        for rx in range(sheet.nrows):
            juniper_partner_account = int(sheet.cell_value(rowx=rx, colx=0))
            iboosy_partner_account = int(sheet.cell_value(rowx=rx, colx=1))
            customer = partner_obj.search([
                ('customer_account_ref_methabook', '=',
                 iboosy_partner_account)])
            if len(customer) > 1:
                raise exceptions.Warning(
                    _('account %s is assinged to %s customers' % (
                        iboosy_partner_account, len(customer))))
            if customer:
                customer.customer_account_ref = juniper_partner_account
                if not customer.customer:
                    customer.customer = True
            supplier = partner_obj.search([
                ('supplier_account_ref_methabook',
                 '=', iboosy_partner_account)])
            if supplier:
                if len(supplier) > 1:
                    raise exceptions.Warning(
                        _('account %s is assinged to %s suppliers' % (
                            iboosy_partner_account, len(supplier))))
                supplier.supplier_account_ref = juniper_partner_account
                if not supplier.supplier:
                    supplier.supplier = True

    @api.multi
    def button_ok(self):
        active_id = self.env.context.get('active_id', False)
        if not active_id:
            return
        webservice_id = self.env['booking.webservice'].browse(active_id)
        if not webservice_id.type == 'juniper':
            return
        if self.ffile:
            try:
                ffile = base64.decodestring(self.ffile)
                self.assing_partner_account_ref(ffile)
            except Exception as e:
                raise exceptions.Warning(_(
                    'It has occurred following error: %s.' % e))
