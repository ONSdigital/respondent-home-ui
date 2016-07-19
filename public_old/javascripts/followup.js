$(document).ready(function(event) {
  
  // Set the value of the field to itself after focusing it, so the entire text isn't selected.
  $("#contactname").focus().val($("#contactname").val());
  $("#visitdate").datepicker({ "dateFormat": "d M yy" });
  $("#visithours").spinner({
    spin: function(event, ui) {
      if (ui.value > 24) {
        $(this).spinner("value", 1);
        return false;
      } else if (ui.value < 1) {
        $(this).spinner("value", 24);
        return false;
      }
    }
  });

  $("#visitmins").spinner({
    step: 5,
    spin: function(event, ui) {
      if (ui.value > 60) {
        $(this).spinner("value", 1);
        return false;
      } else if (ui.value < 1) {
        $(this).spinner("value", 60);
        return false;
      }
    }
  });
});
