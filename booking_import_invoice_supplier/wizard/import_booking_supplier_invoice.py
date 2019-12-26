# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api, _, exceptions
import openerp.addons.decimal_precision as dp
import base64
import csv
from tempfile import NamedTemporaryFile
import logging
_log = logging.getLogger(__name__)
try:
    import dateparser
except ImportError:
    _log.debug(_(
        'Module dateparser not installed in server, please install with: '
        'sudo pip install dateparser'))

DATE_FORMAT = "%d/%m/%Y"


def to_integer(num):
    try:
        res = int(num)
    except Exception as e:
        _log.warn(_(
            'Error to convert %s to integer; error: %s. It is returned 0.' % (
                num, e)))
        res = 0
    return res


def to_float(num):
    try:
        num = str(num).replace('.', '')
        num = num.replace(',', '.')
        res = float(num)
    except Exception as e:
        _log.warn(_(
            'Error to convert %s to float; error: %s. It is returned 0.' % (
                num, e)))
        res = 0
    return res


def cls_string(string):
    try:
        res = string.strip()
    except Exception as e:
        _log.warn(_(
            'Error clean string %s; error: %s. It is returned ''.' % (
                string, e)))
        res = ''
    return res


def _reopen(self, res_id, model, title):
    return {
        'name': title or _('Import Invoice'),
        'type': 'ir.actions.act_window',
        'view_mode': 'form',
        'view_type': 'form',
        'res_id': res_id,
        'res_model': self._name,
        'target': 'new',
        'context': {
            'default_model': model}}


class WizBookingSupplierInvoice(models.TransientModel):
    _name = 'wiz.booking.supplier.invoice'
    _description = 'Import Invoice Supplier'

    name = fields.Char(
        string='Empty')
    ffile = fields.Binary(
        string='File csv',
        filters='*.csv',
        required=True)
    invoice_new_ids = fields.One2many(
        comodel_name='wiz.booking.supplier.invoice.linenew',
        inverse_name='wizard_id',
        string="New Invoice",
        required=False,
        readonly=True)
    invoice_unknown_ids = fields.One2many(
        comodel_name='wiz.booking.supplier.invoice.unknown',
        inverse_name='wizard_id',
        string="Unknown Invoice",
        required=False,
        readonly=True)
    read_lines = fields.Integer(
        string='Read lines',
        readonly=True)
    state = fields.Selection(
        string='State',
        selection=[
            ('step1', 'Step1'),
            ('step2', 'Step2'),
            ('done', 'Done')],
        required=True,
        default='step1')

    @api.model
    def get_partner_id(self, name, vat):
        """
        ----------------------------------------------------------------------
        Buscar proveedor
        ----------------------------------------------------------------------
        :param name: Nombre del proveedor
        :param vat: CIF del proveedor
        ----------------------------------------------------------------------
        :return: El objeto partner
        ----------------------------------------------------------------------
        """
        partners = self.env['res.partner'].search([('name', 'ilike', name)])
        if not partners:
            partners = self.env['res.partner'].search([('vat', '=', vat)])
            if not partners:
                partner_id = None
                _log.warn(
                    _('The partner \'%s\' does not exist in the system, '
                      'it is not assigned.' % name))
        else:
            partner_id = partners[0].id
        return partner_id

    @api.model
    def get_booking_id(self, booking, ex_reference):
        """
        ----------------------------------------------------------------------
        Buscar la reserva en el sistema
        ----------------------------------------------------------------------
        :param booking: Codigo de la reserva
        :param ex_reference: Referencia del proveedor para la reserva
        ----------------------------------------------------------------------
        :return: Objeto reserva
        ----------------------------------------------------------------------
        """
        booking_line_id = None
        booking_lines = self.env['booking.line'].search([
            ('booking_code', '=', booking)])
        if not booking_lines:
            booking_lines = self.env['booking.line'].search([
                ('ex_reference', '=', ex_reference)])
            if not booking_lines:
                _log.warn(
                    _('The booking \'%s\' does not exist in the system, '
                      'it is not assigned.' % booking))
        else:
            booking_line_id = booking_lines[0].id
        return booking_line_id

    @api.model
    def get_currency_id(self, currency):
        """
        ----------------------------------------------------------------------
        Busca el objeto moneda
        ----------------------------------------------------------------------
        :param currency: Nombre ISO de la divisa
        ----------------------------------------------------------------------
        :return: Objeto moneda
        ----------------------------------------------------------------------
        """
        currencys = self.env['res.currency'].search([('name', '=', currency)])
        if not currencys:
            currency_id = None
            _log.warn(
                _('The booking \'%s\' does not exist in the system, '
                  'it is not assigned.' % currency))
        else:
            currency_id = currencys[0].id
        return currency_id

    @api.multi
    def back_step1(self):
        self.ensure_one()
        if self.invoice_new_ids:
            for line in self.invoice_new_ids:
                line.unlink()
        if self.invoice_unknown_ids:
            for line in self.invoice_unknown_ids:
                line.unlink()
        self.write({'state': 'step1'})
        return _reopen(self, self.id, 'wiz.booking.supplier.invoice',
                       title=_('Import Invoice Step1'))

    @api.multi
    def read_file_lines(self, data, header):
        """
        Read invoice lines of the file and create the lines classified by
        types (new, unknown).
       """
        try:
            isupplier = header.index('proveedor')
            ivat = header.index('cif')
            idate = header.index('fecha factura')
            iname = header.index('loc.')
            iex_reference = header.index('loc. ext.')
            idate_init = header.index('inicio')
            idate_end = header.index('fin')
            isupplier_invoice_number = header.index('factura')
            iamount_total = header.index('precio')
            icurrency = header.index('moneda')
        except Exception as e:
                raise exceptions.Warning('%s' % e)
        # Leemos los registros de datos y clasificamos la salida.
        for invoice in data:
            partner_id = self.get_partner_id(
                cls_string(invoice[isupplier]), cls_string(invoice[ivat]))
            if not partner_id:
                raise exceptions.Warning(
                    _('The supplier "%s" with VAT %s don\'t exists. Please '
                      'create a partner with this info') % (
                        invoice[isupplier], invoice[ivat]))
            booking_line_id = self.get_booking_id(
                cls_string(invoice[iname]), cls_string(invoice[iex_reference]))
            currency_id = self.get_currency_id(cls_string(invoice[icurrency]))
            date = dateparser.parse(invoice[idate])
            date_init = dateparser.parse(invoice[idate_init])
            date_end = dateparser.parse(invoice[idate_end])
            data = {
                'name': invoice[iname],
                'supplier_id': partner_id,
                'vat': cls_string(invoice[ivat]),
                'date': date,
                'date_init': date_init,
                'date_end': date_end,
                'supplier_invoice_number':
                    cls_string(invoice[isupplier_invoice_number]) or '',
                'amount_total': to_float(invoice[iamount_total]),
                'check_total': to_float(invoice[iamount_total]),
                'currency_id': currency_id,
                'ex_reference': cls_string(invoice[iex_reference]),
                'booking_line_id': booking_line_id,
                'wizard_id': self.id}
            _log.info('=' * 79)
            _log.info('Datos invoice: %s' % invoice)
            _log.info('=' * 79)
            if partner_id and booking_line_id and currency_id:
                self.env['wiz.booking.supplier.invoice.linenew'].create(data)
            else:
                self.env['wiz.booking.supplier.invoice.unknown'].create(data)
        return True

    @api.multi
    def button_import(self):
        """Imports the file and creates the lines of the wizard."""
        self.ensure_one()
        if self.ffile:
            # ***************************************************************
            # Save file in temporal folder for backup an sniffer csv format
            # ***************************************************************
            file_obj = NamedTemporaryFile(
                'w+', suffix='.csv', delete=False)
            file_obj.write(base64.decodestring(self.ffile))
            path = file_obj.name
            file_obj.close()
            # Open file
            csvfile = open(path, "rb")
            dialect = csv.Sniffer().sniff(csvfile.read(10 * 1024))
            csvfile.seek(0)
            # Reads file lines and creates wizard lines
            reader = csv.reader(
                csvfile, delimiter=';', quotechar='"', dialect=dialect)
            # Reads file lines and creates wizard lines
            header = reader.next()
            # Change columns to lowercase
            header = [x.lower() for x in header]
            data = [row for row in reader]
            csvfile.close()
            self.read_file_lines(data, header)
        self.write({'state': 'step2'})
        return _reopen(self, self.id, 'wiz.booking.supplier.invoice',
                       title=_('Import Invoice Step2'))

    @api.multi
    def button_create(self):
        """
        Depending on which option is selected: create or update, it will
        create or it will update the following models:
            - Invoice type supplier
        """
        self.ensure_one()
        active_ids = []
        for invoice in self.invoice_new_ids:
            # TODO: Aqui grabo el numero de factura de proveedor
            invoice.booking_line_id.supplier_invoice_number = \
                invoice.supplier_invoice_number
            active_ids.append(invoice.booking_line_id.id)
        context = self.env.context.copy()
        context['active_ids'] = active_ids
        context['default_model'] = 'booking.supplier.invoice'
        return {
            'name': _("Generate Supplier Invoice"),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'booking.supplier.invoice',
            'target': 'new',
            'context': context,
            'nodestroy': True}


class WizBookingSupplierInvoiceLineNew(models.TransientModel):
    _name = 'wiz.booking.supplier.invoice.linenew'

    name = fields.Char(
        string='Booking')
    wizard_id = fields.Many2one(
        comodel_name='wiz.booking.supplier.invoice',
        string='Import Invoice Supplier',
        required=False)
    booking_line_id = fields.Many2one(
        comodel_name='booking.line',
        string="Booking Line",
        required=True)
    booking_code = fields.Char(
        related='booking_line_id.booking_code',
        select=True)
    supplier_id = fields.Many2one(
        comodel_name='res.partner',
        string='Supplier',
        required=True)
    vat = fields.Char(
        string='TIN',
        help="Tax Identification Number. Check the box if this contact is "
             "subjected to taxes. Used by the some of the legal statements.")
    date = fields.Date(
        string="Date",
        required=False)
    ex_reference = fields.Char(
        string='External Ref.',
        required=False)
    date_init = fields.Date(
        string='Begin Travel',
        required=False)
    date_end = fields.Date(
        string='End Travel',
        required=False)
    supplier_invoice_number = fields.Char(
        string='Supplier Invoice Number',
        help="The reference of this invoice as provided by the supplier.")
    amount_total = fields.Float(
        string='Total',
        digits=dp.get_precision('Account'))
    check_total = fields.Float(
        string='Verification Total',
        digits=dp.get_precision('Account'))
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True)


class WizBookingSupplierInvoiceLineUnknown(models.TransientModel):
    _name = 'wiz.booking.supplier.invoice.unknown'

    name = fields.Char(
        string='Booking')
    wizard_id = fields.Many2one(
        comodel_name='wiz.booking.supplier.invoice',
        string='Import Invoice Supplier',
        required=False)
    booking_line_id = fields.Many2one(
        comodel_name='booking.line',
        string="Booking Line",
        required=False)
    supplier_id = fields.Many2one(
        comodel_name='res.partner',
        string='Supplier',
        required=True)
    vat = fields.Char(
        string='TIN',
        help="Tax Identification Number. Check the box if this contact is "
             "subjected to taxes. Used by the some of the legal statements.")
    date = fields.Date(
        string="Date",
        required=False)
    ex_reference = fields.Char(
        string='External Ref.',
        required=False)
    date_init = fields.Date(
        string='Begin Travel',
        required=False)
    date_end = fields.Date(
        string='End Travel',
        required=False)
    supplier_invoice_number = fields.Char(
        string='Supplier Invoice Number',
        help="The reference of this invoice as provided by the supplier.")
    amount_total = fields.Float(
        string='Total',
        digits=dp.get_precision('Account'))
    check_total = fields.Float(
        string='Verification Total',
        digits=dp.get_precision('Account'))
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=False)
