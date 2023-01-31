class ResultTable extends Component {
  constructor(result, allDriversDictionary) {
    super();

    this.result = result;
    this.allDriversDictionary = allDriversDictionary;

    const rootDiv = createElementWithClass("div", [], this.container);
    this.tableDiv = createElementWithClass("div", ["table-responsive"], rootDiv);
    this.createCSS(rootDiv);
    this.updateState();
  }

  updateState() {
    this.populateTable();
  }

  populateTable() {
    this.tableDiv.textContent = "";
    const table = createElementWithClass("table", ["table", "table-sm", "table-striped"], this.tableDiv);
    this.createHeader(table);
    const tbody = createElementWithClass("tbody", [], table);

    // the first driver result should be the one with the most laps
    const maxNumLaps = this.result[0][1].length;
    for (let i = 0; i < maxNumLaps; i++) {
      let tr = createElementWithClass("tr", [], tbody);
      let lapCell = createElementWithClass("td", [], tr);
      lapCell.innerHTML = `<b>${i + 1}</b>`;
      this.result.forEach(el => {
        let laptimes = el[1];
        let td = createElementWithClass("td", [], tr);
        if (i < laptimes.length) {
          const lapTimeObj = el[1][i];
          td.textContent = this.formatTime(lapTimeObj);
        }
      });
    }
  }

  formatTime(lapTimeObj) {
    return `${zeroPad(lapTimeObj.minutes, 1)}:${zeroPad(lapTimeObj.seconds, 2)}:${zeroPad(lapTimeObj.milliseconds, 3)}`;
  }

  createHeader(tableElement) {
    const header = createElementWithClass("thead", [], tableElement);
    const headerRow = createElementWithClass("tr", [], header);
    const lapHeader = createElementWithClass("th", [], headerRow);
    lapHeader.innerHTML = "<b>Varv</b>";
    this.result.forEach(el => {
      const number = el[0];
      const name = this.allDriversDictionary[number];
      const th = createElementWithClass("th", [], headerRow);
      th.setAttribute("scope", "col");
      th.textContent = `${number} - ${name}`;
    });
  }

  createCSS(rootDiv) {
    const style = document.createElement("style");
    style.textContent = `
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
}

customElements.define("result-table", ResultTable);

