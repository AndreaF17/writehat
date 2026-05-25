function postFigureMetadata(findingID) {
  if (inEngagements()) {
    let figureMetadata = [];
    let forceUpdate = false;
    $('.figureItem').each(function() {
      if ( $(this).attr('id') != 'dummyFigureItem' ) {
        let figureID = $(this).attr('figure-id');
        let figureCaption = $(this).find('.figure-caption').text();
        let figureSize = $(this).attr('figure-size');
        figureMetadata.push({
          'guid': figureID,
          'size': figureSize,
          'caption': figureCaption
        })
      } else if ($(this).attr('id') === 'dummyFigureItem' && $(this).prop('forceUpdate') === true) {
        forceUpdate = true
      } else {
        // continue
        return;
      }
    })
    if ((figureMetadata && figureMetadata.length) ||
        (figureMetadata.length === 0 && forceUpdate)) {
      $.ajax({
        url: `/images/finding/${findingID}/edit`,
        type:'post',
        data: JSON.stringify(figureMetadata),
        success: function(response) {
          success('Successfully saved figure metadata');
        },
        error: function(response) {
          error('Failed to update figure metadata');
        }
      })
    }
  }
}


function setCategoryID() {
  var categoryID = $('#finding-info').attr('category-id');
  $('#id_categoryID').val(categoryID);
  $('.selectpicker').selectpicker('refresh')
}


let findingPreviewTimer = null;

function configureFindingSplitPaneLayout() {
  var paneContent = $("#writehat-content .paneContent");
  if (!paneContent.length) {
    return;
  }

  paneContent.css({
    height: "85vh",
    overflow: "hidden",
  });

  paneContent.children(".pane").css({
    height: "100%",
    overflowY: "hidden",
  });

  $("#leftPane").css("overflowY", "auto");
  $("#rightPane").css({
    overflowY: "hidden",
    overflowX: "hidden",
  });

  var findingPreview = document.getElementById("findingPreview");
  if (findingPreview && findingPreview.style) {
    findingPreview.style.setProperty("overflow-y", "auto", "important");
    findingPreview.style.setProperty("overflow-x", "hidden", "important");
  }
}

function fitFindingPreviewPage(previewDocument) {
  if (!previewDocument || !previewDocument.documentElement) {
    return;
  }

  var page = previewDocument.querySelector("section.container.component.part");
  if (!page) {
    return;
  }

  var viewportWidth = previewDocument.documentElement.clientWidth || 0;
  var pageWidthPx = 8.5 * 96;
  var gutterPx = 24;
  var scale = Math.min(1, (viewportWidth - gutterPx) / pageWidthPx);

  if (!isFinite(scale) || scale <= 0) {
    scale = 1;
  }

  previewDocument.documentElement.style.setProperty(
    "--finding-preview-scale",
    String(scale),
  );

  var scaledPageHeight = Math.ceil(page.scrollHeight * scale + gutterPx);

  if (previewDocument.body) {
    previewDocument.body.style.minHeight = scaledPageHeight + "px";
  }

  var frameElement =
    previewDocument.defaultView && previewDocument.defaultView.frameElement;
  if (frameElement) {
    frameElement.style.height = scaledPageHeight + "px";
    frameElement.style.minHeight = scaledPageHeight + "px";
  }
}

function bindFindingPreviewWheelProxy(previewDocument) {
  if (!previewDocument || previewDocument.__findingWheelProxyBound) {
    return;
  }

  var frameElement =
    previewDocument.defaultView && previewDocument.defaultView.frameElement;
  if (!frameElement) {
    return;
  }

  var scrollContainer = frameElement.closest("#findingPreview");
  if (!scrollContainer) {
    return;
  }

  previewDocument.addEventListener(
    "wheel",
    function (event) {
      if (!event || typeof event.deltaY !== "number") {
        return;
      }

      var maxScroll =
        scrollContainer.scrollHeight - scrollContainer.clientHeight;
      if (maxScroll <= 0) {
        return;
      }

      scrollContainer.scrollTop += event.deltaY;
      event.preventDefault();
    },
    { passive: false },
  );

  previewDocument.__findingWheelProxyBound = true;
}

function applyFindingPreviewOverrides(previewDocument) {
  if (!previewDocument) {
    return;
  }

  var styleId = "finding-preview-overrides";
  var existingStyle = previewDocument.getElementById(styleId);
  if (existingStyle) {
    existingStyle.remove();
  }

  var styleNode = previewDocument.createElement("style");
  styleNode.id = styleId;
  styleNode.textContent = `
    :root {
      --finding-preview-page-width: 8.5in;
      --finding-preview-scale: 1;
    }

    html, body {
      margin: 0;
      padding: 0;
      background: #ececec;
      height: 100%;
    }

    html {
      overflow: hidden;
    }

    body {
      display: flex;
      justify-content: center;
      overflow: hidden;
    }

    .container.component.part {
      --page-content-width: calc(var(--finding-preview-page-width) - 2rem);
      --page-content-height: auto;
      flex: 0 0 auto;
      flex-shrink: 0;
      width: var(--finding-preview-page-width);
      max-width: none;
      max-height: none;
      padding: 1rem;
      margin: .75rem 0;
      box-sizing: border-box;
      background: #fff;
      transform: scale(var(--finding-preview-scale));
      transform-origin: top center;
    }

    .finding-header {
      display: flex;
      flex-direction: row !important;
      align-items: stretch;
      min-width: 0;
    }

    .finding-severity {
      flex: 0 0 11rem !important;
      width: 11rem !important;
      min-width: 11rem !important;
      max-width: 11rem !important;
      height: auto !important;
      box-sizing: border-box;
      padding: 1rem .5rem;
      line-height: 1.2;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      text-align: center;
      overflow-wrap: anywhere;
      word-break: break-word;
    }

    .finding-title {
      flex: 1 1 auto;
      min-width: 0;
      width: auto;
      max-width: none;
      height: auto !important;
      box-sizing: border-box;
      padding: 1rem !important;
      display: flex;
      align-items: center;
    }

    .finding {
      height: auto !important;
      min-height: 0 !important;
      overflow: visible !important;
    }

    .finding-table {
      height: auto !important;
      min-height: 0 !important;
      flex-grow: 0 !important;
      width: 100%;
      max-width: 100%;
      overflow: visible !important;
    }

    .finding-content {
      display: flex;
      flex-direction: row;
      align-items: stretch;
      min-width: 0;
      height: auto !important;
      width: 100%;
      max-width: 100%;
      box-sizing: border-box;
    }

    .finding-content-header {
      float: none;
      flex: 0 0 11rem;
      min-width: 11rem;
      max-width: 11rem;
      height: auto !important;
      box-sizing: border-box;
    }

    .finding-content-body {
      margin-left: 0;
      width: auto;
      max-width: none;
      min-width: 0;
      flex: 1 1 auto;
      height: auto !important;
      box-sizing: border-box;
      overflow-wrap: anywhere;
      word-break: break-word;
    }

    .finding .finding-content:last-child {
      height: auto !important;
    }

    .finding-content-header.cvss-vector + .finding-content-body {
      word-break: break-all;
    }

    .finding-content-body pre,
    .finding-content-body code {
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      word-break: break-word;
    }

    .finding-content-body pre {
      width: 100%;
      max-width: 100%;
      margin-right: 0;
      box-sizing: border-box;
      overflow-wrap: anywhere;
      word-break: break-all;
    }

    .finding-content-body pre code {
      display: block;
      width: 100%;
      max-width: 100%;
      box-sizing: border-box;
      margin: 0;
    }

    .finding,
    .finding-table {
      overflow-x: visible;
    }
  `;

  if (previewDocument.head) {
    previewDocument.head.appendChild(styleNode);
  } else if (previewDocument.documentElement) {
    previewDocument.documentElement.appendChild(styleNode);
  }

  bindFindingPreviewWheelProxy(previewDocument);
  fitFindingPreviewPage(previewDocument);
}

function refreshFindingPreview() {
  var previewFrame = $("#finding-preview-frame")[0] || $("#preview-frame")[0];
  var previewURL = $("#finding-info").attr("finding-preview-url");
  var form = $("#findingForm");

  if (!previewFrame || !previewURL || !form.length) {
    return;
  }

  $.ajax({
    url: previewURL,
    type: "POST",
    data: form.serialize(),
    success: function (response) {
      var previewDocument =
        previewFrame.contentDocument || previewFrame.contentWindow.document;
      previewDocument.open();
      previewDocument.write(response);
      previewDocument.close();
      applyFindingPreviewOverrides(previewDocument);
    },
    error: function () {
      // best effort: avoid noisy errors while form values are mid-edit
    },
  });
}

function queueFindingPreviewRefresh(delay = 300) {
  clearTimeout(findingPreviewTimer);
  findingPreviewTimer = setTimeout(refreshFindingPreview, delay);
}

function bindFindingPreviewEvents() {
  var form = $("#findingForm");
  if (
    !form.length ||
    !($("#finding-preview-frame").length || $("#preview-frame").length)
  ) {
    return;
  }

  form.off(".findingPreview");
  form.on(
    "input.findingPreview change.findingPreview",
    "input, textarea, select",
    function () {
      queueFindingPreviewRefresh();
    },
  );

  $(".CodeMirror").off(".findingPreview");
  $(".CodeMirror").on("keyup.findingPreview paste.findingPreview", function () {
    queueFindingPreviewRefresh();
  });

  $(window).off("resize.findingPreview");
  $(window).on("resize.findingPreview", function () {
    var previewFrame = $("#finding-preview-frame")[0] || $("#preview-frame")[0];
    if (!previewFrame) {
      return;
    }

    var previewDocument =
      previewFrame.contentDocument ||
      (previewFrame.contentWindow && previewFrame.contentWindow.document);
    fitFindingPreviewPage(previewDocument);
  });

  queueFindingPreviewRefresh(0);
}


function findingSave() {
  let form = $('.writehat-form').closest('form');
  let post_url = form.attr('action');
  if (inEngagements()) {
    var engagementID = $('#engagement-info').attr('engagement-id');
    var redirectURL = '/engagements/fgroup/finding/edit/';
  } else {
    var redirectURL = '/findings/edit/';
  }
  // submit form
  $.ajax({
    url: post_url,
    type:'post',
    data: form.serialize(),
    success: function(findingID) {
      postFigureMetadata(findingID);
      var successMsg = 'Successfully saved finding';
      if (window.location.pathname.includes('/edit/')) {
        success(successMsg);
        $(document).trigger('saveEvent');
      } else {
        successRedirect(redirectURL + findingID, successMsg);
      }
    },
    error: function() {
      error('Failed to save finding');
    }
  })
}


// Update the CVSS/CVSS4/DREAD vector string and severity based on current selections
function updateRiskBadge() {

  var form = $('.writehat-form').closest('form');
  var form_data = form.serialize();
  var badgeContent = $('.risk-badge').text().trim().toUpperCase();

  // determine scoring type based on form fields
  if ($("#id_cvss4AV").length) {
    var scoringType = "CVSS4";
  } else if ($("#id_cvssAV").length) {
    var scoringType = "CVSS";
  } else if ($("#id_dreadDamage").length) {
    var scoringType = "DREAD";
  } else {
    var scoringType = "PROACTIVE";
    $(".risk-badge").attr("finding-severity", "Proactive");
    $(".risk-badge .textButton-text").text("Proactive");
  }

  if (scoringType != 'PROACTIVE') {
    // submit form
    $.post({
      url: `/validation/${scoringType}`.toLowerCase(),
      data: form.serialize(),
      success: function(response) {
        // update badge color
        $('.risk-badge').attr('finding-severity', response['severity']);
        // update badge text
        var severity = `${scoringType}: ${response['score'].toFixed(1)} ${response['severity']}`;
        $('.risk-badge .textButton-text').text(severity);
        // update vector string
        $('.risk-badge-content .dropdown-content').html(
          `<input value="${response['vector']}" style="min-width: 20rem"></input>`
        );
      },
      error: function() {
        error(`Failed to generate ${scoringType} preview`);
      }
    })
  }

}


function loadFigureSortable() {
  if($('#manageFiguresContent').length) {
    try {
      figureSortable.destroy();
    } catch {
      // ignore if sortable doesn't exist
    }
    figureSortable = new Sortable(manageFiguresSortable, {
      animation: 150,
    })
  }

  // figure delete
  $('.figureDelete').off().click(function(e) {
    e.stopPropagation();
    $(this).closest('.figureItem').remove();
    if ($('.figureItem').length === 1) {
      const dummy = $('.figureItem').first()
      if (dummy.prop("id") === "dummyFigureItem") {
        console.debug("Last figure deleted; setting forceUpdate on dummy item")
        dummy.prop("forceUpdate", true)
      }
    }
  })

  // figure edit
  $('.figureEdit').off().click(function(e) {

    e.stopPropagation();
    var figureItem = $(e.currentTarget).closest('.figureItem')
    var src = figureItem.find('img').attr('src');
    var caption = figureItem.find('.figure-caption').text();
    var size = figureItem.attr('figure-size');

    var readyEvent = 'figureEditReadyEvent';
    var imageEditor = new ImageUploader(inline=false, editing=true);

    $( document ).off(ImageUploader.editSuccessEvent);
    $( document ).on(ImageUploader.editSuccessEvent, function(e, figureID, caption, size) {
      console.log('editSuccessEvent');
      figureItem.find('.figure-caption').text(caption);
      figureItem.attr('figure-size', size);
      $('.modal').modal('hide');
    })

    $( document ).off(ImageUploader.readyEvent);
    $( document ).on(ImageUploader.editReadyEvent, function() {
      imageEditor.edit(src, caption, size);
      $( document ).off(ImageUploader.editReadyEvent);
    })
  })

  // figure upload
  $('#figureNew').off().click(function(e) {
    $( document ).off(ImageUploader.readyEvent);
    var imageUploader = new ImageUploader(input=null, inline=false);
    imageUploader.select();
  })
}


function refreshFigures() {
  if (inEngagements()) {
    loadPane('findingsFiguresList', 'manageFiguresContent', success_callback=function() {
      loadFigureSortable()
      $( document ).trigger( 'figuresRefresh' );
    })
  }
}

function showAdvancedCheckbox() {
  if (scoringType == "CVSS" || scoringType == "CVSS4") {
    // create new row for advanced checkbox
    if (!$("#advanced-choices-row").length) {
      $(".writehat-form tr:nth-child(18)").after(
        '<tr id="advanced-choices-row"><th class="text-warning">Show Advanced:</th><td></td></tr>',
      );
      $("#show-advanced-choices")
        .detach()
        .appendTo("#advanced-choices-row > td");
    }

    // show/hide when toggled
    $("#finding-advanced-checkbox")
      .off()
      .change(function () {
        if (this.checked) {
          $(".finding-advanced-choice").each(function () {
            $(this).closest("tr").show();
          });
        } else {
          $(".finding-advanced-choice").each(function () {
            $(this).closest("tr").hide();
          });
        }
      });

    // hide advanced options by default
    var advanced_choices = $(".finding-advanced-choice");
    var advanced_choice_values = advanced_choices
      .map(function (x, y) {
        return y.value;
      })
      .toArray();

    // unless one of them has been changed already
    if (
      !advanced_choice_values.some(function (v) {
        return v !== "X";
      })
    ) {
      advanced_choices.each(function () {
        $(this).closest("tr").hide();
      });
    } else {
      $("#finding-advanced-checkbox").click();
    }
  } else {
    // TODO: hide DREAD Descriptions and Affected Resources

    $("#show-advanced-choices").hide();
  }
}


function refreshJS() {
  configureFindingSplitPaneLayout();

  // update risk preview
  updateRiskBadge();

  // stop dropdowns from closing when clicking inside
  $('.figure-caption').on("click.bs.dropdown", function (e) {
    e.stopPropagation();
    e.preventDefault();
  });

  // fancy select buttons
  $("select").not(".selectpicker").not(".grouped").togglebutton();
  $("select").not(".selectpicker").addClass("grouped");
  var groups = $("table.writehat-form .btn-group");

  groups.children("button").addClass("btn-secondary");
  groups.each(function() { 
    var buttons = $(this).children("button");
    var btnCount = buttons.length;
    buttons.each( function() { 
      $(this).addClass("n" + btnCount);
    });
  });

  showAdvancedCheckbox();

  // update the risk badge when selectors are changed
  $("select[name^='cvss'], select[name^='dread']").change(updateRiskBadge);

  loadToolTips();
  loadMarkdown();
  $('.selectpicker').selectpicker();
  refreshFigures();
  bindFindingPreviewEvents();
}


function loadBlankForm() {
  console.log('loadBlankForm');
  $('#formDiv').show();
  $('#leftHeader').html('New Engagement Finding (blank form)');
  $('#findingForm').attr("action", formURL);
  $('#findingDatabaseSelect-modal').off('hide.bs.modal');
  $('#findingDatabaseSelect-modal').modal('hide');
  refreshJS();
}


function loadImportedForm() {
  console.log('loadImportedForm');
  $.ajax(
    {
      url : '/engagements/fgroup/' + $("#fgroup-info").attr('fgroup-id') + '/finding/import/' + $("#id_finding").val(),
      type: 'GET',
      contentType: 'application/json; charset=utf-8',
      dataType: 'html',
      success: function(data)
      {
        $('#leftHeader').html('New Engagement Finding (' + $("#id_finding option:selected" ).text() + ')');
        $('#findingDatabaseSelect-modal').modal('hide');
        $('#formDiv').html(data);
        //$('#id_categoryID').selectpicker();
        $('#findingForm').attr("action",formURL);
        $('#formDiv').show();
        refreshJS();
        setCategoryID();
        $('#id_findingGroup').val($("#fgroup-info").attr('fgroup-id'));
        $('#id_findingGroup').selectpicker('refresh');
        
        $('.categoryAddButton').off().click(function() {
          $('#categoryAdd-modal').modal('show');
        })
      },
      error: function()
      {
        error('Failed to import finding')
      }

    }
  )
}


function loadToolTips() {
  $('.tooltipSelect').click(function(e){
    var buttonID = $(e.currentTarget).attr('id').split('-');
    var fieldName = buttonID[buttonID.length-1];

    loadModal('tooltipSelect', function(tooltipSelectModal) {
      
      if (scoringType == 'DREAD'){
        $('#tooltipSelect-modalLabel').text('DREAD Info');
      }
      
      if (scoringType == 'CVSS'){
        $('#tooltipSelect-modalLabel').text('CVSS Info');
      }

      if (scoringType == "CVSS4") {
        $("#tooltipSelect-modalLabel").text("CVSS4 Info");
      }
  
      tooltipSelectModal.modal('show');
      selectedTooltipText = $('#tooltipText-'+fieldName).html();
      tooltipSelectModal.find('.modal-body').html(selectedTooltipText);
    })
  })
}


$(document).ready( function() {

  setCategoryID();

  // prevent cvss badge dropdown from closing on click
  $('.risk-badge-content .dropdown-content').click(function(e) {e.stopPropagation();})
  $('.dread-badge-content .dropdown-content').click(function(e) {e.stopPropagation();})

  // back button
  $('#backButton').click(function() {
    if (inEngagements()) {
      var engagementID = $('#engagement-info').attr('engagement-id');
      redirect(`/engagements/edit/${engagementID}`);
    } else {
      redirect('/findings');
    }
  })

  engagementID = $('#engagement-info').attr('engagement-id');
  fgroupID = $('#fgroup-info').attr('fgroup-id');
  scoringType = $('#fgroup-info').attr('fgroup-type');
  formURL = `/engagements/fgroup/${fgroupID}/finding/create`;

  //set the finding group ID
 $('#id_findingGroup').val(fgroupID);
 $('#id_findingGroup').selectpicker('refresh');

  // submit button
  $('#findingSave').click(function(e) {
    findingSave();
  });

  // saveToTemplate button
  $('#findingExport').click(function(e) {
    var findingID = $('#finding-info').attr('finding-id');
    successRedirect(
      `/findings/import/${findingID}`,
      'Successfully retrieved finding data',
      newTab=true
    )
  })
  

  // finding delete
  $('#findingDelete').click(function(e) {

    var findingName = $('#finding-info').attr('finding-name');

    promptModal(
      confirm_callback=function(e) {
        var findingID = $('#finding-info').attr('finding-id');
        if (inEngagements()) {
          var fgroupId = $('#fgroup-info').attr('fgroup-id');
          var deleteURL = `/engagements/fgroup/finding/delete/${findingID}`;
          var redirectURL = `/engagements/edit/${engagementID}`;
        } else {
          var deleteURL = `/findings/delete/${findingID}`;
          var redirectURL = `/findings`;
        }
        $.ajax({url: deleteURL, 
          type: 'POST',
          success: function(result) {
            successRedirect(redirectURL, `Successfully deleted finding "${findingName}"`);
          },
          error: function(result) {
            error(`Failed to delete finding "${findingName}"`);
          }
        })
      },
      title='Delete Finding?',
      body=`Are you sure you want to delete **${findingName}**?`,
      leftButtonName='Cancel',
      rightButtonName='Delete Finding',
      danger=true
    )

  });



  if ( ! inEngagements() ) {
    $(".finding-database-exclude").each(function(){
      $(this).closest('tr').hide();
    })
  }

  if ( inEngagements() || window.location.pathname.includes('/findings/')) {
    refreshJS();
  } 

  // figure upload
  $( document ).on(ImageUploader.successEvent, function(e, figureID, caption, size) {
    if (!(inline)) {
      $('.modal').modal('hide');
      let newFigure = $('#dummyFigureItem').clone();
      newFigure.removeAttr('id');
      newFigure.find('.figure-caption').text(caption);
      newFigure.find('img').attr('src', '/images/' + figureID);
      newFigure.attr('figure-id', figureID);
      newFigure.attr('figure-size', size);
      newFigure.find('[figure-id]').each(function() {
        $(this).attr('figure-id', figureID);
      })
      newFigure.show();
      $('#manageFiguresSortable').append(newFigure);
      loadFigureSortable();
    }
  })

  // open the "import finding" modal if we're in engagements
  if ( inEngagements() && window.location.pathname.includes('/finding/new') ) {
    loadModal('findingDatabaseSelect', function(findingDatabaseSelectModal) {
      findingDatabaseSelectModal.modal('show');
      // load a blank form if the modal is closed
      findingDatabaseSelectModal.on('hide.bs.modal', loadBlankForm)
      $('#loadBlankForm').click(loadBlankForm);
      $('#loadImportedForm').click(function() {
        // cancel the loading of the blank form
        findingDatabaseSelectModal.unbind();
        loadImportedForm();
      })
      // simulate a click on the selectpicker
      $('.selectpicker').on('loaded.bs.select', function() {
        $('button.btn.dropdown-toggle.btn-light').click();
      })
      $('#id_finding').selectpicker();
    })
  }

})
