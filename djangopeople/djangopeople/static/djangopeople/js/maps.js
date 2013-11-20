function makeWindow(name, username, location, photo, iso_code, lat, lon) {
    var html =  '<ul class="detailsList">' + 
        '<li>' + 
        '<img src="' + photo + '" alt="' + name + '" class="main">' + 
        '<h3><a href="/' + username + '/">' + name + '</a></h3>' + 
        '<p class="meta"><a href="/' + iso_code + '/" class="nobg">' + 
        '<img src="' + STATIC_URL + 'djangopeople/img/flags/' + iso_code + '.gif"></a> ' + 
        location + '</p>' + 
        '<p class="meta"><a href="#" onclick="zoomOn(' + lat + ', ' + lon + '); return false;">Zoom to point</a></p>' +
        '</li>';
    return html;
}

function zoomOn(lat, lon) {
    //gmap.closeInfoWindow();
    gmap.setCenter(new google.maps.LatLng(lat, lon));
    gmap.setZoom(12);
}

/* Plots people on the maps and adds an info window to it
 * which becomes visible when you click the marker
 */
function plotPeopleOnMap(people, gmap) {
    var bounds = new google.maps.LatLngBounds();
    $.each(people, function(index, person) {
        var marker = getPersonMarker(person);
        var infoWindow = getPersonInfoWindow(person);
        marker.setMap(gmap);
        bounds.extend(marker.getPosition());
        // Hook up the marker click event
        google.maps.event.addListener(marker, 'click', function() {
            infoWindow.open(gmap, marker);
        });
    });   

    return bounds;
}


function hidePeopleOnMap(peopleArray) {
    if (peopleArray) {
        for (i in peopleArray) {
            peopleArray[i].setMap(null);
        }
    }
}

function showPeopleOnMap(peopleArray, gmap) {
    if (peopleArray) {
        for (i in peopleArray) {
            peopleArray[i].setMap(gmap);
        }
    }
}

// Creates a Marker object for a person
function getPersonMarker(person) {
    var lat = person[0];
    var lon = person[1];
    var point = new google.maps.LatLng(lat, lon);
    // custom marker options removed for now
    var marker = new google.maps.Marker({
        position: point,
        icon: greenIconImage(),
        shadow: greenIconShadow()
    });

    return marker;
}

// Creates a info dialog for a person
function getPersonInfoWindow(person) {
    var lat = person[0];
    var lon = person[1];
    var name = person[2];
    var username = person[3];
    var location_description = person[4];
    var photo = person[5];
    var iso_code = person[6];

    var infoWindow = new google.maps.InfoWindow({
        content: makeWindow(
                     name, username, location_description, photo, iso_code, 
                     lat, lon
                     )
    });

    return infoWindow;
}

/* Creates an array of person Markers for easier toggling
 * of their visibility on the map. 
 */
function getPeopleArray(peopleList) {
    var peopleArray = [];
    $.each(peopleList, function(index, person) {
        var marker = getPersonMarker(person);
        peopleArray.push(marker);
    });

    return peopleArray;
}

function greenIconImage() {
    var greenIcon = new google.maps.MarkerImage(STATIC_URL + 'djangopeople/img/green-bubble.png',
            new google.maps.Size(32, 32),
            new google.maps.Point(0, 0),
            new google.maps.Point(16, 32)
            );
    return greenIcon;
}

function greenIconShadow() {
    var greenIconShadow = new google.maps.MarkerImage(STATIC_URL + 'djangopeople/img/green-bubble-shadow.png',
            new google.maps.Size(49, 32),
            new google.maps.Point(0, 0),
            new google.maps.Point(16, 32)
            );
    return greenIconShadow;
}

