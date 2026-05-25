$(document).ready(function () {

  function initHomepageTeamEditor() {
    var componentType = (
      $("#component-info").attr("component-type") || ""
    ).trim();
    if (componentType !== "HomepageComponent") {
      return;
    }

    var formTable = $("table.writehat-form");
    if (!formTable.length) {
      return;
    }

    var pairs = [];
    for (var i = 1; i <= 5; i++) {
      var nameInput = $("#id_teamMember" + i + "Name");
      var roleInput = $("#id_teamMember" + i + "Role");
      if (!nameInput.length || !roleInput.length) {
        continue;
      }

      pairs.push({
        index: i,
        nameInput: nameInput,
        roleInput: roleInput,
        nameRow: nameInput.closest("tr"),
        roleRow: roleInput.closest("tr"),
      });
    }

    if (!pairs.length) {
      return;
    }

    var firstRow = pairs[0].nameRow;
    var editorWrapper = $(
      '<tr class="homepage-team-editor-row">' +
        "<th>Penetration Test Team</th>" +
        "<td>" +
        '<div class="homepage-team-editor"></div>' +
        '<button type="button" class="btn btn-sm btn-outline-primary mt-2" id="homepageTeamAdd">' +
        '<i class="fas fa-plus"></i> Add Team Member' +
        "</button>" +
        "</td>" +
        "</tr>",
    );

    var editorBody = editorWrapper.find(".homepage-team-editor");
    firstRow.before(editorWrapper);

    var visibleRows = 1;
    pairs.forEach(function (pair, idx) {
      var hasValue =
        (pair.nameInput.val() || "").trim().length > 0 ||
        (pair.roleInput.val() || "").trim().length > 0;
      if (hasValue) {
        visibleRows = Math.max(visibleRows, idx + 1);
      }
    });

    pairs.forEach(function (pair, idx) {
      var row = $(
        '<div class="form-row align-items-end mb-2 homepage-team-member-row" data-row-index="' +
          (idx + 1) +
          '"></div>',
      );

      var nameCol = $('<div class="col-md-6"></div>');
      var roleCol = $('<div class="col-md-6"></div>');

      nameCol.append('<label class="small text-muted mb-1">Name</label>');
      roleCol.append('<label class="small text-muted mb-1">Role</label>');

      pair.nameInput.attr("placeholder", "Team member name");
      pair.roleInput.attr("placeholder", "Team member role");

      pair.nameInput.addClass("form-control");
      pair.roleInput.addClass("form-control");

      nameCol.append(pair.nameInput);
      roleCol.append(pair.roleInput);

      row.append(nameCol).append(roleCol);
      editorBody.append(row);

      if (idx + 1 > visibleRows) {
        row.hide();
      }

      pair.nameRow.remove();
      pair.roleRow.remove();
    });

    function updateAddButtonState() {
      var hiddenRows = editorBody.find(".homepage-team-member-row:hidden");
      if (hiddenRows.length) {
        $("#homepageTeamAdd").show();
      } else {
        $("#homepageTeamAdd").hide();
      }
    }

    $("#homepageTeamAdd")
      .off("click")
      .on("click", function () {
        var nextHidden = editorBody
          .find(".homepage-team-member-row:hidden")
          .first();
        if (nextHidden.length) {
          nextHidden.show();
        }
        updateAddButtonState();
      });

    updateAddButtonState();
  }

  function buildTargetSummaryScoresEditor() {
    var textarea = $("#id_scores");
    if (!textarea.length) {
      return;
    }

    var scoreOptions = [
      "INSERT SCORE",
      "CRITICAL",
      "HIGH",
      "MEDIUM",
      "LOW",
      "INFO",
    ];
    var lines = (textarea.val() || "").split(/\r?\n/);
    var rows = [];

    lines.forEach(function (rawLine) {
      var line = (rawLine || "").trim();
      if (!line || line.startsWith("#")) {
        return;
      }

      var separator =
        line.indexOf("|") >= 0 ? "|" : line.indexOf("=") >= 0 ? "=" : null;
      var target = "";
      var score = "INSERT SCORE";

      if (separator) {
        var parts = line.split(separator);
        target = (parts.shift() || "").trim();
        score =
          (parts.join(separator) || "").trim().toUpperCase() || "INSERT SCORE";
      } else {
        target = line;
      }

      if (target) {
        rows.push({ target: target, score: score });
      }
    });

    if (!rows.length) {
      return;
    }

    var wrapper = $('<div class="target-summary-scores-editor mt-2"></div>');
    rows.forEach(function (row, index) {
      var rowEl = $('<div class="form-row mb-2 align-items-center"></div>');
      var targetCol = $('<div class="col-sm-8"></div>');
      var scoreCol = $('<div class="col-sm-4"></div>');

      targetCol.append(
        $('<label class="mb-0 font-weight-bold"></label>').text(row.target),
      );

      var select = $('<select class="form-control form-control-sm"></select>');
      scoreOptions.forEach(function (opt) {
        select.append($("<option></option>").attr("value", opt).text(opt));
      });
      if (scoreOptions.indexOf(row.score) < 0) {
        select.append(
          $("<option></option>").attr("value", row.score).text(row.score),
        );
      }
      select.val(row.score);
      select.attr("data-target-index", index);
      scoreCol.append(select);

      rowEl.append(targetCol).append(scoreCol);
      wrapper.append(rowEl);
    });

    function syncTextarea() {
      var updated = rows
        .map(function (row) {
          return row.target + " | " + row.score;
        })
        .join("\n");
      textarea.val(updated);
    }

    wrapper.on("change", "select", function () {
      var i = parseInt($(this).attr("data-target-index"), 10);
      rows[i].score = ($(this).val() || "INSERT SCORE").trim().toUpperCase();
      syncTextarea();
    });

    textarea.hide();
    textarea.after(wrapper);
    textarea
      .siblings(
        ".editor-toolbar, .CodeMirror, .editor-preview-side, .editor-statusbar",
      )
      .hide();
    syncTextarea();
  }

  buildTargetSummaryScoresEditor();
  initHomepageTeamEditor();

  // prefill the findingGroup form field if it exists
  $('#id_findingGroup').val($("#fgroup-info").attr('fgroup-id'));
  $('#id_findingGroup').selectpicker('refresh');

  $('#componentUpdate').click(function(e) {
    e.preventDefault();
    $.ajax({
      url : $('form').attr('action') || window.location.pathname,
      type: "POST",
      data: $('form').serialize(),
      success: function (data) {
        success('Successfully saved component');
        // refresh preview iframe
        $('#preview-frame')[0].contentDocument.location.reload(true);
        $(document).trigger('saveEvent');
      },
      error: function (result) {
        error('Failed to save component');
      }
    })
  });

  // fancy select buttons
  $("select.review-status").not(".grouped").togglebutton();
  $("select.review-status").addClass("grouped");
  var groups = $("table.writehat-form .btn-group");

  groups.children("button").addClass("btn-secondary");
  groups.each(function() { 
    $(this).addClass("review-status-group");
    var buttons = $(this).children("button");
    var btnCount = buttons.length;
    buttons.each( function() { 
      $(this).addClass("reviewStatus");
    });
  });
});
