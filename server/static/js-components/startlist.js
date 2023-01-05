class StartListInput extends Component {
  constructor(rcclass, group, datalistId) {
    super();

    /*
     * The list of driver numbers and names which are currently inputed
     * to this input. Each driver is represented by an object: {name: str, number: int}
     */
    this.drivers = [];
    this.datalistId = datalistId;

    this.onDriverAdded = (driverNumberAndName) => { };
    this.onDriverRemoved = (driverNumberAndName) => { };
    this.onDeleteClicked = (startListInput) => { };

    const editMode = this.hasAttribute("edit-mode")
      ? this.getAttribute("edit-mode")
      : false;

    const editable = this.hasAttribute("editable")
      ? this.getAttribute("editable")
      : false;

    this.deletable = this.hasAttribute("deletable")
      ? this.getAttribute("deletable")
      : false;

    this.onlyEditable = this.hasAttribute("only-editable")
      ? this.getAttribute("only-editable")
      : false;

    this.rcclassEditable = this.hasAttribute("rcclass-editable")
      ? this.getAttribute("rcclass-editable")
      : false;

    this.rcclassOptions = ["2WD", "4WD"];
    this.groupOptions = ["A", "B"];

    this.editable = editable || this.onlyEditable;

    this.editMode = editMode || this.onlyEditable;
    this.shouldShowEditButton = this.editable && !this.onlyEditable;

    rcclass = this.hasAttribute("rcclass")
      ? this.getAttribute("rcclass")
      : rcclass;

    group = this.hasAttribute("group")
      ? this.getAttribute("group")
      : group;

    this.updateRcclassGroup(rcclass, group);

    // copy the list of available drivers
    this.availableDrivers = {}
    this.updateAvailableDrivers();
    /*
     * TODO kanske gör en egen datalist som kan hålla koll på availableDrivers?
     * Så flera startlists kan ta del av dem och synka med varandra?
     */

    const rootDiv = createElementWithClass("div", [], this.container);
    this.createCSS(rootDiv);
    this.editButton = undefined;
    const cardBody = this.createCard(rootDiv, this.rcclass, this.group);

    const tableDiv = createElementWithClass("div", ["table-responsive", "start-list-table"], cardBody);
    const table = createElementWithClass("table", ["table", "table-striped", "table-sm"], tableDiv);

    this.constructTableHeader(table);

    this.tableBody = createElementWithClass("tbody", [], table);
    this.createInputBox(cardBody, datalistId);

    this.updateState();
  }

  updateAvailableDrivers() {
    let datalist = document.getElementById(this.datalistId);
    this.availableDrivers = this.getDriverDictionaryFromDatalist(datalist);
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

    this.deleteButton = createElementWithClass(
      "button", ["btn", "btn-link", "btn-sm", "delete-list-button"], cardHeaderDiv);
    this.deleteButton.innerHTML = `
      <span data-feather="trash-2" class="align-text-bottom"></span>
    `;
    this.deleteButton.onclick = (event) => { this.onDeleteClicked(this) };

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

    this.deleteButton.style.display = this.deletable ? "block" : "none";

    // update the feather icons since they don't automatically
    // respond to the display property
    feather.replace();
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

  createInputBox(rootDiv, datalistId) {
    const hr = createElementWithClass("hr", [], rootDiv);
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

    this.setUpCallbacks(input, addButton);
  }

  createCSS(rootDiv) {
    const style = document.createElement("style");
    style.textContent = `
      .add-button {
        width: 170px;
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
      .delete-list-button {
        color: #5F5F5F;
        padding: 0px;
        margin-left: 20px;
      }
    `;
    rootDiv.appendChild(style);
  }

  setUpCallbacks(inputBox, addButton) {

    let onDriverSubmit = () => {
      let driverNumberAndName = this.addInputToListIfValid(
        inputBox, parseInt(inputBox.value), addButton);
      if (driverNumberAndName) {
        this.onDriverAdded(driverNumberAndName);
      }
    };

    inputBox.onkeypress = (event) => {
      var keycode = (event.keyCode ? event.keyCode : event.which);
      if (keycode === 13) {
        onDriverSubmit();
      }
    };

    addButton.onclick = (event) => {
      onDriverSubmit();
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
      var driverNumberAndName = {name: this.availableDrivers[number], number: number}
      this.drivers.push(driverNumberAndName);
      textbox.value = "";
      addButton.disabled = true;
      this.updateState();
      return driverNumberAndName;
    }
    return null;
  }

  populateTable() {
    this.tableBody.textContent = "";

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
}

customElements.define("start-list-input", StartListInput);

