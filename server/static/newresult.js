let createStartListInput = (data) => {
  let resultEditContainer = document.getElementById("resultEditContainer");
  let configuration = {
    deletable: false,
    onlyEditable: true,
    rcclassEditable: true,
    result: data
  };
  let startListInput = new StartListInput();
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
