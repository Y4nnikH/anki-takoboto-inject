import pickle
from typing import List, Sequence, Tuple

from anki.notes import NoteId, Note
from anki.models import NoteType
from anki.collection import Collection

import aqt
from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.browser import Browser
from aqt.operations import CollectionOp, OpChanges, QueryOp
from aqt.utils import showInfo

from .utils import log, takoboto_link_word


def setup_browser_menu(browser: Browser):
    """ Add bulk-inject option """
    a = QAction("Takoboto inject links for android", browser)
    a.triggered.connect(lambda: bulk_update_selected_notes(browser))
    browser.form.menuEdit.addSeparator()
    browser.form.menuEdit.addAction(a)
    # TODO: add option to remove links

def sanitize(word: str) -> str:
    # TODO: remove furigana [] notation
    # TODO: remove all non-japanese characters
    return word

def has_fields(notetype: NoteType, fields: list) -> bool:
    if notetype is None:
        return False
    
    n_fields = mw.col.models.field_names(notetype)

    for field in fields:
        if field not in n_fields:
            return False
        
    return True

def bulk_options_dialog(browser: Browser) -> Tuple[dict[str, bool], bool, bool]:
    # TODO: make scrollable and or better shaped

    dialog = QDialog(browser.window())
    dialog.setWindowTitle("Select options")
    dialog.setWindowModality(Qt.WindowModality.WindowModal)
    dialog.setLayout(QGridLayout())

    note_type = mw.col.get_note(browser.selected_notes()[0]).note_type()

    field_names = mw.col.models.field_names(note_type)

    label_1 = QLabel("Select which fields should be updated")

    dialog.layout().addWidget(label_1, 0, 0, 1, 2)

    field_checkboxes = []

    for i, (field_name1, field_name2) in enumerate(zip(field_names[::2], field_names[1::2])):
        field_checkboxes.append(QCheckBox(field_name1))
        field_checkboxes.append(QCheckBox(field_name2))

        dialog.layout().addWidget(field_checkboxes[-2], i + 1, 0, 1, 1)
        dialog.layout().addWidget(field_checkboxes[-1], i + 1, 1, 1, 1)

    if len(field_names) % 2 == 1:
        field_checkboxes.append(QCheckBox(field_names[-1]))
        dialog.layout().addWidget(field_checkboxes[-1], len(field_names) // 2 + 1, 0, 1, 1)

    label_2 = QLabel("If an exact match is not found")
    behaviour_radio = QButtonGroup()
    choose_first_radio = QRadioButton("Choose first match")
    skip_unk_radio = QRadioButton("Skip")
    choose_first_radio.setChecked(True)
    behaviour_radio.addButton(choose_first_radio)
    behaviour_radio.addButton(skip_unk_radio)

    label_3 = QLabel("Where to place links")
    link_radio = QButtonGroup()
    replace_radio = QRadioButton("Linkify word")
    seperate_field_radio = QRadioButton("Add to separate field")
    replace_radio.setChecked(True)
    link_radio.addButton(replace_radio)
    link_radio.addButton(seperate_field_radio)

    label_4 = QLabel("Field")
    field_combo = QComboBox()
    field_combo.addItems(field_names)
    field_combo.setEnabled(False)

    link_radio.buttonClicked.connect(lambda: field_combo.setEnabled(seperate_field_radio.isChecked()))

    ok_button = QPushButton("OK")
    ok_button.clicked.connect(dialog.accept)

    cancel_button = QPushButton("Cancel")
    cancel_button.clicked.connect(dialog.reject)

    offset = (len(field_names) + 1) / 2 + 1

    dialog.layout().addWidget(label_2, offset, 0, 1, 2)
    dialog.layout().addWidget(choose_first_radio, offset + 1, 0, 1, 2)
    dialog.layout().addWidget(skip_unk_radio, offset + 2, 0, 1, 2)
    dialog.layout().addWidget(label_3, offset + 3, 0, 1, 2)
    dialog.layout().addWidget(replace_radio, offset + 4, 0, 1, 2)
    dialog.layout().addWidget(seperate_field_radio, offset + 5, 0, 1, 2)
    dialog.layout().addWidget(label_4, offset + 6, 0, 1, 1)
    dialog.layout().addWidget(field_combo, offset + 6, 1, 1, 1)
    dialog.layout().addWidget(ok_button, offset + 7, 0, 1, 1)
    dialog.layout().addWidget(cancel_button, offset + 7, 1, 1, 1)

    dialog.exec()

    if dialog.result() == QDialog.DialogCode.Accepted:
        selected_fields = {}
        print(len(field_checkboxes))
        for i, field_name in enumerate(field_names):
            print(i, field_name)
            checkbox = field_checkboxes[i]
            selected_fields[field_name] = checkbox.isChecked()
        return selected_fields, choose_first_radio.isChecked(), replace_radio.isChecked(), field_combo.currentText()
    else:
        return None
    
def update_notes(col: Collection, nids: Sequence[NoteId], selected_fields: dict[str, bool], choose_first: bool, linkify_word: bool, link_field: str) -> List[Note]:

    # Load the data
    # {kanji: reading, JMDict id}
    with open("./JMDict_kanji_reading_id.pkl", "rb") as f:
        kanji_reading_id = pickle.load(f)

    updated_notes = []
    
    for i, nid in enumerate(nids):

        aqt.mw.taskman.run_on_main(
            lambda: aqt.mw.progress.update(
                label=f"Processing notes... ({i}/{len(nids)})",
                value=i,
                max=len(nids),
            )
        )

        note = col.get_note(nid)

        if not has_fields(note.note_type(), selected_fields.keys()):
            log("Skipping: wrong note type")
            continue

        links = []

        for field in mw.col.models.field_names(note.note_type()):

            if not selected_fields[field]:
                continue

            word = note[field]

            # TODO: sanitize word

            reading_id_pairs = kanji_reading_id.get(word)

            if reading_id_pairs is None:
                log(f"Skipping field: no JMDict entry found for {word}")
                continue
            ids = [id for reading, id in reading_id_pairs]

            if len(ids) > 1 and not choose_first:
                log(f"Skipping field: Multiple JMDict entries found for {word}")
                continue
                
            reading, id = reading_id_pairs[0]

            word_with_link = takoboto_link_word(word, id)

            if linkify_word:
                note[field] = word_with_link

            links.append(word_with_link)

        if not linkify_word and links:
            if note[link_field] == "":
                note[link_field] = f"Takoboto Link{'s' if len(links) > 1 else ''}: {', '.join(links)}"
            else:
                note[link_field] = note[link_field] + f"\n<br> Takoboto Link{'s' if len(links) > 1 else ''}: {', '.join(links)}"

        if not links:
            log(f"Skipping note: no links found for note {note.id}")
            continue
        
        updated_notes.append(note)
    
    return updated_notes
                   
def bulk_update_selected_notes(browser: Browser):
    options = bulk_options_dialog(browser)

    if options is None:
        return
    
    selected_fields, choose_first, linkify_word, link_field = options
    
    fetch_op = QueryOp(
        parent=browser.window(),
        op=lambda col: update_notes(col, browser.selected_notes(), selected_fields, choose_first, linkify_word, link_field),
        success=lambda notes: commit_changes(browser, browser.col, notes)
    )

    fetch_op.with_progress("Updating notes...").run_in_background()

def commit_changes(browser: Browser, col: Collection, notes: Sequence[Note]):
    if not notes:
        showInfo("No notes to update")
        return
    commit_op(notes, browser.window()).success(lambda op_changes: commit_success(op_changes, len(notes))).run_in_background()

def commit_success(op_changes: OpChanges, n_notes: int):
    log(f"{op_changes}")
    showInfo(f"Updated {n_notes} notes")

def commit_op(notes: Sequence[Note], parent: QWidget) -> CollectionOp[OpChanges]:
    return CollectionOp(
        parent=parent,
        op=lambda col: commit_action(col, notes)
    )

def commit_action(col: Collection, notes: Sequence[Note]) -> OpChanges:
    custom_undo_pos = col.add_custom_undo_entry("Takoboto bulk-inject links")

    for note in notes:
        col.update_note(note)
        op_changes = col.merge_undo_entries(custom_undo_pos)

    return op_changes


def init():
    gui_hooks.browser_menus_did_init.append(setup_browser_menu)  # Bulk add menu entry
