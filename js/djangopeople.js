(function($, undefined) {
    var hasRegions = function(country_name) {
        return $('select#id_region optgroup[label="' + country_name + '"]').length;
    };

    var reverseGeocode = function() {
        var lon = $('input#id_longitude').val();
        var lat = $('input#id_latitude').val();

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
    };

    var handleFormGeoElements = function(map) {
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

        /* If latitude and longitude are populated, center there */
        if ($('input#id_latitude').val() && $('input#id_longitude').val()) {
            var center = new L.LatLng(
                $('input#id_latitude').val(),
                $('input#id_longitude').val()
            );
            map.setView(center, 10, true);
        } else {
            map.locate({setView: true});
        }

        var lookupTimer = false;

        map.on("moveend", function() {
            var center = this.getCenter();
            if (lookupTimer) {
                clearTimeout(lookupTimer);
            }
            lookupTimer = setTimeout(reverseGeocode, 1500);
            $('input#id_latitude').val(center.lat);
            $('input#id_longitude').val(center.lng);
        }, map);

        /* The first time the map is hovered, scroll the page */
        $('#map').one('click', function() {
            $('html,body').animate({scrollTop: $('#map').offset().top}, 500);
        });
    };

    var getPersonPopupContent = function(person) {
        var STATIC_URL = $('body').data('static-url');
        var lat = person[0];
        var lon = person[1];
        var name = person[2];
        var username = person[3];
        var location_description = person[4];
        var photo = person[5];
        var iso_code = person[6];
        var html =  '<ul class="detailsList">' +
            '<li>' +
            '<img src="' + photo + '" alt="' + name + '" class="main">' +
            '<h3><a href="/' + username + '/">' + name + '</a></h3>' +
            '<p class="meta"><a href="/' + iso_code + '/" class="nobg">' +
            '<img src="' + STATIC_URL + 'djangopeople/img/flags/' + iso_code + '.gif"></a> ' +
            location_description + '</p>' +
            '<p class="meta"><a href="#" onclick="djangopeople.zoomOn(' + lat + ', ' + lon + '); return false;">Zoom to point</a></p>' +
            '</li>';
        return html;
    };

    var zoomOn = function(lat, lon) {
        window.MAP.panTo(new L.LatLng(lat, lon));
        window.MAP.setZoom(12);
    };

    /* Plots people on the maps and adds an info window to it
     * which becomes visible when you click the marker
     */
    var plotPeopleOnMap = function(people, map) {
        var bounds = new L.LatLngBounds();
        $.each(people, function(index, person) {
            var marker = getPersonMarker(person);
            bounds.extend(marker.getLatLng());
            marker.addTo(map);
        });
        map.fitBounds(bounds);
        return bounds;
    };

    // Creates a Marker object for a person
    var getPersonMarker = function(person) {
        var lat = person[0];
        var lon = person[1];
        var point = new L.LatLng(lat, lon);
        // custom marker options removed for now
        var marker = new L.Marker(point, {
            icon: greenIconImage(),
        });
        var info = getPersonPopupContent(person);
        marker.bindPopup(info)

        return marker;
    };

    var greenIconImage = function() {
        var STATIC_URL = $('body').data('static-url');
        var greenIcon = L.icon({
            iconUrl: STATIC_URL + 'djangopeople/img/green-bubble.png',
            shadowUrl: STATIC_URL + 'djangopeople/img/green-bubble-shadow.png',
            iconSize:     [32, 32], // size of the icon
            shadowSize:   [32, 32], // size of the shadow
            iconAnchor:   [16, 32], // point of the icon which will correspond to marker's location
            shadowAnchor: [10, 32],  // the same for the shadow
            popupAnchor:  [0, -32] // point from which the popup should open relative to the iconAnchor
        });
        return greenIcon;
    };

    var shrinkMap = function(map, latlng) {
        // Center map
        map.panTo(latlng);

        var ShrinkMapControl = L.Control.extend({
            options: {
                position: 'bottomleft'
            },

            onAdd: function (map) {
                // create the control container with a particular class name
                var container = L.DomUtil.create('div', 'shrinkControl');
                container.innerHTML = 'Shrink map';
                L.DomEvent.addListener(container, 'click', this.onClick, this);

                return container;
            },

            onClick: function () {
                $('#map').css({'cursor': 'pointer'}).attr(
                    'title', 'Activate larger map'
                );
                $('#map').animate({
                    height: '7em',
                    opacity: 0.6
                }, 500, 'swing', function() {
                    map._onResize()
                    $('#map').click(onMapClicked);
                    shrinkControl.removeFrom(map);
                });

            }
        });
        var shrinkControl = new ShrinkMapControl();

        /* Map enlarges and becomes active when you click on it */
        $('#map').css({'cursor': 'pointer', 'opacity': 0.6}).attr(
                'title', 'Activate larger map'
                );
        function onMapClicked() {
            $('#map').css({'cursor': ''}).attr('title', '');
            $('#map').animate({
                height: '25em',
                opacity: 1.0
            }, 500, 'swing', function() {
                map._onResize()

                // Unbind event so user can actually interact with map
                $('#map').unbind('click', onMapClicked);
                shrinkControl.addTo(map);
            });
        }
        $('#map').click(onMapClicked);


        // Marker for the current profile, not clickable
        var marker = new L.Marker(latlng, {
            icon: greenIconImage(),
        }).addTo(map);
    };

    /**
     * Djangopeople API
     */
    window.djangopeople = {
        handleFormGeoElements: handleFormGeoElements,
        plotPeopleOnMap: plotPeopleOnMap,
        zoomOn: zoomOn,
        shrinkMap: shrinkMap,
    };

    /**
     * plugins
     */
    $.extend($.fn, {
        yellowFade: function() {
            return this.css({
                'backgroundColor': 'yellow',
            }).animate({
                'backgroundColor': 'white',
            }, 1500);
        },
    });

    /**
     * commons
     */
    $(function() {
        // Inline login form
        $('div.nav a.login').click(function() {
            $('div#hiddenLogin').show().css({
                position: 'absolute',
                top: $(this).offset().top + $(this).height() + 7,
                left: $(this).offset().left
            });
            $('#id_usernameH').focus();
            return false;
        });

        // Profile
        $('#editSkills').hide();
        $('ul.tags li.edit a').toggle(
            function() {
                $('#editSkills').show();
                return false;
            },
            function() {
                $('#editSkills').hide();
                return false;
            }
        );
    });
})(jQuery);
