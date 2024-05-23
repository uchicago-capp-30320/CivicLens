function uncheckAgencies() {
    var agencySelect = document.getElementById('selected_agencies');
    for (var i = 0; i < agencySelect.options.length; i++) {
      agencySelect.options[i].selected = false;
    }
  }
