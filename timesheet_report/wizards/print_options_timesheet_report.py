# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import calendar
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from openerp import models, fields, api, exceptions, _

import logging
_log = logging.getLogger(__name__)


class WizTimesheetReportOptions(models.TransientModel):
    _name = 'wiz.timesheet.report_options'
    _description = 'Wizard to report timesheets'

    employe_ids = fields.Many2many(
        comodel_name='hr.employee',
        string='Employee',
        required=True,
    )
    month = fields.Selection(
        selection=[(i, calendar.month_name[i]) for i in range(1, 13)],
        string='Month',
        required=True,
        default=datetime.now().month,
    )
    fiscal_year = fields.Many2one(
        comodel_name='account.fiscalyear',
        default=lambda self: self.env['account.fiscalyear'].search([
            ('code', '=', datetime.now().strftime('%Y'))
        ]),
        required=True,
    )

    def get_config_values(self):
        config_fields = ['working_hours', 'break_duration']
        time_conf_fields = [
            'break_time', 'entrance', 'late_shift', 'exit_time']
        config_vals = self.env[
            'hr.config.settings'].default_get(config_fields + time_conf_fields)
        for key in config_fields + time_conf_fields:
            if not config_vals[key]:
                raise exceptions.Warning(
                    _('Please complete config parameters first'))
            if key in time_conf_fields:
                config_vals[key] = str(timedelta(hours=config_vals[key]))[:-3]
        entr2 = datetime.strptime(
            config_vals['break_time'], '%H:%M') + relativedelta(
                minutes=config_vals['break_duration'])
        config_vals['entrance2'] = entr2.strftime("%H:%M")
        return config_vals

    def get_month_days(self):
        year = int(self.fiscal_year.date_start[0:4])
        day, month_days = calendar.monthrange(year, int(self.month))
        return month_days

    def get_keys(self):
        return {
            'extra_hrs': 'HE',
            'strday_hrs': 'HS',
            'festive_hrs': 'HF',
            'std_hrs': 'HN',
            'holday_hrs': 'H Vacaciones',
            'permit_hrs': 'H Permiso Retribuido',
            'accident_hrs': 'H Baja Accidente',
            'medical_hrs': 'H Baja Enfermedad',
            'parenthood_hrs': 'H Baja M/Paternidad',
        }

    def get_hr_types(self):
        hours_keys = self.get_keys()
        worker_rates = self.env['hr.payslip.worker.rate'].search([])
        hr_types = {}
        for key_type in hours_keys:
            hr_types.setdefault(key_type, [])
            filtered_rates = worker_rates.filtered(
                lambda x: x.name.startswith(hours_keys[key_type]))
            if not filtered_rates:
                _log.warning(('Worked rate not found:', hours_keys[key_type]))
            for filtered_rate in filtered_rates:
                hr_types[key_type].append(filtered_rate.name)
        return hr_types

    def get_journeys(self, month_days, config_values, employe_id):
        journeys_dict = {}
        hr_types = self.get_hr_types()
        totals = {
            'ordinaries': 0,
            'he': 0,
            'hs': 0,
            'hf': 0,
            'hv': 0,
            'hp': 0,
            'ha': 0,
            'hm': 0,
            'hpt': 0,
        }
        year = int(self.fiscal_year.date_start[0:4])
        for day in range(1, month_days + 1):
            config_values = self.get_config_values()
            entrance = datetime.strptime(config_values['entrance'], '%H:%M')
            bktime = datetime.strptime(config_values['break_time'], '%H:%M')
            entr2 = datetime.strptime(config_values['entrance2'], '%H:%M')
            count = 0
            count_hn = 0
            extra_hours = 0
            festive_hours = 0
            saturday_hours = 0
            holday_hours = 0
            permit_hours = 0
            accident_hours = 0
            medical_hours = 0
            parenthood_hours = 0
            date_act = date(year, int(self.month), day)
            timesheets = self.env['hr.analytic.timesheet'].search([
                ('date', '=', date_act.strftime('%Y-%m-%d')),
                ('user_id', '=', employe_id.user_id.id)])
            entr3 = False
            exit3 = False
            for timesheet in timesheets:
                wrkd_rate_name = timesheet.worked_rate.display_name
                if not timesheet.unit_amount:
                    raise exceptions.Warning(
                        _('There are timesheets without duration'))
                if wrkd_rate_name in hr_types['extra_hrs']:
                    extra_hours += timesheet.unit_amount
                    continue
                if wrkd_rate_name in hr_types['festive_hrs']:
                    count += timesheet.unit_amount
                    festive_hours += timesheet.unit_amount
                    if date_act.weekday() in [5, 6]:
                        wrk_hours = config_values['working_hours']
                        if timesheet.unit_amount > wrk_hours:
                            entr3 = datetime.strptime('15:00', '%H:%M')
                            exit3 = entr3 + relativedelta(
                                hours=timesheet.unit_amount - wrk_hours)
                        continue
                if wrkd_rate_name in hr_types['strday_hrs']:
                    saturday_hours += timesheet.unit_amount
                    count += timesheet.unit_amount
                    continue
                if wrkd_rate_name in hr_types['std_hrs']:
                    count += timesheet.unit_amount
                    count_hn += timesheet.unit_amount
                if wrkd_rate_name in hr_types['holday_hrs']:
                    holday_hours += timesheet.unit_amount
                if wrkd_rate_name in hr_types['permit_hrs']:
                    permit_hours += timesheet.unit_amount
                if wrkd_rate_name in hr_types['accident_hrs']:
                    accident_hours += timesheet.unit_amount
                if wrkd_rate_name in hr_types['medical_hrs']:
                    medical_hours += timesheet.unit_amount
                if wrkd_rate_name in hr_types['parenthood_hrs']:
                    parenthood_hours += timesheet.unit_amount
            working_hours = config_values['working_hours']
            exit2 = datetime.strptime(config_values['exit_time'], '%H:%M')
            if count < working_hours:
                difference = bktime - entrance
                difference_hours = difference.seconds / 3600.0
                if count < difference_hours:
                    entr2 = False
                    exit2 = False
                    bktime = entrance + relativedelta(hours=count)
                else:
                    exit2 = exit2 - relativedelta(hours=working_hours - count)
            if count > working_hours and wrkd_rate_name in hr_types['std_hrs']:
                extra_hours = count - working_hours
                count = working_hours
            if extra_hours:
                if extra_hours <= 1:
                    exit2 = exit2 + relativedelta(hours=extra_hours)
                else:
                    entr3 = datetime.strptime(
                        config_values['late_shift'], '%H:%M')
                    exit3 = entr3 + relativedelta(hours=extra_hours)
            journeys_dict.setdefault(
                int(date_act.day), {
                    'weekday': date_act.weekday(),
                    'breaktime': bktime and bktime.strftime('%H:%M') or False,
                    'entrance2': entr2 and entr2.strftime('%H:%M') or False,
                    'entrance3': entr3 and entr3.strftime("%H:%M") or False,
                    'exit2': exit2 and exit2.strftime("%H:%M") or False,
                    'exit3': exit3 and exit3.strftime("%H:%M") or False,
                    'ordinaries': count_hn,
                    'he': extra_hours,
                    'hf': festive_hours,
                    'hs': saturday_hours,
                    'hv': holday_hours,
                    'hp': permit_hours,
                    'ha': accident_hours,
                    'hm': medical_hours,
                    'hpt': parenthood_hours,
                })
            for key in totals.keys():
                totals[key] += journeys_dict[date_act.day][key]
            journeys_dict['totals'] = totals
        return journeys_dict

    @api.multi
    def button_print(self):
        month_days = self.get_month_days()
        config_values = self.get_config_values()
        journeys_dict = {}
        for employe_id in self.employe_ids:
            journeys = self.get_journeys(month_days, config_values, employe_id)
            journeys_dict.setdefault(employe_id.id, journeys)
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'timesheet_report.report_timesheet',
            'datas': dict(
                config_values=config_values,
                employe_ids=self.employe_ids.ids,
                journeys=journeys_dict,
                month_days=month_days,
                year=self.fiscal_year.code,
                month=calendar.month_name[int(self.month)],
            )
        }
