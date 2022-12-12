$(document).ready(() => {

  /*
   * TODO lägg till ett normal- och edit-läge.
   * I normal-läget ska textrutan och alla redigeringskontroller vara
   * borta/dolda, och en edit-knapp ska finnas. Klickar man på edit-knappen
   * går man in i edit-läget. På så sätt kan denna användas på alla ställen
   * där startlistor används. Naturligtvis ska editläget bara vara tillgängligt
   * för administratörer.
   */

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
    let driversDataList = document.getElementById(datalistId);
    this.allDrivers = this.getDriverDictionaryFromDatalist(driversDataList);
    // copy allDrivers to initialize availableDrivers
    this.availableDrivers = Object.assign({}, this.allDrivers);
    /*
     * TODO kanske gör en egen datalist som kan hålla koll på availableDrivers?
     * Så flera startlists kan ta del av dem och synka med varandra?
     */

    const rootDiv = document.createElement("div");
    this.shadow.appendChild(rootDiv);

    this.createCSS(rootDiv);

    // Create the table element
    const tableDiv = document.createElement("div");
    tableDiv.classList.add("table-responsive");
    rootDiv.appendChild(tableDiv);

    const table = document.createElement("table");
    table.classList.add("table", "table-striped", "table-sm");
    tableDiv.appendChild(table);

    this.constructTableHeader(table);

    this.tableBody = document.createElement("tbody");
    table.appendChild(this.tableBody);

    this.createInputBox(rootDiv, datalistId, driversDataList);

    this.updateState();
  }

  updateState() {
    this.populateTable();
    let numbers = this.drivers.map((d) => d.number);
    console.log(numbers);
    this.setAttribute("value", numbers);
  }

  createInputBox(rootDiv, datalistId, datalist) {
    const label = document.createElement("label");
    label.classList.add("form-label");
    label.textContent = "Lägg till förare";
    rootDiv.appendChild(label);

    const inputDiv = document.createElement("div");
    inputDiv.classList.add("input-div");
    rootDiv.appendChild(inputDiv);

    const input = document.createElement("input");
    input.setAttribute("list", datalistId);
    input.setAttribute("type", "text");
    input.classList.add("form-control");
    inputDiv.appendChild(input);

    const addButton = document.createElement("button");
    addButton.classList.add("btn", "btn-primary", "add-button");
    addButton.textContent = "Lägg till";
    addButton.disabled = true;
    inputDiv.appendChild(addButton);

    // add the datalist here again since it's not visible in the shadow DOM
    rootDiv.appendChild(datalist);

    this.setUpCallbacks(input, addButton);
  }

  createCSS(rootDiv) {
    const style = document.createElement("style");
    style.textContent = `
      .add-button {
        width: 30%;
        margin-left: 5px;
      }
      .input-div {
        display: flex;
      }
    `;
    rootDiv.appendChild(style);
  }

  setUpCallbacks(inputBox, addButton) {

    inputBox.onkeypress = (event) => {
      var keycode = (event.keyCode ? event.keyCode : event.which);
      if (keycode == '13') {
        this.addInputToListIfValid(event.target, event.target.value, addButton);
      }
    };

    addButton.onclick = (event) => {
      this.addInputToListIfValid(inputBox, inputBox.value, addButton);
    };

    inputBox.oninput = (event) => {
      addButton.disabled = !(inputBox.value in this.availableDrivers);
    };
  }

  addInputToListIfValid(textbox, number, addButton) {
    if (number in this.availableDrivers) {
      this.drivers.push({name: this.availableDrivers[number], number: number});
      textbox.value = "";
      addButton.disabled = true;
      this.updateState();
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
