/* globals Chart:false, feather:false */
$(document).ready(() => {
  feather.replace({ 'aria-hidden': 'true' });
});

let clearError = () => {
  document.getElementById("errorAlert").style.display = "none";
};

let showError = (errorMsg) => {
  let errorAlert = document.getElementById("errorAlert");
  errorAlert.style.display = "block";
  errorAlert.textContent = errorMsg;
};
