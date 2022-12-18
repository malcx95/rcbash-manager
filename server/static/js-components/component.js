
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

    // const link = document.createElement("link");
    // link.setAttribute("rel", "stylesheet");
    // link.setAttribute("href", "/static/assets/dist/css/bootstrap.min.css");
    // this.shadow.appendChild(link);

    // this.jquery = document.createElement("script");
    // this.jquery.setAttribute("src", "https://code.jquery.com/jquery-3.6.1.min.js");
    // this.shadow.append(this.jquery);

    // this.bootstrapJS = document.createElement("script");
    // this.bootstrapJS.setAttribute("src", "/static/assets/dist/js/bootstrap.bundle.min.js");
    // this.shadow.append(this.bootstrapJS);

  }
}
