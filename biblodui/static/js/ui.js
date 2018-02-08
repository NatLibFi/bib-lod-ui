$(document).ready(function() {
    if (window.location.hash != "") {
      /* show the tab identified by the hash part of the URL */
      $('#instances a[href="' + window.location.hash + '"]').tab('show');
    } else {
      /* show the first tab */
      $('#instances a:first').tab('show');
    }
});

$('#query').autocomplete({
    minChars: 3,
    preventBadQueries: false,
    showNoSuggestionNotice: true,
    noSuggestionNotice: "No results",
    lookup: function (query, done) {
        $.get('/bib/search.xml?query=' + query, function(data) {
          var xml = $(data);
          var items = [];
          xml.find("item").each(function() {
            var $this = $(this),
              item = {
                value: $this.find("category").text() + ": " + $this.find("title").text() + " (" + $this.find("link").text().split('/').pop() + ")",
                data: {
                  type: $this.find("category").text(),
                  uri: $this.find("link").text()
                }
              }
            items.push(item);
          });
          var result = { suggestions: items };
          done(result);
        });
    },
    onSearchStart: function (query) {
      $(this).addClass("spin");
    },
    onSearchComplete: function (query, suggestions) {
      $(this).removeClass("spin");
    },
    onSearchError: function (query, jqXHR, textStatus, errorThrown) {
      $(this).removeClass("spin");
    },
    onSelect: function (suggestion) {
        window.location.href = suggestion.data.uri;
    },
    deferRequestBy: 500
});

function loadQuery (query_id) {
    $.ajax("/static/sparql/" + query_id + ".rq", {
        dataType: 'text',
        success: function (data) {
            yasgui.current().setQuery(data);
            yasgui.current().yasqe.query();
        }
    });
}
