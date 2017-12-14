(function () {
    'use strict';
    $(document).ready(function () {
        function check_in_stock() {
            var product_id = $('input.product_id');
            if( product_id && $('input[name="wspis_product_id_' + product_id.val() + '"]').attr('wspis-in-stock') == 'True') {
                $('.wspis_out_of_stock_msg').hide();
                $('.wspis_out_of_stock_msg').css('visibility','hidden');
                $('.wspis_in_stock_msg').fadeIn();
                $('.wspis_in_stock_msg').css('visibility','visible');
                $('#add_to_cart').removeClass('disabled');
            } else {
                $('.wspis_out_of_stock_msg').fadeIn();
                $('.wspis_out_of_stock_msg').css('visibility','visible');
                $('.wspis_in_stock_msg').hide();
                $('.wspis_in_stock_msg').css('visibility','hidden');
                if( $('input[name="wspis_allow_sale_out_of_stock"]').val() != 'True') {
                    $('#add_to_cart').addClass('disabled');
                }
            }
        }
        $('.oe_website_sale').each(function () {
            var oe_website_sale = this;
            $(oe_website_sale).on('change', 'input.js_variant_change, select.js_variant_change', function (ev) {
                check_in_stock();
            });
        });
        check_in_stock();
    });
})();
