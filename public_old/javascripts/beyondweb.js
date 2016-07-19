$(document).keyup(function(event) {
  if ($("#postcode").is(":focus") && (event.keyCode == 13)) {
    var postcode = $("#postcode").val();
    if (postcode.length > 0) {
      postcode = postcode.replace(/\s+/g, '');
      postcode = postcode.toUpperCase();
      window.location = "/postcode/" + postcode;
    }
  }
});
