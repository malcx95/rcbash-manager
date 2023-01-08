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

    if (!this.hasAttribute("add-dropdown-list-id")) {
      console.error("RaceRoundEditor used without add-dropdown-list-id");
      return;
    }

    if (!this.hasAttribute("add-dropdown-button-id")) {
      console.error("RaceRoundEditor used without add-dropdown-button-id");
      return;
    }

    let addGroupDropdownListId = this.getAttribute("add-dropdown-list-id");
    let addGroupDropdownButtonId = this.getAttribute("add-dropdown-button-id");
    this.addGroupDropdownList = document.getElementById(addGroupDropdownListId);
    this.addGroupDropdownButton = document.getElementById(addGroupDropdownButtonId);

    const initialRcclassGroups = [
      {rcclass: "4WD", group: "A"},
      {rcclass: "2WD", group: "A"}
    ];

    this.content = createElementWithClass("div", ["row", "row-cols-1", "row-cols-md-2", "row-cols-lg-3", "g-3", "race-round-editor-content"], this.container);

    this.lowestTakenGroupIndices = {"4WD": 0, "2WD": 0};
    this.availableDriversDatalist = createElementWithClass("datalist", [], this.container);
    this.availableDriversDatalist.id = AVAILABLE_DRIVERS_ID;
    this.startListInputs = [];
    this.updateAvailableDrivers();

    initialRcclassGroups.forEach((rcclassGroup) => {
      this.createStartListInput(rcclassGroup.rcclass, rcclassGroup.group);
    });

    this.updateStartListInputs();
    this.updateDropdownOptions();

    this.createCSS(this.container);
  }

  getValue() {
    let startLists = {};
    this.startListInputs.forEach((input) => {
      let rcclass = input.rcclass;
      let group = input.group;
      if (!(rcclass in startLists)) {
        startLists[rcclass] = {};
      }
      startLists[rcclass][group] = input.drivers;
    });
    return startLists;
  }

  updateStartListInputs() {
    this.startListInputs.sort((a, b) => {
      if (a.rcclass != b.rcclass) {
        return a.rcclass > b.rcclass;
      }
      return a.group > b.group;
    });
    this.content.textContent = "";
    let first2WDIndex = -1;
    let first4WDIndex = -1;
    let last2WDIndex = 0;
    let last4WDIndex = 0;

    this.startListInputs.forEach((startListInput, i) => {
      if (startListInput.rcclass === "4WD") {
        last4WDIndex = i;
        first4WDIndex = first4WDIndex === -1 ? i : first4WDIndex;
      } else {
        last2WDIndex = i;
        first2WDIndex = first2WDIndex === -1 ? i : first2WDIndex;
      }
    });

    this.startListInputs.forEach((startListInput, i) => {
      // the start list should not be deletable if it is the only group of that class,
      // but should be if there are more than one per group and it's the lowest group
      startListInput.deletable =
        (i === last4WDIndex || i === last2WDIndex)
        && i !== first4WDIndex && i !== first2WDIndex;
      this.content.appendChild(startListInput);
      startListInput.updateState();
    });
  }

  createStartListInput(rcclass, group) {
    const startListInput = new StartListInput(rcclass, group, AVAILABLE_DRIVERS_ID);
    startListInput.rcclassEditable = false;
    startListInput.setOnlyEditable(true);
    startListInput.deletable = false;
    startListInput.onDriverAdded = (d) => this.updateAvailableDrivers();
    startListInput.onDriverRemoved = (d) => this.updateAvailableDrivers();
    startListInput.onDeleteClicked = (s) => this.onStartListDeleted(s);
    this.startListInputs.push(startListInput);
  }

  onStartListDeleted(startListInput) {
    const rcclass = startListInput.rcclass;
    const group = startListInput.group;

    // create new list with everything that does not match
    // the rcclass and group, effectively removing it
    let newStartListInputs = this.startListInputs.filter((input) =>
      !(input.rcclass === rcclass && input.group === group)
    );

    this.startListInputs = newStartListInputs;
    this.lowestTakenGroupIndices[rcclass] -= 1;
    this.updateAvailableDrivers();
    this.updateDropdownOptions();
    this.updateStartListInputs();
  }

  updateDropdownOptions() {
    this.addGroupDropdownList.textContent = "";
    let groups = this.getAvailableGroupsToAdd();
    if (Object.keys(groups).length === 0) {

      this.addGroupDropdownButton.disabled = true;
      // without this the dropdown will be visible when the button is disabled
      this.addGroupDropdownList.className = "";
      this.addGroupDropdownList.classList.add("dropdown-menu");

    } else {
      this.addGroupDropdownButton.disabled = false;
    }

    for (const [rcclass, group] of Object.entries(groups)) {
      let listItem = createElementWithClass("li", [], this.addGroupDropdownList);
      let link = createElementWithClass("a", ["dropdown-item", "pointer"], listItem);
      link.onclick = (event) => {
        this.lowestTakenGroupIndices[rcclass] += 1;
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
      let group = GROUPS[this.lowestTakenGroupIndices[rcclass] + 1];
      if (group !== undefined) {
        groups[rcclass] = group;
      }
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
