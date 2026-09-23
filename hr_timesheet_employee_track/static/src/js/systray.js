odoo.define('hr_timesheet_employee_track.hr_timesheet_employee_track',
  function (require) {
    'use strict';

    var session = require('web.session');
    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');
    var LauncherMenu = Widget.extend({
      template: 'hr_timesheet_employee_track.view.Menu',
      events: {
        click: 'on_click_button',
      },
      on_click_button: function (event) {
        event.preventDefault();
        event.stopPropagation();
        var context = {};
        context.default_model = '';
        context.default_method = 'read_code_action';
        this._getTimeSheetInfo();
      },
      _getTimeSheetInfo: function () {
        var self = this;
        let today = new Date().toISOString().split('T')[0];
        return self
          ._rpc({
            model: 'account.analytic.line',
            method: 'search_read',
            args: [
              [
                ['user_id', '=', session.uid],
                ['date', '=', today],
              ],
              ['name', 'real_time'],
            ],
            kwargs: {
              context: session.user_context,
            },
          })
          .then(function (data) {
            let total = 0;
            for (var i = 0; i < data.length; i++) {
              total += data[i]['real_time'];
            }
            total = total.toFixed(2);
            var hours = Math.floor(total);
            var minutes = Math.round((total - hours) * 60);
            if (minutes < 10) {
              minutes = '0' + minutes;
            }
            total = hours + ':' + minutes;
            self.$('.o_notification_timesheet_counter').text(total);
          });
      },
    });
    SystrayMenu.Items.push(LauncherMenu);
    return {
      LauncherMenu: LauncherMenu,
    };
  }
);
