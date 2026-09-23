/** @odoo-module **/

import publicWidget from 'web.public.widget';

publicWidget.registry.PortalEmployeeLeaveRequest = publicWidget.Widget.extend({
    selector: '#leaves_request',
    events: {
        'change #custom_hours': '_onCustomHoursChange',
    },

    /**
     * @override
     */
    start: function () {
        this._toggleCustomHoursFields();
        return this._super.apply(this, arguments);
    },

    _onCustomHoursChange: function (ev) {
        this._toggleCustomHoursFields();
    },

    _toggleCustomHoursFields: function () {
        const $customHours = this.$('#custom_hours');
        const $customHoursFields = this.$('#custom_hours_fields');
        const $requestDateToRow = this.$('#request_date_to').closest('.row');
        if ($customHours.is(':checked')) {
            $customHoursFields.show();
            $requestDateToRow.hide();
        } else {
            $customHoursFields.hide();
            $requestDateToRow.show();
        }
    },
});
