# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _


class EdifactDocument(models.Model):
    _inherit = 'edifact.document'

    voucher_ids = fields.One2many(
        comodel_name='account.voucher',
        inverse_name='edi_doc_id',
        string='Vouchers')

    @api.multi
    def get_voucher_vals(self, partner_id, amount, reference, journal_id, date,
                         currency_id, account_id, edi_doc_id):
        voucher_vals = {
            'partner_id': partner_id,
            'amount': amount,
            'reference': reference,
            'journal_id': journal_id,
            'date': date,
            'type': 'receipt',
            'currency_id': currency_id,
            'account_id': account_id,
            'edi_doc_id': edi_doc_id}
        return voucher_vals

    @api.multi
    def get_ref(self, unh):
        for rff in unh.get('RFF'):
            if rff.get('C506.1153') == 'AEK':
                return rff.get('C506.1154')
        return None

    @api.multi
    def get_payment_date(self, unh):
        for dtm in unh.get('DTM'):
            if dtm.get('C507.2005') == '227':
                return dtm.get('C507.2380')
        return None

    @api.multi
    def get_partner_ean(self, unh):
        for partner in unh.get('NAD'):
            if partner.get('3035') == 'MS':
                return partner.get('C082.3039')
        return None

    @api.multi
    def create_draft_voucher(self, unh, amount_payed, ref, payment_date,
                             currency_id, edi_doc_id):
        voucher_obj = self.env['account.voucher']
        ean13 = self.get_partner_ean(unh)
        if ean13:
            partner = self.env['res.partner'].search(
                [('ean13', '=', ean13)])
        if not partner:
            return None
        partner_id = self.env[
            'res.partner']._find_accounting_partner(
                partner).id
        res_account = voucher_obj.basic_onchange_partner(
            partner[0].id, self.env.ref(
                '__export__.account_journal_8').id, 'receipt')
        voucher_vals = self.get_voucher_vals(
            partner_id=partner_id,
            amount=amount_payed,
            reference=ref,
            journal_id=self.env.ref(
                '__export__.account_journal_8').id,
            date=payment_date,
            currency_id=currency_id,
            account_id=res_account['value']['account_id'],
            edi_doc_id=edi_doc_id)
        voucher = voucher_obj.create(voucher_vals)
        return voucher

    @api.multi
    def pay_invoice(self, inv, amount_payed, ref, payment_date, currency_id,
                    edi_doc_id):
        voucher_obj = self.env['account.voucher']
        partner_id = self.env[
            'res.partner']._find_accounting_partner(
                inv.partner_id).id
        res_account = voucher_obj.basic_onchange_partner(
            partner_id, self.env.ref(
                '__export__.account_journal_8').id, 'receipt')
        voucher_vals = self.get_voucher_vals(
            partner_id=partner_id,
            amount=amount_payed,
            reference=ref,
            journal_id=self.env.ref(
                '__export__.account_journal_8').id,
            date=payment_date,
            currency_id=currency_id,
            account_id=res_account['value']['account_id'],
            edi_doc_id=edi_doc_id)
        voucher = voucher_obj.create(voucher_vals)
        ctx = dict(self.env.context)
        move_lines = self.env['account.move.line'].search(
            [('invoice', '=', inv.id), ('account_id.type', '=', 'receivable')])
        ctx.update({
            'invoice_id': inv.id,
            'move_line_ids': [l.id for l in move_lines]})
        res = voucher.with_context(ctx).onchange_amount(
            amount=voucher.amount,
            rate=voucher.payment_rate,
            partner_id=voucher.partner_id.id,
            journal_id=voucher.journal_id.id,
            currency_id=voucher.currency_id.id,
            ttype=voucher.type,
            date=voucher.date,
            payment_rate_currency_id=voucher.currency_id.id,
            company_id=voucher.company_id.id)
        ctx.update(res['value'])
        lines = [(0, 0, l) for l in ctx['line_cr_ids']]
        voucher.line_cr_ids = lines
        voucher.with_context(ctx).proforma_voucher()
        return voucher

    @api.multi
    def process_voucher_in_files(self):
        fact_obj = self.env['account.invoice']
        files = self.read_in_files('vouchers')
        data_dict_list = []
        edi_doc = False
        for file in files:
            edi_doc_exist = False
            data_dict_list = self.read_from_file(file)
            for data_dict in data_dict_list:
                unh = data_dict.get('UNH', {})
                ref = self.get_ref(unh)
                payment_date = self.get_payment_date(unh)
                for doc in unh.get('DOC'):
                    inv_name = doc.get('C503.1004')
                    edi_doc_exist = self.search(
                        [('name', '=', inv_name), ('ttype', '=', 'voucher')])
                    if edi_doc_exist:
                        self.move_file_to_duplicated(file)
                        break
                    edi_doc = self.create({
                        'name': inv_name,
                        'ttype': 'voucher',
                        'import_log': ''})
                    inv = fact_obj.search([('number', 'ilike', inv_name)])
                    if not inv:
                        raise exceptions.Warning(
                            _('ERROR: No invoice %s found: file %s - message'
                              '%s') % (inv_name, file, unh.get('0062')))
                    elif inv.state == 'paid':
                        raise exceptions.Warning(
                            _('ERROR: Invoice %s is already paid. File: %s - ')
                            % (inv_name, file))
                    moa = doc.get('MOA')
                    for moa in doc.get('MOA'):
                        amount_payed = float(moa.get('C516.5004'))
                        currency_code = moa.get('C516.6345')
                        currency = self.env['res.currency'].search([(
                            'name', '=', currency_code)])
                        # Only if they want to create a draft voucher when
                        # no invoice found -> uncomment and comment inv raise.
                        # if not inv:
                        #     edi_doc.import_log = '\n'.join(
                        #         [edi_doc.import_log,
                        #          _('No invoice %s found: file %s - message'
                        #          ' %s')
                        #          % (inv_name, file, unh.get('0062'))])
                        #     edi_doc.state = 'error'
                        #     voucher = self.create_draft_voucher(
                        #         unh=unh,
                        #         amount_payed=amount_payed,
                        #         ref=ref,
                        #         payment_date=payment_date,
                        #         currency_id=currency.id,
                        #         edi_doc_id=edi_doc.id)
                        #     if not voucher:
                        #         edi_doc.import_log = '\n'.join(
                        #             [edi_doc.import_log,
                        #              _('No partner found for message: %s')
                        #              % unh.get('0062')])
                        #         raise exceptions.Warning(
                        #             _('ERROR: No client found: file %s - '
                        #               'message %s')
                        #             % (file, unh.get('0062')))
                        #     continue
                        self.pay_invoice(
                            inv=inv,
                            amount_payed=amount_payed,
                            ref=ref,
                            payment_date=payment_date,
                            currency_id=currency.id,
                            edi_doc_id=edi_doc.id)
                        edi_doc.import_log = '\n'.join(
                            [edi_doc.import_log, 'OK: %s' % inv_name])
                        edi_doc.state = 'imported'
                        edi_doc.file_name = file
        files = self.read_in_files('vouchers')
        for file in files:
            self.delete_file(file)
        return edi_doc

    @api.model
    def cron_process_voucher_files(self):
        res = self.process_voucher_in_files()
        return res
