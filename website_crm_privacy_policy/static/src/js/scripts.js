document.addEventListener('DOMContentLoaded', function(){
    jQuery(document).ready(function($){
        $('form[action="/crm/contactus"]').on('submit', function(e) {
            // Check if privacy_policy is checked
            if(!$('input[name="privacy_policy"]').is(':checked')) {
                e.preventDefault();  // Prevent form from submitting
                $('.privacy-policy-msg').removeClass('hidden');
            }
        });
    });
});
