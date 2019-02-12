odoo.define('website_legal_age_notice.website_legal_age_notice', function(require) {
    "use strict";


    var website = require('website.website');

    website.ready().done(function() {
        if(!$('.js_wlan_message').length) {
            return $.Deffered().reject("DOM doesn't contain '.js_wlan_message'");
        }
        var $legalAgeMessage = $('.js_wlan_message');
        var $legalAgePopup = $('.js_wlan_message .modal');
        $legalAgePopup.modal();
        $('.js_wlan_btn_yes').click(function(event){
            event.preventDefault();
            $.ajax($(event.target).attr('href'), {
                'complete': function(jqXHR, textStatus){
                    $legalAgeMessage.fadeOut('fast');
                    $legalAgePopup.modal('hide');
                }
            });
        });
        $('.js_wlan_btn_no').click(function(event){
            event.preventDefault();
            var $legalAgeQuestion = $('.js_wlan_question');
            var $legalAgeNo = $('.js_wlan_legal_age_no');
            $legalAgeQuestion.hide();
            $legalAgeNo.removeClass('hidden');
        });
    });
});
