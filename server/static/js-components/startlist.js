class StartListInput extends Component {
  constructor(rcclass, group, datalistId, configuration) {
    super();

    /*
     * The list of driver numbers and names which are currently inputed
     * to this input. Each driver is represented by an object: {name: str, number: int}
     */
    this.drivers = configuration.drivers || [];
    this.datalistId = datalistId;

    this.onDriverAdded = (driverNumberAndName) => { };
    this.onDriverRemoved = (driverNumberAndName) => { };
    this.onDeleteClicked = (startListInput) => { };

    if (configuration === undefined) {
      configuration = {};
    }
    const editMode = this.hasAttribute("edit-mode")
      ? this.getAttribute("edit-mode")
      : configuration.editMode || false;

    const editable = this.hasAttribute("editable")
      ? this.getAttribute("editable")
      : configuration.editable || false;

    this.deletable = this.hasAttribute("deletable")
      ? this.getAttribute("deletable")
      : configuration.deletable || false;

    this.resultMode = this.hasAttribute("result-mode")
      ? this.getAttribute("result-mode")
      : configuration.resultMode || false;

    this.onlyEditable = this.hasAttribute("only-editable")
      ? this.getAttribute("only-editable")
      : configuration.onlyEditable || false;

    this.rcclassEditable = this.hasAttribute("rcclass-editable")
      ? this.getAttribute("rcclass-editable")
      : configuration.rcclassEditable || false;

    this.options = this.hasAttribute("options")
      ? this.getAttribute("options")
      : configuration.options || {rcclass: rcclass, group: group};

    rcclass = this.hasAttribute("rcclass")
      ? this.getAttribute("rcclass")
      : rcclass;

    group = this.hasAttribute("group")
      ? this.getAttribute("group")
      : group;

    this.editable = editable || this.onlyEditable;

    this.editMode = editMode || this.onlyEditable;
    this.shouldShowEditButton = this.editable && !this.onlyEditable;

    this.updateRcclassGroup(rcclass, group);

    // copy the list of available drivers
    this.availableDrivers = {}
    this.updateAvailableDrivers();

    this.container.classList.add("start-list-input");
    const rootDiv = createElementWithClass("div", [], this.container);
    this.createCSS(rootDiv);
    this.editButton = undefined;
    const cardBody = this.createCard(rootDiv, this.rcclass, this.group);

    const tableDiv = createElementWithClass("div", ["table-responsive", "start-list-table"], cardBody);
    let tableClassList = this.resultMode
      ? ["table", "table-sm"]
      : ["table", "table-striped", "table-sm"];

    const table = createElementWithClass("table", tableClassList, tableDiv);

    this.constructTableHeader(table);

    this.tableBody = createElementWithClass("tbody", [], table);
    this.createInputBox(cardBody, datalistId);

    this.updateState();
  }

  setOnlyEditable(val) {
    this.onlyEditable = val;
    this.editMode = this.editMode || val;
  }

  updateAvailableDrivers() {
    let datalist = document.getElementById(this.datalistId);
    this.availableDrivers = getDriverDictionaryFromDatalist(datalist);
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
      .edit-driver-button {
        color: #5F5F5F;
        padding: 0px;
      }
      .start-list-input {
        margin-top: 0px;
      }

      .winner {
        font-weight: bold;
        color: #ac940f;
      }
      .second {
        font-weight: bold;
        color: gray;
      }
      .third {
        font-weight: bold;
        color: #d28800;
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
    let rowClasses = ["winner", "second", "third"];

    this.drivers.forEach((numberAndName, i) => {
      let rowClassList = this.resultMode && i <= 2
        ? [rowClasses[i]]
        : [];
      const tr = createElementWithClass("tr", rowClassList, this.tableBody);

      const positionCell = createElementWithClass("td", [], tr);
      positionCell.setAttribute("scope", "row");
      positionCell.innerHTML = `<strong>${i + 1}</strong>`;

      const numberCell = createElementWithClass("td", [], tr);
      numberCell.innerHTML = numberAndName.number;

      const nameCell = createElementWithClass("td", [], tr);
      nameCell.innerHTML = numberAndName.name;

      const upCell = createElementWithClass("td", [], tr);
      const downCell = createElementWithClass("td", [], tr);
      const deleteCell = createElementWithClass("td", [], tr);
      if (this.editMode) {

        const upButton = createElementWithClass(
          "button", ["btn", "btn-link", "btn-sm", "edit-driver-button"], upCell);
        upButton.innerHTML = `
          <span data-feather="chevron-up" class="align-text-bottom"></span>
        `;
        upButton.onclick = (event) => {
          // swap this driver with the driver directly above
          [this.drivers[i - 1], this.drivers[i]] = [this.drivers[i], this.drivers[i - 1]];
          this.updateState();
        };
        if (i === 0) {
          // disable the button if we are at the top already
          upButton.setAttribute("disabled", true);
        }

        const downButton = createElementWithClass(
          "button", ["btn", "btn-link", "btn-sm", "edit-driver-button"], downCell);
        downButton.innerHTML = `
          <span data-feather="chevron-down" class="align-text-bottom"></span>
        `;
        downButton.onclick = (event) => {
          // swap this driver with the driver directly below
          [this.drivers[i + 1], this.drivers[i]] = [this.drivers[i], this.drivers[i + 1]];
          this.updateState();
        };
        if (i === this.drivers.length - 1) {
          // disable the button if we are at the bottom already
          downButton.setAttribute("disabled", true);
        }

        const deleteButton = createElementWithClass(
          "button", ["btn", "btn-link", "btn-sm", "edit-driver-button"], deleteCell);
        deleteButton.innerHTML = `
          <span data-feather="x" class="align-text-bottom"></span>
        `;
        deleteButton.onclick = (event) => {
          let newDrivers = this.drivers.filter((d, index) => index !== i);
          this.drivers = newDrivers;
          this.updateState();
          this.onDriverRemoved(numberAndName);
        };
      }

    });
  }

  constructTableHeader(table) {
    let header = createElementWithClass("thead", [], table);
    let headerRow = createElementWithClass("tr", [], header);

    var headerTitles = [
      "",  // index
      "#",  // number
      "Namn",  // name
      "",  // up
      "",  // down
      ""  // delete
    ];
    headerTitles.forEach((title) => {
      let element = createElementWithClass("th", [], headerRow);
      element.setAttribute("scope", "col");
      element.innerHTML = title;
    });
  }
}

customElements.define("start-list-input", StartListInput);

