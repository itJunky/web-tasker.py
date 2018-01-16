$(document).ready(function () {
  var COMMENT_LENGTH = 6;

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

    if ($commentText.val().length < COMMENT_LENGTH) {
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