function validatePasswords(form) {
  var pw1 = form.find('input[name="password1"]').val();
  var pw2 = form.find('input[name="password2"]').val();
  if (pw1 || pw2) {
    if (pw1 !== pw2) {
      error('Passwords do not match.');
      return false;
    }
  }
  return true;
}

$(document).ready(function() {
  $('#userSave').off().click(function() {
    $('#userForm').submit();
  });

  $('#accountSave').off().click(function() {
    $('#accountForm').submit();
  });

  $('#userForm, #accountForm').on('submit', function(e) {
    if (!validatePasswords($(this))) {
      e.preventDefault();
    }
  });
});
