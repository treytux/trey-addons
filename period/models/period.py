# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import api, models, fields
from dateutil.relativedelta import relativedelta


class Period(models.Model):
    _name = 'period'
    _description = 'Period'

    name = fields.Char(
        string='Name',
        translate=True)
    seconds = fields.Integer(
        string='Seconds')
    minutes = fields.Integer(
        string='Minutes')
    hours = fields.Integer(
        string='Hours')
    days = fields.Integer(
        string='Days')
    weeks = fields.Integer(
        string='Weeks')
    months = fields.Integer(
        string='Months')
    years = fields.Integer(
        string='Years')

    @api.multi
    def next(self, date):
        if isinstance(date, str):
            date = fields.Datetime.from_string(date)
        return date + relativedelta(
            years=self.years,
            months=self.months,
            days=self.days,
            weeks=self.weeks,
            hours=self.hours,
            minutes=self.minutes,
            seconds=self.seconds)

    @api.multi
    def before(self, date):
        if isinstance(date, str):
            date = fields.Datetime.from_string(date)
        return date - relativedelta(
            years=self.years,
            months=self.months,
            days=self.days,
            weeks=self.weeks,
            hours=self.hours,
            minutes=self.minutes,
            seconds=self.seconds)
