// this script is included on every page via <script src="/static/settings.js">.
// it runs immediately when the page loads (before the user sees anything) so
// the correct text size and colour mode are applied with no visible flicker.

// preferences are stored in localStorage (the browser's built-in key-value store).
// localStorage persists across page loads and browser restarts, but is local to
// this browser/device only. the server never sees these settings.

(function () {
// read saved preferences (defaults to "normal" if nothing has been saved yet)
var text_size = localStorage.getItem("glh_text_size")  || "normal";
var contrast  = localStorage.getItem("glh_contrast")   || "normal";

// apply the settings by setting data attributes on the <html> element.
// the css file then uses selectors like html[data-text-size="large"] to
// override the font size and colours accordingly.
document.documentElement.setAttribute("data-text-size", text_size);
document.documentElement.setAttribute("data-contrast",  contrast);

// inject the settings cog icon into the navbar once the page has loaded.
// doing this in javascript means we only need to add the script once rather
// than manually editing every html template's navbar.
document.addEventListener("DOMContentLoaded", function () {
    var navbar = document.querySelector(".navbar");
    if (!navbar) return;  // safety check in case the page has no navbar

    // create the cog link and add it to the end of the navbar
    var cog_link = document.createElement("a");
    cog_link.href      = "/settings";
    cog_link.className = "settings-icon";
    cog_link.title     = "Accessibility Settings";
    cog_link.innerHTML = "&#9881;";  // gear symbol
    navbar.appendChild(cog_link);
});
})();