/* globals Chart:false, feather:false */

var startList = [];

$( document ).ready(() => {
  feather.replace({ 'aria-hidden': 'true' });

  //  let driversDataList = $("#drivers")[0];
  //  let options = getOptionsFromDatalist(driversDataList);
  //  console.log(options);
  //
  //  $('#driverInputBox').keypress((event) => {
  //    var keycode = (event.keyCode ? event.keyCode : event.which);
  //    if (keycode == '13') {
  //      addInputToListIfValid(event.target, event.target.value, options);
  //    }
  //  });
});

// function addInputToListIfValid(textbox, value, options) {
//   if (options.includes(value)) {
//     console.log(value);
//     textbox.value = "";
//   }
// }
// 
// function getOptionsFromDatalist(datalist) {
//   let options = [];
//   for (let prop of datalist.options) {
//     options.push(prop.value);
//   }
//   return options;
// }

//
// function constructHtmlTable(datalist) {
//   // create the table element
//   var table = document.createElement("table");
//   table.classList.add("table table-striped table-sm")
// 
//   // create header rows
//   var header = document.createElement("thead");
//   var headerRow = document.createElement("tr");
// 
//   var headerRow = document.createElement()
// 
//   // create the table cells
//   var cell1 = document.createElement("td");
//   var cell2 = document.createElement("td");
//   var cell3 = document.createElement("td");
//   var cell4 = document.createElement("td");
// 
//   // add content to the cells
//   cell1.innerHTML = "Row 1, Cell 1";
//   cell2.innerHTML = "Row 1, Cell 2";
//   cell3.innerHTML = "Row 2, Cell 1";
//   cell4.innerHTML = "Row 2, Cell 2";
// 
//   // add the cells to the rows
//   row1.appendChild(cell1);
//   row1.appendChild(cell2);
//   row2.appendChild(cell3);
//   row2.appendChild(cell4);
// 
//   // add the rows to the table
//   table.appendChild(row1);
//   table.appendChild(row2);
// 
//   // add the table to the document
//   document.body.appendChild(table);
// 
// }
/*
 * TODO
 *
 * Ha en js-array med startlistan.
 * Koden för att lägga till en förare ska lägga till i denna lista.
 * När listan uppdateras ska kod köras som fyller en html-tabell med startlistan.
 */
