function CopyClipboard(element) {
  var $temp = $("<input>");
  $("body").append($temp);
  $temp.val($(element).text()).select();
  document.execCommand("copy");
  alert("Link copied. Now share it to your friends")
  $temp.remove();
}


// document.addEventListener('DOMContentLoaded', function() {
//   var elems = document.querySelectorAll('.sidenav');
//   var instances = M.Sidenav.init(elems, options);
// });

  $(document).ready(function() {
    $('textarea#textarea2').characterCounter();
    $('.sidenav').sidenav();
    // $('.materialboxed').materialbox();
    $('.tabs').tabs();
    $('select').formSelect();
    $('.collapsible').collapsible();
    $('.modal').modal();
  });

