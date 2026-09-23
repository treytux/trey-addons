document.addEventListener("DOMContentLoaded", function() {
    start();
});

function start() {
    if (document.getElementById('filter_stock')) {
        var check_button = document.getElementById('filter_stock')
        check_button.addEventListener('click', function() {
            submitForm();
        })
    }
}

function submitForm() {
    if (document.getElementById('filter_form')) {
        document.getElementById('filter_form').submit();
    }
}
