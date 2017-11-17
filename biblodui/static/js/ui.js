$(document).ready(function() {
    if (window.location.hash != "") {
      /* show the tab identified by the hash part of the URL */
      $('#instances a[href="' + window.location.hash + '"]').tab('show');
    } else {
      /* show the first tab */
      $('#instances a:first').tab('show');
    }
});
