
let areAnyStartListsEmpty = (startLists) => {
  for (const [rcclass, groups] of Object.entries(startLists)) {
    for (const [group, list] of Object.entries(groups)) {
      if (list.length == 0) {
        return true;
      }
    }
  }
  return false;
};

let setInvalidInput = (elementId) => {
  let input = document.getElementById(elementId);
  input.classList.add("is-invalid");
  input.onfocus = (_) => {
    input.classList.remove("is-invalid");
    input.onfocus = undefined;
  };
};

let trySubmitForm = (formData) => {
  let date = formData.date;

  // first, ask if the date exists or will create a new season
  $.ajax({
    type: "GET",
    url: "/api/checkracedaydate",
    data: {date: date},
    dataType: "json",
    success: (data, textStatus, jqXHR) => {
      if (data.dateExists) {
        showError("Det finns redan en tävling med detta datum, välj ett annat.")
        setInvalidInput("dateInput");
        return;
      }
      if (!data.seasonExists) {
        if (!confirm(`Datumet ${date} kommer att skapa en ny säsong, är detta vad du vill?`)) {
          return;
        }
      }

      // now send the actual form
      $.ajax({
        type: "POST",
        url: "/api/newraceday",
        data: JSON.stringify(formData),
        contentType: "application/json",
        dataType: "json",
        success: (data, textStatus, jqXHR) => {
          window.location.href = data.newUrl;
        },
        error: (jqXHR, textStatus, errMsg) => showError(`Ett fel inträffade: ${jqXHR.responseText}`)
      });
    },
    error: (jqXHR, textStatus, errMsg) => showError(`Ett fel inträffade: ${jqXHR.responseText}`)
  });

};

$(document).ready(() => {
  let submitButton = document.getElementById("submitButton");
  submitButton.onclick = (event) => {
    let placeText = document.getElementById("placeInput").value;
    let date = document.getElementById("dateInput").value;
    let startLists = document.getElementById("raceRoundEditor").getValue();

    let formData = {
      location: placeText,
      date: date,
      startLists: startLists
    };

    if (!placeText) {
      setInvalidInput("placeInput");
      showError("Ange plats för deltävlingen");
    } else if (!date) {
      setInvalidInput("dateInput");
      showError("Ange datum för deltävlingen");
    } else if (areAnyStartListsEmpty(startLists)) {
      showError("En eller flera startlistor är tomma, fyll dessa med deltagare eller ta bort dem.")
    } else {
      clearError();
      trySubmitForm(formData);
    }
  };
});
