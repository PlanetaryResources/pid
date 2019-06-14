
// jQuery plugin to prevent double submission of forms
// From: https://stackoverflow.com/a/4473801
$.fn.preventDoubleSubmission = function() {
    $(this).on('submit',function(e){
        let $form = $(this);
        if ($form.data('submitted') === true) {
            // Previously submitted - don't submit again
            e.preventDefault();
        } else {
            // Mark it so that the next submit can be ignored
            $form.data('submitted', true);
        }
    });
    // Keep chainability
    return this;
};

// Helper function for listening to Enter key. From https://stackoverflow.com/a/9964945
$.fn.enterKey = function (fnc) {
    return this.each(function () {
        $(this).keydown(function (ev) {
            let keycode = (ev.keyCode ? ev.keyCode : ev.which);
            if (keycode === 13) {
                fnc.call(this, ev);
            }
        })
    })
};

// Helper function for listening to Escape key
$.fn.escKey = function (fnc) {
    return this.each(function () {
        $(this).keydown(function (ev) {
            let keycode = (ev.keyCode ? ev.keyCode : ev.which);
            if (keycode === 27) {
                fnc.call(this, ev);
            }
        })
    })
};
