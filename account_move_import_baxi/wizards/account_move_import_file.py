###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import io
import logging
from datetime import datetime

from odoo import _, exceptions, fields, models

_log = logging.getLogger(__name__)

try:
    import pandas as pd
except ImportError:
    _log.debug('You need to install pandas library')

try:
    import vatnumber
except ImportError:
    _log.debug('You need to install vatnumber library')
    vatnumber = None


class AccountMoveImportFile(models.TransientModel):
    _inherit = 'account.move.import_file'

    type = fields.Selection(
        selection_add=[
            ('baxi', 'Baxi'),
        ],
        default='baxi',
        ondelete={
            'baxi': 'set default',
        },
    )

    def _import_file(self):
        self.ensure_one()
        if self.type == 'baxi':
            return self._import_file_baxi()
        return super()._import_file()

    def _get_baxi_payments(self):
        payments = self.env['account.payment.mode'].search(
            [('baxi_name', '!=', False)])
        baxi_payments = {}
        for payment in payments:
            for name in payment.baxi_name.split(','):
                baxi_payments[name.strip()] = payment.id
        return baxi_payments

    def _import_file_baxi(self):
        self.ensure_one()
        buf = io.BytesIO()
        buf.write(base64.b64decode(self.file))
        buf.seek(0)
        try:
            df = pd.read_excel(buf)
        except Exception:
            buf.seek(0)
            df = pd.read_html(
                buf, decimal=',', thousands='.')[0]
        df.columns = [col.replace(': ', ':') for col in df.columns]
        col_aliases = {
            'DOCD_TOTAL': 'DOCF_TOTAL',
        }
        df.rename(columns=col_aliases, inplace=True)
        payment_modes = self._get_baxi_payments()
        product = self.env.ref(
            'account_move_import_baxi.baxi_product')
        baxi_journals = self.env['account.journal'].browse(
            self._context.get('active_ids', []))
        journal = baxi_journals[:1]
        moves = self.env['account.move'].browse()
        for index, row in df.iterrows():
            _log.info('[%s/%s] import invoice %s' % (
                index + 1, len(df), row['DOCF_NUMFACTURA']))
            move = self._import_invoice(
                row, payment_modes, product, journal)
            if move:
                moves |= move
        return moves

    def _import_invoice(self, row, payment_modes, product, journal):
        move = self.env['account.move'].search([
            ('name', '=', row['DOCF_NUMFACTURA']),
        ])
        if move:
            _log.info('Ignore %s already exists' % row['DOCF_NUMFACTURA'])
            return self.env['account.move']
        partner = self._partner_search_or_create(row)
        if not partner.vat and journal.simplified_journal_id:
            journal = journal.simplified_journal_id
        product.product_tmpl_id._get_product_accounts()['income']
        if row['PAGO'] not in payment_modes:
            raise exceptions.UserError(_(
                'Payment mode with Baxi name "%s" not defined. Please go to '
                'payment modes and fill a payment mode with this name in '
                '"Baxi name" field') % row['PAGO'])
        paid = row.get('Fact cobrada', '').lower().startswith('s')
        move_type = (
            'out_refund'
            if row.get('TipoDesc') == 'RECTIFICACIÓN'
            else 'out_invoice')
        move = self.env['account.move'].create({
            'move_type': move_type,
            'name': row['DOCF_NUMFACTURA'],
            'ref': row.get('PAGO', ''),
            'invoice_date': datetime.strptime(
                row['DOCF_FECHA'], '%d/%m/%Y %H:%M:%S').date(),
            'journal_id': journal.id,
            'partner_id': partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'name': row.get('DOCF_DESCRIP', ''),
                'quantity': 1,
                'price_unit': row['DOCF_SUBTOTAL'],
                'tax_ids': [(6, 0, [])],
            })],
        })
        if move.amount_total != row.get('DOCF_TOTAL', 0.0):
            move.message_post(body=_(
                'Invoice %s with differents totals between Baxi XLS '
                'file (%.2f €) and Odoo (%.2f €), operation canceled!') % (
                move.name, row['DOCF_TOTAL'], move.amount_total))
            move.state = 'cancel'
            return move
        move.action_post()
        if paid:
            self._register_payment(move, row.get('Recibo Id', ''))
        return move

    def _register_payment(self, move, ref):
        payment_mode = self.env['account.payment.mode'].browse(
            move.payment_mode_id.id) if move.payment_mode_id else False
        if not payment_mode:
            return
        journal = (
            payment_mode.fixed_journal_id
            if payment_mode.bank_account_link == 'fixed'
            else payment_mode.variable_journal_ids[:1]
        )
        payment = self.env['account.payment'].create({
            'date': move.invoice_date,
            'partner_id': move.partner_id.id,
            'partner_type': 'customer',
            'payment_type': 'inbound',
            'amount': move.amount_total,
            'payment_method_id': payment_mode.payment_method_id.id,
            'ref': '[%s] %s (%s)' % (
                ref, move.name, move.ref),
            'journal_id': journal.id,
            'reconciled_invoice_ids': [(6, 0, move.ids)],
        })
        payment.action_post()
        payment.message_post_with_view(
            'mail.message_origin_link',
            values={'self': payment, 'origin': self},
            subtype_id=self.env.ref('mail.mt_note').id,
        )

    def _partner_search_or_create(self, row):
        vat = (
            row['CLIENTE:DNI'] if isinstance(row['CLIENTE:DNI'], str)
            else False)
        if vat:
            vat = vat if vat.startswith('ES') else 'ES%s' % vat
            partner = self.env['res.partner'].search([
                ('parent_id', '=', False),
                ('vat', '=', vat),
            ])
            if not partner:
                partner = self.env['res.partner'].search([
                    ('comment', 'ilike', vat),
                ])
            if partner:
                if len(partner) > 1:
                    raise exceptions.UserError(_(
                        'More than one partner found for VAT: \'%s\'') %
                        row['CLIENTE:DNI'])
                return partner
        try:
            city_zip = self.env['res.city.zip'].search([
                ('name', '=', row['CLIENTE:CP'])], limit=1)
        except KeyError:
            city_zip = False
        return self.env['res.partner'].create({
            'name': row['CLIENTE'],
            'vat': vat if vat else False,
            'comment': (
                ('VAT not valid: %s') % vat
                if vat and vatnumber and not vatnumber.check_vat(vat) else False
            ),
            'street': row['CLIENTE:DIRECCION'],
            'city': (
                city_zip.city_id.name
                if city_zip else row.get('CLIENTE:POBLACION', '')
            ),
            'country_id': (
                city_zip.city_id.country_id.id if city_zip else False),
            'state_id': city_zip.city_id.state_id.id if city_zip else False,
            'zip': city_zip.name if city_zip else False,
        })
