const AVAILABLE_DRIVERS_ID = "availableDriversDatalist";

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

    this.rcclassGroups = [
      {rcclass: "4WD", group: "A"},
      {rcclass: "2WD", group: "A"}
    ];
    this.availableDriversDatalist = createElementWithClass("datalist", [], this.container);
    this.availableDriversDatalist.id = AVAILABLE_DRIVERS_ID;
    this.startListInputs = [];
    this.updateAvailableDrivers();

    this.rcclassGroups.forEach((rcclassGroup) => {
      const startListInput = new StartListInput(rcclassGroup.rcclass, rcclassGroup.group, AVAILABLE_DRIVERS_ID);
      startListInput.rcclassEditable = true;
      startListInput.onlyEditable = true;
      startListInput.onDriverAdded = (d) => this.onDriverAdded(d);
      startListInput.updateState();
      this.startListInputs.push(startListInput);
    });

    this.container.classList.add(
      "row", "row-cols-1", "row-cols-md-2", "row-cols-lg-3", "g-3", "race-round-editor-content");
    for (let i = 0; i < this.rcclassGroups.length; i++) {
      const rcclassGroup = this.rcclassGroups[i];
      const startListInput = this.startListInputs[i];
      this.container.appendChild(startListInput);
    }

    this.createCSS(this.container);
    this.addPlaceHolderCard();
  }

  addPlaceHolderCard() {
    const cardDiv = createElementWithClass("div", ["card", "startlistcard", "placeholder-card"], this.container);
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
      .placeholder-card {
        border-style: dashed;
        min-height: 400px;
      }
    `;
    rootDiv.appendChild(style);
  }
}

customElements.define("race-round-editor", RaceRoundEditor);
