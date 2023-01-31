/* globals Chart:false, feather:false */
$(document).ready(() => {
  feather.replace({ 'aria-hidden': 'true' });
});

let _showAlert = (msg, alertId) => {
  let alert = document.getElementById(alertId);
  alert.style.display = "block";
  alert.textContent = msg;
};

let clearAlerts = () => {
  document.getElementById("errorAlert").style.display = "none";
  document.getElementById("warningAlert").style.display = "none";
  document.getElementById("successAlert").style.display = "none";
  document.getElementById("primaryAlert").style.display = "none";
};

let showError = (msg) => _showAlert(msg, "errorAlert");
let showWarning = (msg) => _showAlert(msg, "warningAlert");
let showSuccess = (msg) => _showAlert(msg, "successAlert");
let showPrimary = (msg) => _showAlert(msg, "primaryAlert");
