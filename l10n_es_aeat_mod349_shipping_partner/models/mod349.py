###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import math

from odoo import models
from odoo.fields import first
from odoo.tools import float_is_zero


class Mod349(models.Model):
    _inherit = 'l10n.es.aeat.mod349.report'

    def _get_349_partner_from_move_line(self, move_line):
        shipping_partner = move_line.move_id.partner_shipping_id
        return shipping_partner or move_line.partner_id

    def _create_349_invoice_records(self):
        rec_obj = self.env['l10n.es.aeat.mod349.partner_record']
        detail_obj = self.env['l10n.es.aeat.mod349.partner_record_detail']
        data = {}
        for record_detail in self.partner_record_detail_ids:
            move_line = record_detail.move_line_id
            partner = self._get_349_partner_from_move_line(move_line)
            op_key = move_line.l10n_es_aeat_349_operation_key
            partner_dict = data.setdefault(partner, {})
            op_key_dict = partner_dict.setdefault(
                op_key, {'record_details': detail_obj})
            op_key_dict['record_details'] += record_detail
        for partner in list(data.keys()):
            for op_key in list(data[partner].keys()):
                record_created = rec_obj.create({
                    'report_id': self.id,
                    'partner_id': partner.id,
                    'partner_vat': partner.vat,
                    'operation_key': op_key,
                    'country_id': partner.country_id.id,
                })
                for record_detail in data[partner][op_key]['record_details']:
                    record_detail.partner_record_id = record_created
        rounding = self.env.company.currency_id.rounding
        self.partner_record_ids.filtered(
            lambda r: float_is_zero(
                r.total_operation_amount, precision_rounding=rounding
            )).unlink()
        return True

    def _create_349_refund_records(self):
        self.ensure_one()
        detail_obj = self.env['l10n.es.aeat.mod349.partner_record_detail']
        obj = self.env['l10n.es.aeat.mod349.partner_refund']
        refund_detail_obj = self.env[
            'l10n.es.aeat.mod349.partner_refund_detail']
        move_line_obj = self.env['account.move.line']
        taxes = self._get_taxes()
        data = {}
        visited_details = self.env['l10n.es.aeat.mod349.partner_record_detail']
        visited_move_lines = self.env['account.move.line']
        groups = {}
        for refund_detail in self.partner_refund_detail_ids:
            move_line = refund_detail.refund_line_id
            origin_invoice = move_line.move_id.reversed_entry_id
            key = (origin_invoice, move_line.l10n_es_aeat_349_operation_key)
            groups.setdefault(key, refund_detail_obj)
            groups[key] += refund_detail
        for (origin_invoice, op_key), refund_details in groups.items():
            refund_detail = first(refund_details)
            move_line = refund_detail.refund_line_id
            partner = self._get_349_partner_from_move_line(move_line)
            op_key = move_line.l10n_es_aeat_349_operation_key
            if not origin_invoice:
                continue
            original_details = detail_obj.search(
                [
                    ('report_id.state', '!=', 'cancelled'),
                    ('move_line_id.move_id', '=', origin_invoice.id),
                    ('partner_record_id.operation_key', '=', op_key),
                    ('id', 'not in', visited_details.ids),
                ],
                order='report_id desc')
            visited_details |= original_details
            if original_details:
                report = original_details.mapped('report_id')[:1]
                original_details = original_details.filtered(
                    lambda d: d.report_id == report)
                origin_amount = sum(
                    original_details.mapped('amount_untaxed'))
                period_type = report.period_type
                year = str(report.year)
                last_refund_detail = refund_detail_obj.search(
                    [
                        ('report_id.date_start', '>', report.date_end),
                        ('report_id.date_end', '<', self.date_start),
                        ('move_id', 'in', origin_invoice.reversal_move_id.ids),
                    ],
                    order='date desc',
                    limit=1)
                if last_refund_detail:
                    origin_amount = (
                        last_refund_detail.refund_id.total_operation_amount)
            else:
                original_amls = move_line_obj.search(
                    [
                        ('tax_ids', 'in', taxes.ids),
                        ('l10n_es_aeat_349_operation_key', '=', op_key),
                        ('move_id', '=', origin_invoice.id),
                    ]
                )
                origin_amount = abs(
                    sum((
                        original_amls - visited_move_lines).mapped('balance')))
                visited_move_lines |= original_amls
                if original_amls:
                    original_move = original_amls[:1]
                    year = str(original_move.date.year)
                    month = '%02d' % (original_move.date.month)
                else:
                    continue
                if self.period_type == '0A':
                    period_type = '0A'
                elif self.period_type in ('1T', '2T', '3T', '4T'):
                    period_type = '%sT' % int(math.ceil(int(month) / 3.0))
                else:
                    period_type = month
            key = (partner, op_key, period_type, year)
            key_vals = data.setdefault(
                key,
                {
                    'original_amount': origin_amount,
                    'refund_details': refund_detail_obj,
                })
            key_vals['refund_details'] += refund_details
        for key, key_vals in data.items():
            partner, op_key, period_type, year = key
            partner_refund = obj.create({
                'report_id': self.id,
                'partner_id': partner.id,
                'partner_vat': partner.vat,
                'operation_key': op_key,
                'country_id': partner.country_id.id,
                'total_origin_amount': key_vals['original_amount'],
                'period_type': period_type,
                'year': year,
            })
            key_vals['refund_details'].write({
                'refund_id': partner_refund.id,
            })
