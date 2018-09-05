$(document).ready(function () {
  var MIN_COMMENT_LENGTH = 6;

  var commentTextSelector = 'form[action="/comment_to_task"] [name="commenttext"]';
  var commentFormSelector = 'form[action="/comment_to_task"]';

  //////
  // add `comment form` validation to length less than 6 letters
  //////
  $('body').on('focus', commentTextSelector, function (e) {
    var $commentText = $(this);
    var $helpBlock = $commentText.parent().find('.help-block');
    $helpBlock.addClass('invisible');
    $commentText.parent().removeClass('has-error');
  });

  $('body').on('submit', commentFormSelector, function(e) {

    var $commentText = $('[name="commenttext"]');
    var $helpBlock = $commentText.parent().find('.help-block');

    if ($commentText.val().length < MIN_COMMENT_LENGTH) {
      e.preventDefault();
      $commentText.parent().addClass('has-error');
      $helpBlock.removeClass('invisible');
      return false;
    }
  });

  //////
  //  add user to project checkbox handler
  //  fix issue #4
  //////
  $('body').on('click', '#adduser', function (e) {
    if ($(this).prop('checked')) {
      $("#dinamic-form").css('display', 'block');
    } else {
      $("#dinamic-form").css('display', 'none');
    }
  });

  ////
  // Task list (BootstrapTable)
  ////
  var $taskList = $('#task-list');
  if ($taskList.length) {

    $taskList.bootstrapTable({
      customSort: function (sortName, sortOrder) {
        if (sortName === 'timestamp') {
          if (sortOrder === 'asc') {
            depthFirstTreeSort(this.data, parentTimestampCmpAsc);
          } else if (sortOrder === 'desc') {
            depthFirstTreeSort(this.data, parentTimestampCmpDesc);
          } else { }
        } else { }
      },
      onPostBody: function(e) {
        $taskList.removeClass('invisible faded');
      }
    });
  }

  ////
  // Task
  ////

  ////
  //  Feature: comment editing.
  ////

  var $commentsSection = $('.comments-section');
  var commentSelector = '.tasklist.table';
  var editingComment = null;

  if ($commentsSection.length) {
    // Sets event handlers if there are comments.
    $commentsSection.click(commentsSectionClickHandler);
    $commentsSection.dblclick(commentsSectionDblClickHandler);
  }

  function commentsSectionDblClickHandler(e){
    // Event handler function to doubleclick event on comment text field.
    e.preventDefault();
    var target = e.target;
    var comment = $(target).parents(commentSelector);
    var td = $(comment).find('.td-content');

    if (target.tagName === 'PRE') {
      if (editingComment) return;
      startCommentEdit(td);
      return;
    }
  }

  function commentsSectionClickHandler(e) {
    // Handle single click to edit button,
    // control buttons(save, cancel) in editing mode.
    var target = e.target;
    var comment = $(target).parents(commentSelector);
    var td = $(comment).find('.td-content');
    var data = $(comment).data('data');

    if (!target.classList.contains('js-delete-comment-button')) {
      e.preventDefault();
    }

    if (target.classList.contains('edit-cancel')) {
      stopCommentEdit(editingComment.elem, false);
      return;
    }

    if (target.classList.contains('edit-ok')) {
      stopCommentEdit(editingComment.elem, true, data);
      return;
    }

    if (target.classList.contains('js-edit-comment-button')) {
      if (editingComment) return;
      startCommentEdit(td);
      return
    }

  }

  function startCommentEdit(td){
    // Generate textarea field and controls to editing mode.
    // Stores data to previous state in `editingComment` object.

    editingComment = {
      elem: td,
      data: td.html()
    };

    var ta = $('<textarea>');
    var helpBlock = $('<span>');
    var controls = $('<div>');
    var okButton = $('<button>');
    var cancelButton = $('<button>');
    var pre = td.find('pre');

    ta
      .outerWidth(pre.outerWidth())
      .outerHeight(pre.outerHeight())
      .addClass('edit-area')
      .addClass('form-control')
      .val(td.text());

    helpBlock
      .text('Здесь может быть твоё информационное сообщение.')
      .addClass('help-block')
      .addClass('invisible');

    controls
      .addClass('edit-controls');


    okButton
      .addClass('edit-ok')
      .addClass('btn btn-primary btn-sm')
      .text('SAVE');

    cancelButton
      .addClass('edit-cancel')
      .addClass('btn btn-default btn-sm')
      .text('CANCEL');

    controls
      .append(okButton)
      .append(cancelButton);

    td
      .html('')
      .append(ta)
      .append(helpBlock)
      .append(controls);

    ta.trigger('focus');

    ta.on('focus', function (e) {
      var $ta = $(this);
      var $helpBlock = $ta.parent().find('.help-block');
      $helpBlock.addClass('invisible');
      $ta.parent().removeClass('has-error');
    });
  }

  function stopCommentEdit(td, isOkButtonPressed, data){
    if (isOkButtonPressed) {
      var ta = td.find('.edit-area');
      var text = ta.val();
      var oldtext = $(editingComment.data).text();


      // Check whether text has been modified.
      // If it was, than check does comment length longer than
      // min lenght, if it greater then send data.
      // In case text did't modify just close edit dialog, nothing send.
      // In case text less than min length, show info message
      // below edit area.
      data = {
        commentid: data.commentid,
        taskid: data.taskid,
        commenttext: text,
        oldcommenttext: oldtext
      };

      if(isCommentModified(text, oldtext)) {

        if (isCommentLengthEnough(text.length, MIN_COMMENT_LENGTH)) {
          // !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
          // There you could specify endpoint you want, http verb and etc.
          // Data stores in object named `data` which looks like below:
          // data = {
          //   commentid: 'number: comment id',
          //   taskid: 'number: task id',
          //   commenttext: 'string: new comment text',
          //   oldcommenttext: 'string: old comment text'
          // };
          // *** All you need is just specify endpoint and HTTP METHOD ***
          // !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

          $.ajax('/edit_comment_to_task', {
            method: 'POST',
            data: data
          });

          td
            .html(editingComment.data)
            .find('pre')
            .text(text);
        } else {

          var $helpBlock = td.find('.help-block');
          $helpBlock
            .removeClass('invisible')
            .text("Длина комментария должна быть больше "+MIN_COMMENT_LENGTH+" символов.");
          td.addClass('has-error');

          return;
        }

      } else {
        td.html(editingComment.data);
      }

    } else {
      if (td.hasClass('has-error')) td.removeClass('has-error');
      td.html(editingComment.data);
    }

    editingComment = null;
  }


  function isCommentModified(oldComment, newComment){
    return oldComment !== newComment;
  }


  function isCommentLengthEnough(lenght, minLenght) {
    minLenght = minLenght || MIN_COMMENT_LENGTH;
    return lenght >= minLenght;
  }




  ////
  // Helpers
  ////

  ////
  // Tree structure sorting
  // Solution:
  // https://codereview.stackexchange.com/questions/119574/sort-array-of-objects-with-hierarchy-by-hierarchy-and-name
  ////
  function depthFirstTreeSort(arr, cmp) {

    // Returns an object, where each key is a node number, and its value
    // is an array of child nodes.
    function makeTree(arr) {
        var tree = {};
        for (var i = 0; i < arr.length; i++) {
            if (!isIdExist(arr, arr[i].parent_id)) { continue };
            if (!tree[arr[i].parent_id]) tree[arr[i].parent_id] = [];
            tree[arr[i].parent_id].push(arr[i]);
        }
        return tree;
    }

    // For each node in the tree, starting at the given id and proceeding
    // depth-first (pre-order), sort the child nodes based on cmp, and
    // call the callback with each child node.
    function depthFirstTraversal(tree, id, cmp, callback) {
        var children = tree[id];
        if (children) {
            children.sort(cmp);
            for (var i = 0; i < children.length; i++) {
                callback(children[i]);
                depthFirstTraversal(tree, children[i].id, cmp, callback);
            }
        }
    }

    // Overwrite arr with the reordered result
    var counter = 0;
    var tree = makeTree(arr);
    depthFirstTraversal(tree, 0, cmp, function(node) {
        arr[counter++] = node;
    });
    if (arr.length > counter) { arr.length = counter; }
  }

  function parentIdCmpAsc(a, b) { return a.id - b.id; }
  function parentIdCmpDesc(a, b) { return b.id - a.id; }
  function parentTimestampCmpAsc(a, b) { return a.timestamp_seconds - b.timestamp_seconds; }
  function parentTimestampCmpDesc(a, b) { return b.timestamp_seconds - a.timestamp_seconds; }

  function isIdExist(arr, parent_id) {
    return !!~Array.prototype.findIndex.call(arr, function (el) {
      return el.id === parent_id || parent_id === String(0);
    });
  }

});