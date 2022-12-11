class Component extends HTMLElement {
  constructor() {
    super();

    // Create a shadow root
    this.shadow = this.attachShadow({mode: "open"});

    const link = document.createElement("link");
    link.setAttribute("rel", "stylesheet");
    link.setAttribute("href", "/static/assets/dist/css/bootstrap.min.css");
    this.shadow.appendChild(link);

  }
}
