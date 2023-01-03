const AVAILABLE_DRIVERS_ID = "availableDriversDatalist";
const GROUPS = ["A", "B", "C", "D"];

class RaceRoundEditor extends Component {
  constructor() {
    super();

    if (!this.hasAttribute("datalist")) {
      console.error("RaceRoundEditor used without datalist-id");
      return;
    }

    let datalistId = this.getAttribute("datalist");

    let allDriversDataList = document.getElementById(datalistId);
    this.allDrivers = this.getDriverDictionaryFromDatalist(allDriversDataList);

    if (!this.hasAttribute("add-dropdown-id")) {
      console.error("RaceRoundEditor used without add-dropdown-id");
      return;
    }

    let addGroupDropdownId = this.getAttribute("add-dropdown-id");
    this.addGroupDropdown = document.getElementById(addGroupDropdownId);

    this.rcclassGroups = [
      {rcclass: "4WD", group: "A"},
      {rcclass: "2WD", group: "A"}
    ];

    this.content = createElementWithClass("div", ["row", "row-cols-1", "row-cols-md-2", "row-cols-lg-3", "g-3", "race-round-editor-content"], this.container);

    this.highestAvailableGroupIndices = {"4WD": 0, "2WD": 0};
    this.availableDriversDatalist = createElementWithClass("datalist", [], this.container);
    this.availableDriversDatalist.id = AVAILABLE_DRIVERS_ID;
    this.startListInputs = [];
    this.updateAvailableDrivers();

    this.rcclassGroups.forEach((rcclassGroup) => {
      this.createStartListInput(rcclassGroup.rcclass, rcclassGroup.group);
    });

    this.updateStartListInputs();
    this.updateDropdownOptions();

    this.createCSS(this.container);
  }

  updateStartListInputs() {
    this.startListInputs.sort((a, b) => {
      if (a.rcclass != b.rcclass) {
        return a.rcclass > b.rcclass;
      }
      return a.group > b.group;
    });
    this.content.textContent = "";
    this.startListInputs.forEach((startListInput) => {
      this.content.appendChild(startListInput);
    });
  }

  createStartListInput(rcclass, group) {
    const startListInput = new StartListInput(rcclass, group, AVAILABLE_DRIVERS_ID);
    startListInput.rcclassEditable = true;
    startListInput.onlyEditable = true;
    startListInput.onDriverAdded = (d) => this.onDriverAdded(d);
    startListInput.updateState();
    this.startListInputs.push(startListInput);
  }

  updateDropdownOptions() {
    this.addGroupDropdown.textContent = "";
    let groups = this.getAvailableGroupsToAdd();
    for (const [rcclass, group] of Object.entries(groups)) {
      let listItem = createElementWithClass("li", [], this.addGroupDropdown);
      let link = createElementWithClass("a", ["dropdown-item", "pointer"], listItem);
      link.onclick = (event) => {
        this.highestAvailableGroupIndices[rcclass] += 1;
        this.createStartListInput(rcclass, group);
        this.updateStartListInputs();
        this.updateDropdownOptions();
      };
      link.innerHTML = `
        <strong>${rcclass}</strong> grupp ${group}
      `;
    }
  }

  getAvailableGroupsToAdd() {
    let groups = {};
    ["2WD", "4WD"].forEach((rcclass) => {
      let group = GROUPS[this.highestAvailableGroupIndices[rcclass] + 1];
      groups[rcclass] = group;
    });
    return groups;
  }

  updateAvailableDrivers() {
    this.availableDriversDatalist.textContent = "";
    let takenNumbers = new Set();
    this.startListInputs.forEach((startListInput) => {
      startListInput.drivers.forEach((driverNumberAndName) => {
        takenNumbers.add(driverNumberAndName.number);
      });
    });
    let availableDrivers = {};
    for (let driverNumber in this.allDrivers) {
      if (!takenNumbers.has(parseInt(driverNumber))) {
        availableDrivers[driverNumber] = this.allDrivers[driverNumber];
      }
    }
    for (const driverNumber in availableDrivers) {
      let name = availableDrivers[driverNumber];
      let option = createElementWithClass("option", [], this.availableDriversDatalist);
      option.setAttribute("value", driverNumber);
      option.setAttribute("label", `${driverNumber} - ${name}`);
      option.setAttribute("name", name);
    }
    this.startListInputs.forEach((startListInput) => {
      startListInput.updateAvailableDrivers();
    });
  }

  onDriverAdded(driverNumber) {
    this.updateAvailableDrivers();
  }

  createCSS(rootDiv) {
    const style = document.createElement("style");
    style.textContent = `
      .race-round-editor-content {
          margin: 0px;
          background: #F0F0F0;
      }
    `;
    rootDiv.appendChild(style);
  }
}

customElements.define("race-round-editor", RaceRoundEditor);
