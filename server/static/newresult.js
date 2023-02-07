let createDriversList = (data, allDriversDictionary) => {
  return data.positions.map(d => ({"name": allDriversDictionary[d], "number": d}));
};

let createStartListInput = (data) => {
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
  resultEditContainer.appendChild(startListInput);

  let resultTable = new ResultTable(data.fullResult, allDriversDictionary);
  resultTableContainer.appendChild(resultTable);

  // HACK: you need to do this for the edit buttons to be displayed
  feather.replace();
};

let addResultManually = () => {
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
  resultEditContainer.appendChild(startListInput);
};

let onSuccessfulParse = (data, textStatus, jqXHR) => {
  if (data.warningMsg) {
    showWarning(data.warningMsg);
  }
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
});
