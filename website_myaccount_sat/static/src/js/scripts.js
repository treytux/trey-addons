(function () {
    'use strict';

    $(document).ready(function () {
        $('.send-a-message').on('click', function(e) {
            e.preventDefault();
            $(this).hide();
            $('.message-sat-new').fadeIn('fast');
        });
        $('.myaccount-sat-claim-edit').on('click', function(e) {
            e.preventDefault();
            $(this).hide();
            $('.myaccount-sat-claim-cancel').fadeIn('fast');
            $('.myaccount-sat-claim-save').fadeIn('fast');
            $('.field-readonly').hide();
            $('.field-edit').fadeIn('fast');
        });
        $('.myaccount-sat-claim-cancel').on('click', function(e) {
            e.preventDefault();
            $(this).hide();
            $('.myaccount-sat-claim-save').hide();
            $('.myaccount-sat-claim-edit').fadeIn('fast');
            $('.field-edit').hide();
            $('.field-readonly').fadeIn('fast');
        });
    });

})();
