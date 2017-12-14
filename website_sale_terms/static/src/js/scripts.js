document.addEventListener('DOMContentLoaded', function(){
    jQuery(document).ready(function($){
        $('form[action="/shop/confirm_order"]').on('submit', function(e) {
            // Check if checkout_terms is checked
            if(!$('input[name="checkout_terms"]').is(':checked')) {
                e.preventDefault();  // Prevent form from submitting
                $('.checkout-policy-msg').removeClass('hidden');
            }
        });
    });
});
