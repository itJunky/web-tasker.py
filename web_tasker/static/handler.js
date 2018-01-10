window.onload = function () {
  document.getElementById('adduser').onclick = function ()
  {
    if(this.checked)
      document.getElementById("dinamic-form").style.display="block";
    else
      document.getElementById("dinamic-form").style.display="none";
  }
}

//////
// add `comment form` validation to length less than 6 letters
//////
$(document).ready(function () {
  const COMMENT_LENGTH = 6;

  let commentTextSelector = 'form[action="/comment_to_task"] [name="commenttext"]';
  let commentFormSelector = 'form[action="/comment_to_task"]';

  $('body').on('focus', commentTextSelector, function (e) {
    let $commentText = $(this);
    let $helpBlock = $commentText.parent().find('.help-block');
    $helpBlock.addClass('invisible');
    $commentText.parent().removeClass('has-error');
  });

  $('body').on('submit', commentFormSelector, function(e) {

    let $commentText = $('[name="commenttext"]');
    let $helpBlock = $commentText.parent().find('.help-block');

    if ($commentText.val().length < COMMENT_LENGTH) {
      e.preventDefault();
      $commentText.parent().addClass('has-error');
      $helpBlock.removeClass('invisible');
      return false;
    }
  });

});