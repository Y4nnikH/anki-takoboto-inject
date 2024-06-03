# Anki-Takoboto-Inject

Hack android Takoboto intent links into any anki cards

Fields will be updated so that the Japanese word will be encapsulated by a link to the android Takoboto app.

- Example CSS to add to card style
```css
a.takoboto-link {
    color: #0078d7;
    text-decoration: none;
}
a.takoboto-link:hover {
    text-decoration: underline;
    text-decoration-style: dashed;
}
a.takoboto-link:visited {
    color: #551a8b;
}
```