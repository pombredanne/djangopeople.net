jQuery(function($) {
    $('div.nav a.login').click(function() {
        // Show inline login form
        $('div#hiddenLogin').show().css({
            position: 'absolute',
            top: $(this).offset().top + $(this).height() + 7,
            left: $(this).offset().left
        });
        $('#id_usernameH').focus();
        return false;
    });
});
