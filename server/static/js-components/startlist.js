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

    const editMode = this.hasAttribute("edit-mode")
      ? this.getAttribute("edit-mode")
      : false;

    const editable = this.hasAttribute("editable")
      ? this.getAttribute("editable")
      : false;

    this.onlyEditable = this.hasAttribute("only-editable")
      ? this.getAttribute("only-editable")
      : false;

    this.rcclassEditable = this.hasAttribute("rcclass-editable")
      ? this.getAttribute("rcclass-editable")
      : false;

    this.rcclassOptions = ["2WD", "4WD"];
    this.groupOptions = ["A", "B"];

    console.log(this.rcclassOptions);

    this.editable = editable || this.onlyEditable;

    this.editMode = editMode || this.onlyEditable;
    this.shouldShowEditButton = this.editable && !this.onlyEditable;

    const rcclass = this.hasAttribute("rcclass")
      ? this.getAttribute("rcclass")
      : "";

    const group = this.hasAttribute("group")
      ? this.getAttribute("group")
      : "";

    this.updateRcclassGroup(rcclass, group);

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

    const rootDiv = createElementWithClass("div", [], this.container);
    this.createCSS(rootDiv);
    this.editButton = undefined;
    const cardBody = this.createCard(rootDiv, this.rcclass, this.group);

    const tableDiv = createElementWithClass("div", ["table-responsive"], cardBody);
    const table = createElementWithClass("table", ["table", "table-striped", "table-sm"], tableDiv);

    this.constructTableHeader(table);

    this.tableBody = createElementWithClass("tbody", [], table);
    this.createInputBox(cardBody, datalistId, driversDataList);

    this.updateState();
  }

  updateOptions() {
    this.options = [];
    this.rcclassOptions.forEach((rcclass) => {
      this.groupOptions.forEach((group) => {
        this.options.push({"rcclass": rcclass, "group": group});
      });
    });
  }

  createCard(rootDiv) {
    const cardDiv = createElementWithClass("div", ["card", "startlistcard"], rootDiv);
    const cardHeaderDiv = createElementWithClass("div", ["card-header", "card-header-div"], cardDiv);
    this.cardHeadingDiv = createElementWithClass("div", ["card-heading-div"], cardHeaderDiv);
    if (this.shouldShowEditButton)
    {
      this.editButton = document.createElement("button");
      cardHeaderDiv.appendChild(this.editButton);
    }
    const cardBody = createElementWithClass("div", ["card-body"], cardDiv);
    return cardBody;
  }

  updateCardHeading() {
    this.cardHeadingDiv.textContent = "";
    if (!this.rcclassEditable) {
      const cardHeading = createElementWithClass("h5", [], this.cardHeadingDiv);
      cardHeading.innerHTML = `
        <strong>${this.rcclass}</strong> Grupp ${this.group}
      `;
    } else {
      const button = createElementWithClass("h5",
        ["editable-heading", "dropdown-toggle"], this.cardHeadingDiv);
      button.setAttribute("data-bs-toggle", "dropdown");
      button.setAttribute("aria-expanded", "false");
      button.id = "dropdown" + this.rcclass + this.group;
      button.innerHTML = `
        <strong>${this.rcclass}</strong> Grupp ${this.group}
        `;
      const dropdownList = createElementWithClass("ul", ["dropdown-menu"], this.cardHeadingDiv);
      dropdownList.setAttribute("aria-labelledby", button.id);
      this.options.forEach((option) => {
        const listItem = createElementWithClass("li", ["dropdown-item", "dropdown-option"], dropdownList);
        listItem.innerHTML = `
          <strong>${option.rcclass}</strong> Grupp ${option.group}
        `;
        listItem.onclick = (event) => {
          this.updateRcclassGroup(option.rcclass, option.group);
          this.updateState();
        };
      });
    }
  }

  updateRcclassGroup(rcclass, group) {
    this.rcclass = rcclass;
    this.group = group;
    this.setAttribute("rcclass", rcclass);
    this.setAttribute("group", group);
  }

  updateEditButton() {
    if (this.shouldShowEditButton) {
      if (this.editMode) {
        this.editButton.className = "";
        this.editButton.classList.add("btn", "btn-success", "btn-sm", "edit-button");
        this.editButton.textContent = "Klar";
      } else {
        this.editButton.className = "";
        this.editButton.classList.add("btn", "btn-outline-dark", "btn-sm", "edit-button");
        this.editButton.textContent = "Redigera";
      }
    }
  }

  updateState() {
    this.populateTable();
    let numbers = this.drivers.map((d) => d.number);
    this.updateOptions();
    this.setAttribute("value", numbers);
    this.updateEditButton();
    this.updateCardHeading();
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
      h5 {
        margin-bottom: 0px;
      }
      .editable-heading {
        cursor: pointer;
      }
      .card-heading-div {
        width: 90%;
      }
      .card-header-div {
        display: flex;
        flex-direction: row;
      }
      .edit-button {
        font-size: 8pt;
      }
      .dropdown-option {
        cursor: pointer;
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

    if (this.shouldShowEditButton)
    {
      this.editButton.onclick = (event) => {
        this.editMode = !this.editMode;
        this.updateState();
      };
    }
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
