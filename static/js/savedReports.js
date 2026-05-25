function saveState() {
  console.log("SAVED");
  var status = {};
  $(".btn-save-state").each(function() {
    status[$(this).attr("id")] = $(this).prop("checked");
  });
  localStorage.setItem("status", JSON.stringify(status));
}

function triggerImport(importUrl, redirectUrl) {
  var input = $('<input type="file" accept=".json" style="display:none">');
  $("body").append(input);
  input.on("change", function () {
    var file = this.files[0];
    if (!file) return;
    var formData = new FormData();
    formData.append("file", file);
    $.ajax({
      url: importUrl,
      method: "POST",
      data: formData,
      processData: false,
      contentType: false,
      success: function () {
        successRedirect(redirectUrl, "Successfully imported");
      },
      error: function (xhr) {
        error("Import failed: " + (xhr.responseText || "unknown error"));
      },
    });
    input.remove();
  });
  input.click();
}

$(document).ready(function() {

  if (localStorage.getItem("status")) {
    var savedStatus = JSON.parse(localStorage.getItem("status"));
    if (savedStatus) {
      $(".btn-save-state").each(function() {
        var id = $(this).attr("id");
        if (savedStatus.hasOwnProperty(id)) {
          $(this).prop("checked", savedStatus[id]);
          $(this).closest("label").toggleClass("active", savedStatus[id]);
        }
      });
    }
  }

  // Custom range filtering function
  $.fn.dataTable.ext.search.push(function (settings, data, dataIndex) {
    if (settings.nTable.id !== "reports") {
      return true
    }

    let wrapper = $(settings.nTableWrapper)

    let itemStatus = data[4];
    let name = data[0].toLowerCase()
    let query = wrapper.find('[type="search"]').val().toLowerCase()

    selected_status = $(`input[name='status'][value='${itemStatus}']:checked`).length === 1;
    searched_name = name.indexOf(query) != -1

    return selected_status && searched_name

  });

  var table = $('#reports').DataTable();

  // Bind the change event handler
  $('#status-radio').change(function() {
    saveState();
      table.draw();
  });

  // Trigger the change event to set the filter active by default
  $('#status-radio').trigger('change');

  // Export report template
  $('.writehat-reports').on('click', '.reportTemplateExport', function(e) {
    var reportID = $(e.currentTarget).closest('tr').attr('report-id');
    window.location.href = `/templates/export/${reportID}`;
  });

  // Import report template
  $('#reportTemplateImport').click(function() {
    triggerImport('/templates/import', '/templates');
  });

  // Export page template
  $('#writehat-pagetemplates').on('click', '.pageTemplateExport', function(e) {
    var pageID = $(e.currentTarget).closest('tr').attr('page-id');
    window.location.href = `/pages/export/${pageID}`;
  });

  // Import page template
  $('#pageTemplateImport').click(function() {
    triggerImport('/pages/import', '/templates');
  });

});