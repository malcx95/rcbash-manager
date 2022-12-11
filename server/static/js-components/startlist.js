$(document).ready(() => {

class StartListInput extends Component {
  constructor() {
    super();

    this.drivers = [];
    //this.drivers = [{number: 90, name: "malcx95"}];

    if (!this.hasAttribute("datalist")) {
      console.error("StartList used without datalist-id");
      return;
    }
    const datalistId = this.getAttribute("datalist");
    let driversDataList = $("#drivers")[0];
    this.allDrivers = this.getDriverDictionaryFromDatalist(driversDataList);
    // copy allDrivers to initialize availableDrivers
    this.availableDrivers = Object.assign({}, this.allDrivers);

    const rootDiv = document.createElement("div");
    rootDiv.classList.add("table-responsive");
    this.shadow.appendChild(rootDiv);

    // Create the table element
    const table = document.createElement("table");
    table.classList.add("table", "table-striped", "table-sm");
    rootDiv.appendChild(table);

    this.constructTableHeader(table);

    this.tableBody = document.createElement("tbody");
    table.appendChild(this.tableBody);

    const inputBox = this.createInputBox(rootDiv, datalistId);
    this.setUpCallbacks(inputBox);

    this.populateTable();
  }

  createInputBox(rootDiv, datalistId) {
    const label = document.createElement("label");
    label.classList.add("form-label");
    label.textContent = "Lägg till förare";
    rootDiv.appendChild(label);

    const input = document.createElement("input");
    input.setAttribute("list", datalistId);
    input.setAttribute("type", "text");
    input.classList.add("form-control");
    rootDiv.appendChild(input);

    return input;
  }

  setUpCallbacks(inputBox) {

    inputBox.onkeypress = (event) => {
      var keycode = (event.keyCode ? event.keyCode : event.which);
      if (keycode == '13') {
        this.addInputToListIfValid(event.target, event.target.value);
      }
    };

  }

  addInputToListIfValid(textbox, number) {
    if (number in this.availableDrivers) {
      this.drivers.push({name: this.availableDrivers[number], number: number});
      textbox.value = "";
      this.populateTable();
    }
  }


  populateTable() {
    this.tableBody.textContent = "";

    // if (this.drivers.length == 0) {
    //   const span = document.createElement("span");
    //   tbody.appendChild(span);
    //   span.textContent = "Lägg till förare";
    // }

    this.drivers.forEach((numberAndName, i) => {
      const tr = document.createElement("tr");
      this.tableBody.appendChild(tr);

      const positionCell = document.createElement("th");
      positionCell.setAttribute("scope", "row");
      positionCell.innerHTML = i + 1;
      tr.appendChild(positionCell);

      const numberCell = document.createElement("td");
      numberCell.innerHTML = numberAndName.number;
      tr.appendChild(numberCell);

      const nameCell = document.createElement("td");
      nameCell.innerHTML = numberAndName.name;
      tr.appendChild(nameCell);
    });
  }

  constructTableHeader(table) {
    var header = document.createElement("thead");
    table.appendChild(header);
    var headerRow = document.createElement("tr");
    header.appendChild(headerRow);

    var headerTitles = ["", "#", "Namn"];
    headerTitles.forEach((title) => {
      let element = document.createElement("th");
      element.setAttribute("scope", "col");
      element.innerHTML = title;
      headerRow.appendChild(element);
    });
  }

  getDriverNumbersFromDatalist(datalist) {
    let options = [];
    for (let prop of datalist.options) {
      options.push(prop.value);
    }
    return options;
  }

  getDriverNamesFromDatalist(datalist) {
    let options = [];
    for (let prop of datalist.options) {
      options.push(prop.getAttribute("name"));
    }
    return options;
  }

  getDriverDictionaryFromDatalist(datalist) {
    let driverNumbers = this.getDriverNumbersFromDatalist(datalist);
    let driverNames = this.getDriverNamesFromDatalist(datalist);

    let result = {};

    for (let i = 0; i < driverNames.length; i++) {
      result[driverNumbers[i]] = driverNames[i];
    }

    return result;
  }
}

customElements.define("start-list-input", StartListInput);

});
