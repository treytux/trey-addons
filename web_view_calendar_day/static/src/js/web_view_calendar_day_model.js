odoo.define('web_view_calendar_day.CalendarDayModel', function (require) {
    'use strict';

    var AbstractModel = require('web.AbstractModel')

    var CalendarDayModel = AbstractModel.extend({
        get: function () {
            return {
                locations_events: this.locations_events,
                location_templates: this.location_templates,
            }
        },
        load: function (params) {
            return this._load(params)
        },
        reload: function (id, params) {
            return this._load(params)
        },
        _load: function (params) {
            if (this.domain && this.domain.length > 0) {
                this.last_domain = this.domain
            }
            this.domain = params.domain && params.domain.length > 0 ? params.domain :
              this.last_domain && this.last_domain.length > 0 ? this.last_domain :
              [];
            this.context = params.context || this.domain || []
            this.date = false
            let date_context = false
            if (this.context && this.context.date && !Array.isArray(this.context.date)) {
                date_context = new Date(this.context.date)
                this.date = date_context.getFullYear() + '-' + String(date_context.getMonth() + 1).padStart(2, '0') + '-' + String(date_context.getDate()).padStart(2, '0') + 'Z' + date_context.getTimezoneOffset() / 60
            }
            var self = this
            this._rpc({
                model: 'res.partner',
                method: 'search_read',
                fields: ['id','name'],
                domain: [['partner_category', '=', 'event_location'], ['parent_id', '!=', false], ['show_in_calendar', '=', true]],
                orderBy: [{name: 'sequence', asc: true}],
                context: {lang: 'es_ES'},
            }).then(function (result) {
                self.location_templates = result
            })
            return this._rpc({
                model: 'event.event',
                method: 'get_events_day',
                args: [self.res_id, this.domain],
                context: {lang: 'es_ES', date: this.date},
            }).then(function (result) {
                self.locations_events = result
            })
        },
    })
    return CalendarDayModel
})
