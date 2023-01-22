let getDriverNumbersFromDatalist = (datalist) => {
  let options = [];
  for (let prop of datalist.options) {
    options.push(prop.value);
  }
  return options;
}

let getDriverNamesFromDatalist = (datalist) => {
  let options = [];
  for (let prop of datalist.options) {
    options.push(prop.getAttribute("name"));
  }
  return options;
}

let getDriverDictionaryFromDatalist = (datalist) => {
  let driverNumbers = getDriverNumbersFromDatalist(datalist);
  let driverNames = getDriverNamesFromDatalist(datalist);

  let result = {};

  for (let i = 0; i < driverNames.length; i++) {
    result[parseInt(driverNumbers[i])] = driverNames[i];
  }

  return result;
}
