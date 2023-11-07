from datetime import datetime

# import the main window object (mw) from aqt
from aqt import mw, gui_hooks

# import the "show info" tool from utils.py
from aqt.utils import showInfo, qconnect

from aqt.qt import QAction

# We're going to add a menu item below. First we want to create a function to
# be called when the menu item is activated.

TABLE_NAME = "notes_modtime"

menu_group = mw.form.menuTools.addMenu("Backup note modtime")


def backup_notemod() -> None:
    timestamp = int(datetime.now().timestamp())
    t = datetime.fromtimestamp(timestamp)

    mw.col.db.execute(
        f"""
    CREATE TABLE {TABLE_NAME} (
        id    INT NOT NULL,
        mod   INT NOT NULL,
        PRIMARY KEY (id)
    );
    """
    )
    mw.col.db.execute(
        f"INSERT INTO {TABLE_NAME} (id, mod) VALUES (0, ?)",
        timestamp,
    )
    mw.col.db.execute(f"INSERT INTO {TABLE_NAME} SELECT id, mod FROM notes")

    update_state()

    # show a message box
    showInfo(f"Backed up note modtime ({t})")


# create a new menu item and it to the tools menu
b_backup = QAction("Backup", mw)
b_backup.setDisabled(True)
qconnect(b_backup.triggered, backup_notemod)
# and add it to the tools menu
menu_group.addAction(b_backup)


def restore_backup() -> None:
    r = mw.col.db.execute(f"SELECT mod FROM {TABLE_NAME} WHERE id = 0")[0]

    mw.col.db.execute(
        f"""
    UPDATE notes
    SET mod = b.mod
    FROM (SELECT id, mod FROM {TABLE_NAME}) AS b
    WHERE notes.id = b.id;
    """
    )
    mw.col.db.execute(f"DROP TABLE {TABLE_NAME};")

    update_state()

    # show a message box
    showInfo(f"Restore note modtime ({datetime.fromtimestamp(r[0])})")


# create a new menu item and it to the tools menu
b_restore = QAction("Restore", mw)
b_restore.setVisible(False)
qconnect(b_restore.triggered, restore_backup)
menu_group.addAction(b_restore)


def delete_backup() -> None:
    r = mw.col.db.execute(f"SELECT mod FROM {TABLE_NAME} WHERE id = 0")[0]

    mw.col.db.execute(
        f"""
    DROP TABLE {TABLE_NAME};
    """
    )

    update_state()

    # show a message box
    showInfo(f"Cleaned note modtime ({datetime.fromtimestamp(r[0])})")


# create a new menu item and it to the tools menu
b_delete = QAction("Clean up", mw)
b_delete.setVisible(False)
qconnect(b_delete.triggered, delete_backup)
menu_group.addAction(b_delete)


def update_state(*args):
    has_table = bool(
        len(mw.col.db.execute("SELECT * FROM pragma_table_info(?) LIMIT 1", TABLE_NAME))
    )
    b_backup.setDisabled(False)
    b_backup.setVisible(not has_table)
    b_restore.setVisible(has_table)
    b_delete.setVisible(has_table)


gui_hooks.collection_did_load.append(update_state)
