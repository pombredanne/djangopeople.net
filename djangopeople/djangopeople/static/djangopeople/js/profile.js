window.onload = function() {
    function ShrinkControl(button) {
        button.innerHTML = 'Shrink map';
        button.style.color = "black";
        button.style.backgroundColor = "white";
        button.style.font = "12px Arial";
        button.style.border = "1px solid black";
        button.style.padding = "2px";
        button.style.marginBottom = "3px";
        button.style.textAlign = "center";
        button.style.width = "6em";
        button.style.cursor = "pointer";

        google.maps.event.addDomListener(button, "click", function() {
            $('#gmap').css({'cursor': 'pointer'}).attr(
                'title', 'Activate larger map'
            );
            gmap.controls[google.maps.ControlPosition.BOTTOM_LEFT].clear();
            hidePeopleOnMap(peopleArray);
            $('#gmap').animate({
                height: '7em',
                opacity: 0.6
            }, 500, 'swing', function() {
                google.maps.event.trigger(gmap, 'resize');
                gmap.setCenter(personLatLng);
                gmap.setZoom(12);
                gmap.setOptions({
                    draggable: false,
                    panControl: false,
                    zoomControl: false,
                    mapTypeControl: false
                });
                $('#gmap').click(onMapClicked);
            });
        });
    }

    var personLatLng =  new google.maps.LatLng(person_latitude, person_longitude);

    var myOptions = {
        zoom: 12,
        center: personLatLng,
        mapTypeId: google.maps.MapTypeId.ROADMAP,
        draggable: false,
        disableDefaultUI: true,
        scrollwheel: false
    };
    var gmap = new google.maps.Map(document.getElementById('gmap'), myOptions);

    var shrinkButtonDiv = document.createElement('div');
    var shrinkButton = new ShrinkControl(shrinkButtonDiv);
    shrinkButtonDiv.index = 1;



    /* Map enlarges and becomes active when you click on it */
    $('#gmap').css({'cursor': 'pointer', 'opacity': 0.6}).attr(
            'title', 'Activate larger map'
            );
    function onMapClicked() {
        $('#gmap').css({'cursor': ''}).attr('title', '');
        $('#gmap').animate({
            height: '25em',
            opacity: 1.0
        }, 500, 'swing', function() {
            google.maps.event.trigger(gmap, 'resize');
            gmap.panTo(personLatLng);
            gmap.setOptions({
                draggable: true,
                panControl: true,
                zoomControl: true,
                mapTypeControl: true
            });
            showPeopleOnMap(peopleArray, gmap);

            // Unbind event so user can actually interact with map
            $('#gmap').unbind('click', onMapClicked);
        });
        gmap.controls[google.maps.ControlPosition.BOTTOM_LEFT].push(shrinkButtonDiv);
    }
    $('#gmap').click(onMapClicked);

    var marker = new google.maps.Marker({
        position: personLatLng,
        map: gmap,
        icon: greenIconImage(),
        shadow: greenIconShadow()

    });

    //gets an array of person map markers, used for hiding and showing them on
    //the map
    var peopleArray = getPeopleArray(nearby_people);

};

jQuery(function($) {
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
