
function createElementWithClass(element, classes, parent) {
  const el = document.createElement(element);
  classes.forEach((c) => {
    el.classList.add(c);
  });
  parent.appendChild(el);
  return el;
}


class Component extends HTMLElement {
  constructor() {
    super();

    // Create a shadow root
    this.container = document.createElement("div");
    this.appendChild(this.container);
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
      result[parseInt(driverNumbers[i])] = driverNames[i];
    }

    return result;
  }
}
