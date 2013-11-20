jQuery.fn.yellowFade = function() {
    return this.css({
        'backgroundColor': 'yellow'
    }).animate({
        'backgroundColor': 'white'
    }, 1500);
};

var INITIAL_LAT = 43.834526782236814;
var INITIAL_LON = -37.265625;

function reverseGeocode() {
    var lon = $('input#id_longitude').val();
    var lat = $('input#id_latitude').val();
    // Don't geocode if we're still at the starting point
    if (!lon || !lat || (
            Math.abs(lat - INITIAL_LAT) < 0.01 &&
            Math.abs(lon - INITIAL_LON) < 0.01)) {
        return;
    }
    var url = 'http://ws.geonames.org/findNearbyPlaceNameJSON?';
    url += 'lat=' + lat + '&lng=' + lon + '&callback=?';
    jQuery.getJSON(url, function(json) {
        if (typeof json.geonames != 'undefined' && json.geonames.length > 0) {
            // We got results
            var place = json.geonames[0];
            var iso_code = place.countryCode;
            var countryName = place.countryName;
            var adminName1 = place.adminName1;
            var name = place.name;
            if (adminName1 && adminName1.toLowerCase() != name.toLowerCase()) {
                name += ', ' + adminName1;
            }
            if ($('#id_location_description').val() != name) {
                $('#id_location_description').val(name);
                $('#id_location_description').parent().yellowFade();
            }
            $('#id_country').val(iso_code).change();
            // Update region field, if necessary
            if (hasRegions(countryName) && place.adminCode1) {
                $('#id_region').val(place.adminCode1);
            } else {
                $('#id_region').val('');
            }
        }
    });
}

function hasRegions(country_name) {
    return $('select#id_region optgroup[label="' + country_name + '"]').length;
}

jQuery(function($) {
    // Set up the select country thing to show flags
    $('select#id_country').change(function() {
        $(this).parent().find('span.flag').remove();
        var iso_code = $(this).val().toLowerCase();
        if (!iso_code) {
            return;
        }
        $('<span class="flag iso-' + iso_code + '"></span>').insertAfter(this);
    }).change();

    // Region select field is shown only if a country with regions is selected
    $('select#id_country').change(function() {
        var selected_text = $(
            'select#id_country option[value="' + $(this).val() + '"]'
        ).text();
        if (hasRegions(selected_text)) {
            $('select#id_region').parent().show();
        } else {
            $('select#id_region').parent().hide();
            $('#id_region').val('');
        }
    }).change();

    $('select#id_region').parent().hide();
    // Latitude and longitude should be invisible too
    $('input#id_latitude').parent().hide();
    $('input#id_longitude').parent().hide();

    var centerPoint;
    var zoom;
    /* If latitude and longitude are populated, center there */
    if ($('input#id_latitude').val() && $('input#id_longitude').val()) {
        centerPoint = new google.maps.LatLng(
            $('input#id_latitude').val(),
            $('input#id_longitude').val()
        );
        zoom = 10;
    } else {
        centerPoint = new google.maps.LatLng(INITIAL_LAT, INITIAL_LON);
        zoom = 3;
    }

    var gmap = new google.maps.Map(document.getElementById('gmap'), {
        zoom: zoom,
        center: centerPoint,
        mapTypeId: google.maps.MapTypeId.ROADMAP,
        scrollwheel: false
    });

    var lookupTimer = false;

    google.maps.event.addListener(gmap, "center_changed", function() {
        window.center = gmap.getCenter();
        if (lookupTimer) {
            clearTimeout(lookupTimer);
        }
        lookupTimer = setTimeout(reverseGeocode, 1500);
        $('input#id_latitude').val(center.lat());
        $('input#id_longitude').val(center.lng());
    });
    google.maps.event.addDomListener(document.getElementById('crosshair'),
        'dblclick', function() {
            gmap.zoomIn();
        }
    );

    /* The first time the map is hovered, scroll the page */
    $('#gmap').one('click', function() {
        $('html,body').animate({scrollTop: $('#gmap').offset().top}, 500);
    });
});
