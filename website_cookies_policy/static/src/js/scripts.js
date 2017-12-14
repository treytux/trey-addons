document.addEventListener('DOMContentLoaded', function(){
    jQuery(document).ready(function($){

        // Obtiene una cookie almacenada en el navegador
        function getCookie(name) {
            if (document.cookie.length > 0) {
                date_start = document.cookie.indexOf(name + "=");
                if (date_start != -1) {
                    date_start = date_start + name.length + 1;
                    date_end = document.cookie.indexOf(";", date_start);
                    if (date_end == -1) {
                        date_end = document.cookie.length;
                    }
                    return unescape(document.cookie.substring(date_start, date_end));
                }
            }
            return "";
        }

        // Almacena una cookie en el navegador durante n días
        function setCookie(name, value, days) {
            var expires;
            if (days) {
                var date = new Date();
                date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
                expires = "; expires=" + date.toGMTString();
            }
            else {
                expires = "";
            }
            document.cookie = name + "=" + value + expires + "; path=/";
        }

        // Asignar funcionalidad al botón
        $('.cookies-policy-btn').on('click', function(e){
            e.preventDefault();
            setCookie('accept_cookies_policy', 'true', 365);
            $('.cookies-policy').removeClass('cookies-policy-show');
        });

        // Comprobar si se han aceptado las Cookies
        if( getCookie('accept_cookies_policy') != 'true' ) {
            $('.cookies-policy').addClass('cookies-policy-show');
        }

    });
});
