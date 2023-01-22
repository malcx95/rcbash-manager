let createDriversList = (data) => {
  let allDriversDictionary = getDriverDictionaryFromDatalist("drivers");
  return data.positions.map(d => {name: allDriversDictionary[d], number: d});
}

let createStartListInput = (data) => {
  let resultEditContainer = document.getElementById("resultEditContainer");
  let configuration = {
    deletable: false,
    onlyEditable: true,
    rcclassEditable: true,
    drivers: createDriversList(data)
  };
  
};

let onSuccessfulParse = (data, textStatus, jqXHR) => {
  createStartListInput(data);
};

$(document).ready(() => {
  let fileUploadButton = document.getElementById("fileUpload");
  fileUploadButton.oninput = (event) => {
    let formData = new FormData();
    formData.append("file", event.target.files[0]);
    $.ajax({
      type: "POST",
      url: "/api/parseresult",
      data: formData,
      processData: false,
      contentType: false,
      dataType: "json",
      success: onSuccessfulParse,
      error: (jqXHR, textStatus, errMsg) => showError(`Ett fel inträffade: ${jqXHR.responseText}`)
    });
  };
});
