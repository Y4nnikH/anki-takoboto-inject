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

## Usage
1. Import add-on
   1. In the desktop app, go to Tools > Add-ons menu item
   2. Click on the View Files button
   3. Add a folder which contains this repo's content
2. Restart Anki ?
3. Select the deck you want to add the links to and open the browser
4. Under the 'Edit' menu item, there should now be a new option called "Takoboto Inject Links for Android"
5. Choose which field(s) to update and press ok
6. All selected notes should be updated if it finds the expression
7. Optional: Undo by pressing ctrl+Z