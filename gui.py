import os
import time
import platform
import presencify
import typing
import tkinter as tk
import ctypes as ct
from tkinter import ttk
from tkinter import messagebox


def sync_presences(local_presences: list, github_presences: list) -> None:
    """
    Sync presences from github repo to local presences
    """
    for local_presence in local_presences:
        if local_presence.folder_name not in list(github_presences.keys()):
            presencify.Logger.write(
                msg=f"If you want to create a new presence, please, check the documentation",
                origin=__name__,
                level="warning",
            )
            message = (
                f"{local_presence.name} not allowed, please use registered presences"
            )
            messagebox.showerror(
                title="Unknow presence",
                message=message,
            )
            raise ValueError(message)
        else:
            local_config = presencify.Utils.hash_string(local_presence.config_file)
            github_config = presencify.Utils.hash_string(
                github_presences[local_presence.folder_name]["config"]
            )
            local_main_code = presencify.Utils.hash_string(local_presence.main_code)
            github_main_code = presencify.Utils.hash_string(
                github_presences[local_presence.folder_name]["main"]
            )
            if local_main_code != github_main_code:
                message = f"{local_presence.folder_name} main.py is modified, please, don't modify it"
                messagebox.showerror(
                    title="Modified file",
                    message=message,
                )
                raise ValueError(message)
            if local_config != github_config:
                message = f"{local_presence.folder_name} config.json is modified, please, don't modify it"
                messagebox.showerror(
                    title="Modified file",
                    message=message,
                )
                raise ValueError(message)
    presencify.Logger.write(msg="Synced presences successfully", origin=__name__)


def get_local_presences() -> typing.List[presencify.Presence]:
    """
    Get all local presences from presences folder
    """
    presences = []
    if not presencify.Utils.exist_folder("presences"):
        os.mkdir("presences")
    subfolders = presencify.Utils.listdirEx("presences", ext=".py", exclude=True)
    for folder in subfolders:
        presences.append(presencify.Presence(location=f"presences/{folder}"))
    presences = [presence for presence in presences if presence.loaded]
    total = len(presences)
    if total == 0:
        presencify.Logger.write(msg="No presences found", origin=__name__)
        return []
    return presences


def on_canvas_configure(event: tk.Event) -> None:
    """
    Update canvas scrollregion when the size of the frame changes.
    """
    canvas.configure(scrollregion=canvas.bbox("all"))


def on_presence_click(
    presence: presencify.Presence, button: ttk.Button, label: ttk.Label, port: int
) -> None:
    # TODO: add a signal when a presence stops completely
    if not presence.connected and not presence.running:
        presence.start(port=port)
        presencify.Logger.write(
            msg=f"Presence {presence.name} started by user", origin=__name__
        )
        label.configure(text="Connected")
    else:
        presencify.Logger.write(
            msg=f"Presence {presence.name} stopped by user", origin=__name__
        )
        presence.stop()
        label.configure(text="Stopping...")
        presence.disconnect()
        label.configure(text="Disconnected")
    button_style = "Connected.TButton" if presence.connected else "Disconnected.TButton"
    button.configure(style=button_style)


def check_repeated_presences(presences: typing.List[presencify.Presence]) -> bool:
    """
    Check if there are repeated presences
    """
    for presence in presences:
        for presence_ in presences:
            if presence == presence_:
                return True
    return False


def set_window(root: tk.Tk) -> None:
    """
    Set window size, title, icon and dark mode
    """
    root.title(f"Presencify v{presencify.__version__}")
    root.geometry("350x200")
    root.resizable(False, False)
    root.iconbitmap("assets/presencify_logo.ico")
    root.update()
    root.iconify()
    DWWMA_USE_IMMERSIVE_DARK_MODE = 20
    set_window_attribute = ct.windll.dwmapi.DwmSetWindowAttribute
    get_parent = ct.windll.user32.GetParent
    hwnd = get_parent(root.winfo_id())
    renduring_policy = DWWMA_USE_IMMERSIVE_DARK_MODE
    value = 1
    value = ct.c_int(value)
    set_window_attribute(hwnd, renduring_policy, ct.byref(value), ct.sizeof(value))
    root.update_idletasks()
    root.deiconify()


def on_gui_close(root: tk.Tk, presences: typing.List[presencify.Presence]) -> None:
    """
    Stop all presences and close the window
    """
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        presencify.Logger.write(msg="Window closed by user", origin=__name__)
        for presence in presences:
            try:
                presence.stop()
                presence.disconnect()
            except Exception as exc:
                presencify.Logger.write(
                    msg=f"Error stopping presence {presence.name}: {exc}",
                    origin=__name__,
                    level="error",
                )
        root.destroy()


if __name__ == "__main__":
    if platform.system() != "Windows":
        message = "This program only works on Windows"
        messagebox.showerror(
            title="OS not supported",
            message=message,
        )
        raise OSError("This program only works on Windows")

    # Window configuration
    root = tk.Tk()
    set_window(root)

    # Opens browser in remote mode
    remote = False
    free_port = presencify.Utils.get_free_port()
    try:
        presencify.Utils.open_remote_browser(free_port)
        remote = True
    except Exception as exc:
        messagebox.showwarning(
            title="Browser",
            message=f"{exc}!\nClose all instances of your default browser and try again if you want to use presences that uses your browser",
        )

    # Presences configuration
    presences = get_local_presences()
    total = len(presences)
    if total == 0:
        message = "No presences found, please, check the documentation"
        messagebox.showerror(
            title="No presences found",
            message=message,
        )
        raise ValueError(message)
    if check_repeated_presences(presences):
        message = "There are repeated presences, please, check your presences"
        messagebox.showerror(
            title="Repeated presences",
            message=message,
        )
        raise ValueError(message)

    allowed_presences = presencify.Utils.fetch_github_presences()
    sync_presences(presences, allowed_presences)

    # Filter browser presences if remote mode is disabled
    if not remote:
        presences = [presence for presence in presences if not presence.uses_browser]
    new_total = len(presences)
    if new_total != total:
        message = "Some presences were removed because they use your browser"
        messagebox.showwarning(
            title="Browser presences",
            message=message,
        )
        presencify.Logger.write(msg=message, origin=__name__)
    if len(presences) == 0:
        message = "No desktop presences found"
        messagebox.showerror(
            title="Presences",
            message=message,
        )
        raise ValueError(message)

    # Presences frame configuration
    main_frame = ttk.Frame(root, height=200)
    main_frame.pack(fill="x")
    main_frame.pack_propagate(False)
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical")
    scrollbar.pack(side="right", fill="y")
    canvas = tk.Canvas(main_frame, yscrollcommand=scrollbar.set)
    canvas.config()
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=canvas.yview)
    list_frame = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=list_frame, anchor="nw")
    list_frame.bind("<Configure>", on_canvas_configure)

    # Button style configuration
    style = ttk.Style()
    style.configure("Connected.TButton", background="green")
    style.configure("Disconnected.TButton", background="red")

    # Set list of presences
    for presence in presences:
        item_frame = ttk.Frame(list_frame)
        item_frame.pack(anchor="w")
        button = ttk.Button(
            item_frame, text=presence.name, style="Disconnected.TButton"
        )
        button.pack(side="left", padx=10, pady=5)
        info_label = ttk.Label(item_frame, text=f"v{presence.version}")
        info_label.pack(side="left", padx=10, pady=5)
        status_label = ttk.Label(item_frame, text="Disconnected")
        status_label.pack(side="left", padx=10, pady=5)
        button.configure(
            command=lambda presence=presence, button=button, label=status_label, port=free_port: on_presence_click(
                presence, button, label, port
            )
        )
        button.bind("<Enter>", lambda event: button.configure(cursor="hand2"))
    canvas.configure(scrollregion=canvas.bbox("all"))

    # Set option menu
    menu = tk.Menu(root)
    root.config(menu=menu)
    menu_list = tk.Menu(menu, tearoff=False)
    menu.add_cascade(label="About", menu=menu_list)
    menu_list.add_command(
        label="Report an issue",
        command=lambda: os.system(
            "start https://github.com/Presencify/Presencify/issues"
        ),
    )
    menu_list.add_command(
        label="Check source code",
        command=lambda: os.system("start https://github.com/Presencify/Presencify"),
    )
    menu_list.add_command(label="Exit", command=lambda: on_gui_close(root, presences))

    # Close window event
    root.protocol("WM_DELETE_WINDOW", lambda: on_gui_close(root, presences))

    # Start main loop
    root.mainloop()
