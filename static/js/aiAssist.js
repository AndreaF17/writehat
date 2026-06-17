/*
 * AI assistant for the component and finding editors.
 *
 * Driven entirely by an #ai-config element on the page:
 *   data-enabled        "true" to activate
 *   data-generate-url   POST {field} -> { text }
 *   data-prompt-url     POST {field, prompt} -> { prompt, hasOverride }
 *   data-save-selector  selector of the page's Save button (clicked after a draft)
 * plus an #ai-fields-data <script type="application/json"> map:
 *   { fieldName: { label, prompt, hasOverride } }
 *
 * For each listed markdown field it adds a "Generate" button (drafts the field,
 * auto-fills it and saves) and a "Prompt" button (edits the per-object prompt).
 */
$(document).ready(function () {

  var $config = $("#ai-config");
  if (!$config.length || $config.attr("data-enabled") !== "true") {
    return;
  }

  var generateUrl = $config.attr("data-generate-url");
  var promptUrl = $config.attr("data-prompt-url");
  var saveSelector = $config.attr("data-save-selector");

  var aiFields = {};
  try {
    aiFields = JSON.parse($("#ai-fields-data").text() || "{}");
  } catch (e) {
    aiFields = {};
  }
  if (!generateUrl || !Object.keys(aiFields).length) {
    return;
  }

  var notifyOk = typeof success === "function" ? success : function () {};
  var notifyErr = typeof error === "function" ? error : function () {};

  injectStyles();
  Object.keys(aiFields).forEach(function (fieldName) {
    setupField(fieldName, aiFields[fieldName]);
  });

  function setupField(fieldName, meta) {
    var $textarea = $("#id_" + fieldName);
    if (!$textarea.length) {
      return;
    }
    var $cell = $textarea.closest("td");

    var $bar = $('<div class="ai-assist-bar"></div>');
    var $genBtn = $(
      '<button type="button" class="btn btn-sm btn-outline-info ai-generate-btn">' +
        '<i class="fas fa-magic"></i> Generate</button>',
    );
    var $promptBtn = $(
      '<button type="button" class="btn btn-sm btn-outline-secondary ai-prompt-btn">' +
        '<i class="fas fa-sliders-h"></i> Prompt</button>',
    );
    if (meta.hasOverride) {
      $promptBtn.addClass("has-override");
    }
    $bar.append($genBtn).append($promptBtn);

    var $promptBox = $('<div class="ai-prompt-box" style="display:none;"></div>');
    var $hint = $(
      '<small class="ai-prompt-hint">Instruction for the AI when drafting this ' +
        "field. Saved on this item; leave blank to use the library default." +
        "</small>",
    );
    // mde attr stops markdown.js from turning this into a SimpleMDE editor
    var $promptArea = $(
      '<textarea class="form-control ai-prompt-text" rows="3" mde="manual"></textarea>',
    );
    $promptArea.val(meta.prompt || "");
    var $savePrompt = $(
      '<button type="button" class="btn btn-sm btn-secondary ai-prompt-save">Save prompt</button>',
    );
    $promptBox.append($hint).append($promptArea).append($savePrompt);

    var $cm = $cell.find(".CodeMirror").first();
    if ($cm.length) {
      $cm.before($bar);
      $cm.before($promptBox);
    } else {
      $textarea.before($bar);
      $textarea.before($promptBox);
    }

    $promptBtn.on("click", function () {
      $promptBox.toggle();
    });

    $savePrompt.on("click", function () {
      if (!promptUrl) {
        return;
      }
      $savePrompt.prop("disabled", true);
      $.ajax({
        url: promptUrl,
        type: "POST",
        data: { field: fieldName, prompt: $promptArea.val() },
        success: function (data) {
          notifyOk("AI prompt saved");
          if (data && data.hasOverride) {
            $promptBtn.addClass("has-override");
          } else {
            $promptBtn.removeClass("has-override");
          }
          $promptBox.hide();
        },
        error: function (xhr) {
          notifyErr(errorMessage(xhr, "Failed to save prompt"));
        },
        complete: function () {
          $savePrompt.prop("disabled", false);
        },
      });
    });

    $genBtn.on("click", function () {
      var original = $genBtn.html();
      $genBtn
        .prop("disabled", true)
        .html('<i class="fas fa-spinner fa-spin"></i> Generating&hellip;');
      $.ajax({
        url: generateUrl,
        type: "POST",
        data: { field: fieldName },
        success: function (data) {
          setFieldValue($textarea, (data && data.text) || "");
          // honor "auto-fill": persist immediately via the page's Save button
          if (saveSelector && $(saveSelector).length) {
            $(saveSelector).trigger("click");
          }
          notifyOk("Draft generated");
        },
        error: function (xhr) {
          notifyErr(errorMessage(xhr, "Generation failed"));
        },
        complete: function () {
          $genBtn.prop("disabled", false).html(original);
        },
      });
    });
  }

  // Write a value into a markdown field, updating its CodeMirror/SimpleMDE.
  function setFieldValue($textarea, value) {
    var cmEl = $textarea.closest("td").find(".CodeMirror")[0];
    if (cmEl && cmEl.CodeMirror) {
      cmEl.CodeMirror.setValue(value);
      if (typeof cmEl.CodeMirror.save === "function") {
        cmEl.CodeMirror.save();
      }
    }
    $textarea.val(value);
    $textarea.trigger("change");
  }

  function errorMessage(xhr, fallback) {
    try {
      var parsed = JSON.parse(xhr.responseText);
      if (parsed && parsed.error) {
        return parsed.error;
      }
    } catch (e) {
      /* ignore */
    }
    return fallback;
  }

  function injectStyles() {
    if ($("#ai-assist-styles").length) {
      return;
    }
    var css =
      ".ai-assist-bar { display: flex; gap: 6px; margin: 4px 0 6px 0; }" +
      ".ai-assist-bar .btn { line-height: 1.2; }" +
      ".ai-prompt-btn.has-override { border-style: solid; font-weight: 600; }" +
      ".ai-prompt-btn.has-override::after { content: ' \\25CF'; color: var(--cyan, #17a2b8); }" +
      ".ai-prompt-box { margin: 0 0 8px 0; padding: 8px; border: 1px dashed var(--cyan, #17a2b8); border-radius: 4px; }" +
      ".ai-prompt-hint { display: block; margin-bottom: 4px; opacity: 0.8; }" +
      ".ai-prompt-box .ai-prompt-text { margin-bottom: 6px; }";
    $("<style id='ai-assist-styles'></style>").text(css).appendTo("head");
  }
});
