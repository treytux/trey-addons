# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, _
import logging
_log = logging.getLogger(__name__)


class BookingWebservice(models.Model):
    _inherit = 'booking.webservice'

    @api.multi
    def mt_find_or_create_booking(self, booking, _cache=None):
        booking_obj = super(BookingWebservice, self).mt_find_or_create_booking(
            booking, _cache=None)
        my_booking = self.add_agents_to_booking_line(booking, booking_obj)
        return my_booking

    @api.multi
    def add_agents_to_booking_line(self, booking_info, booking_obj):
        if not booking_obj:
            return booking_obj
        sale_info = (
            booking_info['Services'][0]['Accommodation']['Price']['Sale'])
        if sale_info['Commission'] > 0:
            if not sale_info.get('CommissionPercentage'):
                msg = _('Booking %s with commission percentage not defined.'
                        % booking_obj.name)
                self.env['methabook.log'].add_log(
                    'booking', None, 'booking', booking_info, msg, 'error')
                self.env.cr.commit()
                return False
            for booking_line in booking_obj.booking_line:
                commission = self.find_or_create_commission(
                    booking_obj, sale_info)
                tax = self.find_taxes(sale_info['TaxPercentage'])
                if sale_info['TaxPercentage'] > 0 and tax is False:
                    msg = _('Booking %s with commision tax %s not defined.' % (
                        booking_obj.name, sale_info['TaxPercentage']))
                    self.env['methabook.log'].add_log(
                        'booking', None, 'booking', booking_obj, msg, 'error')
                    return False
                booking_line_data = {
                    'commission_amount': sale_info['Commission'],
                    'commission_percentage_tax': sale_info['TaxPercentage'],
                    'commission_amount_tax': sale_info['TaxCommission'],
                    'commission_tax_id': tax and tax.id or None}
                if booking_obj.agency_id.id not in booking_line.agents.ids:
                    agent_lines = self.env['booking.line.agent'].search(
                        [('booking_line', '=', booking_line.id)])
                    if not agent_lines:
                        booking_line_data.update({
                            'agents': [(
                                0, 0, {'agent': booking_obj.agency_id.id,
                                       'commission': commission.id,
                                       'booking_line': booking_line.id,
                                       'amount': sale_info['Commission']})]})
                else:
                    booking_line.agents[0].commission = commission.id
                    booking_line.agents[0].amount = sale_info['Commission']
                _log.info('X' * 80)
                _log.info(('booking_line_data', booking_line_data))
                _log.info(('booking_info', booking_info))
                _log.info('X' * 80)
                booking_line.write(booking_line_data)
                booking_obj.amount_commission = sale_info['Commission']
        if sale_info.get('Net'):
            booking_obj.booking_net_price = sale_info['Net']
        return booking_obj

    @api.multi
    def find_or_create_commission(self, booking, sale_info):
        commission_obj = self.env['booking.commission']
        commission_percentage = sale_info['CommissionPercentage']
        commission = commission_obj.search([
            ('name', '=', '%s' % str(commission_percentage) + '%'),
            ('fix_qty', '=', r"%.2f" % (float(commission_percentage) / 100)),
            ('invoice_state', '=', 'open')])
        if not commission:
            commission = commission_obj.create({
                'name': '%s' % str(commission_percentage) + '%',
                'fix_qty': r"%.2f" % (float(commission_percentage) / 100),
                'invoice_state': 'open'})
            self.env.cr.commit()
        if not booking.agency_id.agent:
            booking.agency_id.agent = True
            booking.agency_id.commission = commission.id
        return commission

    @api.multi
    def find_taxes(self, commission_percentage):
        tax_name = '%s' % str(commission_percentage) + '%'
        if commission_percentage == 7:
            tax_name = 'IGIC %s' % str(commission_percentage) + '%'
        tax = self.env['account.tax'].search([('type_tax_use', '=', 'sale'),
                                              ('name', '=', tax_name)])
        return tax and tax[0] or False
