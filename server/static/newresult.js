const RESULT_STARTLIST_ID = "resultStartlistInput";
const RESULT_TABLE_ID = "resultTable";

// TODO this is probably pretty ugly
let totalTimes = null;
let numLapsDriven = null;
let bestLaptimes = null;
let averageLaptimes = null;


let createDriversList = (data, allDriversDictionary) => {
  return data.positions.map(d => ({"name": allDriversDictionary[d], "number": d}));
};

let revealSubmitButton = () => {
  let manualButton = document.getElementById("enterResultManuallyButton");
  let submitButton = document.getElementById("submitButton");
  manualButton.style.display = "none";
  submitButton.style.display = "block";
};

let createStartListInput = (data) => {
  clearAlerts();
  revealSubmitButton();
  let resultEditContainer = document.getElementById("resultEditContainer");
  let resultTableContainer = document.getElementById("resultTableContainer");

  resultEditContainer.textContent = "";
  resultTableContainer.textContent = "";

  let datalist = document.getElementById("drivers");
  let allDriversDictionary = getDriverDictionaryFromDatalist(datalist);

  let configuration = {
    deletable: false,
    onlyEditable: true,
    resultMode: true,
    rcclassEditable: false,
    drivers: createDriversList(data, allDriversDictionary)
  };
  let startListInput = new StartListInput(data.rcclass, data.group, "drivers", configuration);
  startListInput.id = RESULT_STARTLIST_ID;
  resultEditContainer.appendChild(startListInput);

  let resultTable = new ResultTable(data.fullResult, allDriversDictionary);
  resultTable.id = RESULT_TABLE_ID;
  resultTableContainer.appendChild(resultTable);

  // HACK: you need to do this for the edit buttons to be displayed
  feather.replace();
};

let addResultManually = () => {
  clearAlerts();
  revealSubmitButton();

  let resultEditContainer = document.getElementById("resultEditContainer");
  let resultTableContainer = document.getElementById("resultTableContainer");

  resultEditContainer.textContent = "";
  resultTableContainer.textContent = "";

  let datalist = document.getElementById("drivers");
  let allDriversDictionary = getDriverDictionaryFromDatalist(datalist);

  let configuration = {
    deletable: false,
    onlyEditable: true,
    resultMode: true,
    rcclassEditable: true,
    options: [
      {rcclass: "2WD", group: "A"},
      {rcclass: "2WD", group: "B"},
      {rcclass: "2WD", group: "C"},
      {rcclass: "4WD", group: "A"},
      {rcclass: "4WD", group: "B"},
      {rcclass: "4WD", group: "C"}
    ]
  };

  let startListInput = new StartListInput("2WD", "A", "drivers", configuration);
  startListInput.id = RESULT_STARTLIST_ID;
  resultEditContainer.appendChild(startListInput);
};

let submitResult = () => {
  clearAlerts();
  let startListInput = document.getElementById(RESULT_STARTLIST_ID);
  let resultTable = document.getElementById(RESULT_TABLE_ID);
  let drivers = startListInput.drivers;
  let fullResult = resultTable !== undefined ? resultTable.result : {};

  let result = {
    positions: drivers,
    totalTimes: totalTimes,
    numLapsDriven: numLapsDriven,
    bestLaptimes: bestLaptimes,
    averageLaptimes: averageLaptimes,
    fullResult: fullResult,
    manual: false,
  };
  $.ajax({
    type: "POST",
    url: `/api/submitResult/${CURRENT_DATE}`,
    data: result,
    processData: false,
    contentType: false,
    dataType: "json",
    success: (data, textStatus, jqXHR) => {
      showSuccess("Resultatet sparades.")
    },
    error: (jqXHR, textStatus, errMsg) => showError(`Ett fel inträffade: ${jqXHR.responseText}`)
  });
}

let onSuccessfulParse = (data, textStatus, jqXHR) => {
  if (data.warningMsg) {
    showWarning(data.warningMsg);
  }
  totalTimes = data.totalTimes;
  numLapsDriven = data.numLapsDriven;
  bestLaptimes = data.bestLaptimes;
  averageLaptimes = data.averageLaptimes;

  createStartListInput(data);
};

$(document).ready(() => {
  let fileUploadButton = document.getElementById("fileUpload");
  fileUploadButton.oninput = (event) => {
    let formData = new FormData();
    formData.append("file", event.target.files[0]);
    $.ajax({
      type: "POST",
      url: `/api/parseresult/${CURRENT_DATE}`,
      data: formData,
      processData: false,
      contentType: false,
      dataType: "json",
      success: onSuccessfulParse,
      error: (jqXHR, textStatus, errMsg) => showError(`Ett fel inträffade: ${jqXHR.responseText}`)
    });
  };
  let manualButton = document.getElementById("enterResultManuallyButton");
  manualButton.onclick = (event) => addResultManually();
  let submitButton = document.getElementById("submitButton");
  submitButton.onclick = (event) => submitResult();
});
