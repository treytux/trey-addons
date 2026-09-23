odoo.define('web_view_calendar_day.CalendarDayView', function (require) {
    'use strict'

    let Ajax = require('web.ajax')
    let Core = require('web.core')
    let QWeb = Core.qweb
    var AbstractView = require('web.AbstractView')
    var ViewRegistry = require('web.view_registry')
    var CalendarModel = require('web_view_calendar_day.CalendarDayModel')
    var CalendarController = require('web_view_calendar_day.CalendarDayController')
    var CalendarRenderer = require('web_view_calendar_day.CalendarDayRenderer')

    var CalendarDayView = AbstractView.extend({
        icon: 'fa-clock-o',
        config: {
            Model: CalendarModel,
            Controller: CalendarController,
            Renderer: CalendarRenderer,
        },
        viewType: 'calendar_day',
        groupable: false,
        init: function () {
            this._super.apply(this, arguments)
        },
    })
    ViewRegistry.add('calendar_day', CalendarDayView)
    return CalendarDayView
})
