odoo.define('web_view_calendar_day.CalendarDayRenderer', function (require) {
    'use strict'

    var AbstractRenderer = require('web.AbstractRenderer')
    let Ajax = require('web.ajax')
    let Core = require('web.core')
    let QWeb = Core.qweb
    var rpc = require('web.rpc')
    let LoadTemplate = Ajax.loadXML('/web_view_calendar_day/static/src/xml/web_view_calendar_day.xml', QWeb)
    var translation = require('web.translation')
    var _t = translation._t
    var weekdays = new Array(7)
    weekdays[0] = 'Domingo'
    weekdays[1] = 'Lunes'
    weekdays[2] = 'Martes'
    weekdays[3] = 'Miércoles'
    weekdays[4] = 'Jueves'
    weekdays[5] = 'Viernes'
    weekdays[6] = 'Sábado'

    function compareDates(date1, date2){
        let day_milis = 24 * 3600000
        let days1 = Math.floor(date1.getTime() / day_milis)
        let days2 = Math.floor(date2.getTime() / day_milis)
        if (days1 > days2){
            return 1
        } else if (days1 < days2){
            return -1
        } else {
            return 0
        }
    }

    function getTimezoneOffset(date){
        let offset = date.getTimezoneOffset()
        let hours = Math.floor(Math.abs(offset) / 60)
        let minutes = Math.abs(offset) % 60
        if (offset < 0){
            date.setHours(date.getHours() + hours)
            date.setMinutes(date.getMinutes() + minutes)
        } else if (offset > 0){
            date.setHours(date.getHours() - hours)
            date.setMinutes(date.getMinutes() - minutes)
        }
        return date
    }

    var CalendarDayRenderer = AbstractRenderer.extend({
        className: 'o_wvcd_calendar_container_day',
        on_attach_callback: function () {
            this.isInDOM = true
            this._renderEvents()
        },
        _render: function () {
            let $el = this.$el
            if (this.isInDOM) {
                this._renderEvents()
                return $.when()
            }
            LoadTemplate.done(function(){
                let $calendar_day = $(QWeb.render('web_view_calendar_day.calendar_day'))
                $el.append($calendar_day)
            })
            return $.when()
        },
        _isHoliday: function (todayStr, callback) {
            rpc.query({
                model: 'hr.holidays.public.line',
                method: 'search_read',
                domain: [['date', '=', todayStr]],
            }).then(function (records) {
                const isHoliday = records.length > 0;
                callback(isHoliday);
            });
        },
        _getEventDuration: function (today, event_date_begin, event_date_end) {
            var event_date_begin = new Date(event_date_begin)
            event_date_begin = getTimezoneOffset(event_date_begin)
            var event_date_end = new Date(event_date_end)
            event_date_end = getTimezoneOffset(event_date_end)
            if (compareDates(event_date_begin, event_date_end) == 0){
                let diff = event_date_end.getHours() - event_date_begin.getHours()
                diff *= 2
                if (event_date_begin.getMinutes() >= 30){
                    diff -= 1
                }
                if (event_date_end.getMinutes() > 0 && event_date_end.getMinutes() <= 30){
                    diff += 1
                }
                if (event_date_end.getMinutes() > 30){
                    diff += 2
                }
                return diff
            }
            if (compareDates(today, event_date_begin) == 1 && compareDates(event_date_end, today) == 0){
                if (event_date_end.getHours() < 7){
                    return 0
                }
                let diff = event_date_end.getHours() - 7
                diff *= 2
                if (event_date_end.getMinutes() > 0 && event_date_end.getMinutes() <= 30){
                    diff += 1
                }
                if (event_date_end.getMinutes() > 30){
                    diff += 2
                }
                if (diff < 0) {
                    diff = 34
                }
                return diff
            }
            if (compareDates(today, event_date_begin) == 1 && compareDates(event_date_end, today) == 1){
                let diff = (23 - 7) * 2
                diff += 2
                return diff
            }
            if (compareDates(today, event_date_begin) == 0 && compareDates(event_date_end, today) == 1){
                let diff = (23 - event_date_begin.getHours()) * 2
                if (event_date_begin.getMinutes() >= 30){
                    diff += 1
                } else if (event_date_begin.getMinutes() < 30){
                    diff += 2
                }
                return diff
            }
        },
        _getEventRowBegin: function (current_date, event_date_begin) {
            var begin_event_date = new Date(event_date_begin)
            begin_event_date = getTimezoneOffset(begin_event_date)
            if (compareDates(current_date, begin_event_date) == 1){
                return 0
            } else if (compareDates(current_date, begin_event_date) == 0){
                let diff = begin_event_date.getHours() - 7
                diff *= 2
                if (begin_event_date.getMinutes() >= 30){
                    diff += 1
                }
                return diff
            }
        },
        _renderFreeGap: function ($event, current_row, $location_template, location, limit, hours) {
            for (; current_row <= limit; current_row++) {
                $event = $(QWeb.render('web_view_calendar_day.no_event_button', {
                    'name': hours[current_row],
                    'location': location.id,
                    'time': hours[current_row],
                }))
                $location_template.append($event)
            }
        },
        _renderLocationFooter: function ($location_template, location) {
            var $footer = $(QWeb.render('web_view_calendar_day.footer_location', {
                'location_name': location.name,
            }))
            $location_template.append($footer)
        },
        _get_locale_datetime: function (today, time_str, end_date) {
            let time_list = time_str.split(':')
            let time_float = parseInt(time_list[1]) / 60 + parseInt(time_list[0])
            let timeoffset = today.getTimezoneOffset() / 60
            time_float = time_float + timeoffset
            today.setHours(Math.floor(time_float / 1))
            today.setMinutes((time_float % 1) * 60)
            today.setSeconds(0)
            if (end_date) {
                if (time_str == '23:30') {
                    today = moment(today).add(-1, 'm').toDate()
                    today.setSeconds(59)
                }
                today = moment(today).add(30, 'm').toDate()
            }
            return today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0') + '-' + String(today.getDate()).padStart(2, '0') + ' '+ today.toTimeString()
        },
        _renderEvents: function () {
            var self = this
            let today
            let has_date_end = false
            let date_context = self.__parentedParent.model.context.date
            self.__parentedParent.model.domain.forEach(function (domain){
                if (Array.isArray(domain)){
                    domain.forEach(function (field){
                        if (field == 'date_end'){
                            if (date_context && !Array.isArray(date_context)){
                                today = new Date(date_context)
                                domain[2] = date_context
                                self.__parentedParent.model.context.date = []
                            } else {
                                today = new Date(domain[2])
                            }
                            has_date_end = true
                        }
                    })
                }
            })
            if (!has_date_end) {
                today = new Date()
            }
            let real_month =  today.getMonth() + 1
            const date_selection = document.getElementById('date_selection')
            if (date_selection){
                date_selection.value = today.getFullYear() + '-' + String(real_month).padStart(2, '0') + '-' + String(today.getDate()).padStart(2, '0')
            }
            const date_actual = document.getElementById("calendar_button_date")
            if (date_actual){
                date_actual.textContent = String(today.getDate()).padStart(2, '0') + '/' + String(real_month).padStart(2, '0') + '/' + today.getFullYear() + ' ' + weekdays[today.getDay()]
                this._isHoliday(date_selection.value, function(isHoliday) {
                    if (isHoliday) {
                        date_actual.style.color = 'red';
                        date_actual.textContent += ' (Festivo)';
                    } else {
                        date_actual.style.color = 'black';
                    };
                });
            }
            let $el = self.$el
            let locations_events = self.state.locations_events
            let location_templates = self.state.location_templates
            let $calendar = $el.find('.js_web_view_calendar_day_widget .row')
            $calendar.empty()
            let hours = []
            for(var i = 7; i < 24; i++){
                hours.push(i + ':00')
                hours.push(i + ':30')
            }
            var $hours = $(QWeb.render('web_view_calendar_day.hours', {
                'hours': hours,
            }))
            $calendar.append($hours)
            location_templates.forEach(function (location) {
                let location_name = location.name
                var $location_template = $(QWeb.render('web_view_calendar_day.location', {
                    'location_name': location_name,
                }))
                $calendar.append($location_template)
                let current_row = 0
                var $event = false
                if (!locations_events[location_name].length) {
                    self._renderFreeGap($event, current_row, $location_template,location, 33, hours)
                } else {
                    locations_events[location_name].forEach(function (event) {
                        today.setHours(7)
                        let start_row = self._getEventRowBegin(today, event.date_begin)
                        if (start_row < 0) {
                            start_row = 34
                        }
                        let event_duration = 1
                        for (; current_row <= 33; current_row++) {
                            if (current_row < start_row) {
                                let limit = start_row - 1
                                self._renderFreeGap($event, current_row, $location_template, location, limit, hours)
                                current_row = limit
                            } else if (current_row == start_row) {
                                LoadTemplate.done(function(){
                                    let event_date_begin = new Date(event.date_begin)
                                    let event_date_end = new Date(event.date_end)
                                    let condition_01 = compareDates(event_date_begin, today) == 0 || compareDates(event_date_end, today) == 0
                                    let condition_02 = compareDates(today, event_date_begin) == 1 && compareDates(event_date_end, today) == 1
                                    if (!condition_01 && !condition_02){
                                        self._renderFreeGap($event, current_row, $location_template, location, 0, hours)
                                        return
                                    }
                                    event_date_begin = getTimezoneOffset(event_date_begin)
                                    event_date_end = getTimezoneOffset(event_date_end)
                                    event_duration = self._getEventDuration(today, event.date_begin, event.date_end)
                                    if (event_duration == 0){
                                        return
                                    }
                                    $event = $(QWeb.render('web_view_calendar_day.event', {
                                        'event_date_begin': event_date_begin.toLocaleDateString() + ' ' + event_date_begin.toTimeString().slice(0, 5),
                                        'event_date_end': event_date_end.toLocaleDateString() + ' ' + event_date_end.toTimeString().slice(0, 5),
                                        'event_name': event.name,
                                        'calendar_view_color': event.calendar_view_color,
                                        'event_duration': event_duration,
                                        'event_hour_begin': 0,
                                        'event_id': event.id,
                                        'title': event.name,
                                        'event_state': event.state,
                                        'is_preproduction': ((event.is_preproduction) ? 'preproduction' : 'none'),
                                        'other_addresses': event.other_addresses,
                                    }))
                                })
                                current_row += event_duration
                                $location_template.append($event)
                                if (locations_events[location_name][locations_events[location_name].length - 1] == event && current_row <= 33) {
                                    self._renderFreeGap($event, current_row, $location_template, location, 33, hours)
                                }
                                break
                            }
                        }
                    })
                }
                self._renderLocationFooter($location_template, location)
            })
            var $hours = $(QWeb.render('web_view_calendar_day.hours', {
                'hours': hours,
            }))
            $calendar.append($hours)
            let $eventbuttons = $calendar.find('.o_wvcd_event')
            if ($eventbuttons.length) {
                $eventbuttons.each(function(){
                    $(this).on('click', function(){
                        let event_id = $(this).data('event_id');
                        rpc.query({
                            model: 'ir.model.data',
                            method: 'xmlid_to_res_id',
                            args: ['event.event_main_menu'],
                        }).then(function (menu_id) {
                            let url = `/web#id=${event_id}&model=event.event&view_type=form&menu_id=${menu_id}`;
                            window.open(url, '_blank');
                        });
                    });
                })
            }
            let $cellbuttons = $el.find('.js_wvcd_create_div')
            let $all_current_hours = $el.find('.js_wvcd_current_hour')
            let selected_location
            if ($cellbuttons.length) {
                let $first_click
                $cellbuttons.each(function(){
                    $(this).on('mousedown', function(e){
                        e.preventDefault()
                        if ($first_click) {
                            if (selected_location != $(this).data('location')) {
                                $cellbuttons.removeClass('state_down')
                                $all_current_hours.addClass('d-none')
                            }
                            $cellbuttons.removeClass('state_down')
                            $all_current_hours.addClass('d-none')
                        } else {
                            $cellbuttons.removeClass('state_down')
                            $all_current_hours.addClass('d-none')
                            $(this).addClass('state_down')
                            $(this).children('span').removeClass('d-none')
                            $first_click = $(this)
                            selected_location = $(this).data('location')
                        }
                    })
                    $(this).hover(function(){
                        if ($first_click && selected_location == $(this).data('location')) {
                            if ($(this).hasClass('o_wvcd_event') || ($(this).prev().hasClass('o_wvcd_event') && !$(this).is($first_click))){
                                $first_click = null
                                $cellbuttons.removeClass('state_down')
                                $all_current_hours.addClass('d-none')
                            } else if ($(this).prevAll().is($first_click)){
                                $(this).nextAll().each(function(){
                                    $(this).removeClass('state_down')
                                    $(this).children('span').addClass('d-none')
                                })
                                $(this).addClass('state_down')
                                $(this).children('span').removeClass('d-none')
                                $(this).prevAll().each(function(){
                                    $(this).addClass('state_down')
                                    $(this).children('span').removeClass('d-none')
                                })
                                $first_click.prevAll().each(function(){
                                    $(this).children('span').addClass('d-none')
                                    $(this).removeClass('state_down')
                                })
                            }
                            else{
                                $(this).nextAll().each(function(){
                                    $(this).children('span').addClass('d-none')
                                    $(this).removeClass('state_down')
                                })
                            }
                        }
                    })
                    $(this).on('mouseup', function(e){
                        if ($first_click && selected_location == $(this).data('location') && $(this).prevAll().is($first_click) ||  $(this).is($first_click)) {
                            let context = {}
                            let start_datetime = self._get_locale_datetime(today, $first_click.data('time'), false)
                            let end_datetime = self._get_locale_datetime(today, $(this).data('time'), true)
                            context['default_start_booking'] = start_datetime
                            context['default_end_booking'] = end_datetime
                            context['default_start_activity'] = start_datetime
                            context['default_end_activity'] = end_datetime
                            context['default_address_ids'] = [selected_location]
                            rpc.query({
                                model: 'wizard.calendar.event',
                                method: 'get_formview_id',
                                args: [false, context],
                            }).then(function (viewId) {
                                self.do_action({
                                    name: _t('Calendar wizard'),
                                    type:'ir.actions.act_window',
                                    res_model: 'wizard.calendar.event',
                                    views: [[viewId || false, 'form']],
                                    target: 'new',
                                    context: context,
                                })
                            })
                        }
                        $first_click = null
                        selected_location= null
                        $cellbuttons.removeClass('state_down')
                        $all_current_hours.addClass('d-none')
                    })
                })
            }
        },
    })
    return CalendarDayRenderer
})
