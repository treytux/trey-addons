odoo.define('portal_employee.portal_employee', function (require) {
    'use strict';

    $(document).ready(function() {
        $('#custom_hours').change(function() {
            toggleCustomHoursFields();
        });
        function toggleCustomHoursFields() {
            var customHoursFields = $('#custom_hours_fields');
            var request_date_toField = $('#request_date_to');
            if ($('#custom_hours').is(':checked')) {
                customHoursFields.show();
                request_date_toField.hide();
            } else {
                customHoursFields.hide();
                request_date_toField.show();
            }
        }
    });
});
