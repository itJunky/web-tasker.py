window.onload = function () {
  document.getElementById('adduser').onclick = function ()
  {
    if(this.checked)
      document.getElementById("dinamic-form").style.display="block";
    else
      document.getElementById("dinamic-form").style.display="none";
  }
}