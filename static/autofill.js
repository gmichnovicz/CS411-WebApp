var placeSearch, autocomplete, geocoder;

function initAutocomplete() {
  geocoder = new google.maps.Geocoder();
  autocomplete = new google.maps.places.Autocomplete(
      (document.getElementById('autocomplete')));

  autocomplete.addListener('place_changed', fillInAddress);
}



function fillInAddress() {
  var place = autocomplete.getPlace()
}