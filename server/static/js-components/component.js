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
}
