# ---------------------------------------------
# Project: D&D Hoard Combat Tracker
# File: Hoard Tracker.py
# Author: Justin Nieto
# Created: Spring, 2025
# Description: Based of the Lord of Hosts supplamentary materials for D&D, this tool allows 
#   for easy tracking of large groups of enemies. Material for group saves and damage has been
#   ported 1-to-1 from the text
# ---------------------------------------------
import tkinter as tk
from tkinter import simpledialog, messagebox

class Monster:
    def __init__(self, name, count, size, hp_per):
        self.name = name
        self.size = size
        self.hp_per = hp_per
        self.hp_pool = [hp_per] * count  # Individual HP per monster pools allow for manupulation of a the group via individuals

    def total_hp(self):
        return sum(self.hp_pool)

    def count(self):
        return len(self.hp_pool)

    def __str__(self):
        return f"{self.name} (x{self.count()}, {self.size}, {self.hp_per} HP each, {self.total_hp()} HP total)"


class HoardCombatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hoard Manager")

        self.monsters = []

        # UI shit
        self.listbox = tk.Listbox(root, width=60)
        self.listbox.pack(pady=10)

        self.add_button = tk.Button(root, text="Add Creature", command=self.add_monster)
        self.add_button.pack(fill=tk.X)

        self.remove_button = tk.Button(root, text="Remove Creature", command=self.remove_monster)
        self.remove_button.pack(fill=tk.X)

        self.save_button = tk.Button(root, text="Make a Save", command=self.make_save)
        self.save_button.pack(fill=tk.X)

    def add_monster(self):
        name = simpledialog.askstring("Creature Name", "Enter the Creatures's name:")
        if not name:
            return

        try:
            count = int(simpledialog.askstring("Count", f"How many {name}s?"))
        except (TypeError, ValueError):
            messagebox.showerror("Invalid Input", "Count must be a number.")
            return

        size = simpledialog.askstring("Size", f"Enter the size of {name} (e.g., Tiny, Small, Medium, etc):")
        if not size:
            return
# require HP to be an integer
        try:
            hp_per = int(simpledialog.askstring("HP per Creature", f"How many HP does each {name} have?"))
        except (TypeError, ValueError):
            messagebox.showerror("Invalid Input", "HP must be a number.")
            return

        monster = Monster(name, count, size, hp_per)
        self.monsters.append(monster)
        self.update_listbox()


    def remove_monster(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showinfo("Remove Monster", "Please select a monster to remove.")
            return

        index = selection[0]
        del self.monsters[index]
        self.update_listbox()

    def make_save(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showinfo("Make a Save", "Please select a monster to make a save.")
            return

        index = selection[0]
        monster = self.monsters[index]

        try:
            base_damage = int(simpledialog.askstring("Base Damage", "Enter the base damage of the spell:"))
        except (TypeError, ValueError):
            messagebox.showerror("Invalid Input", "Damage must be a number.")
            return

        # Open shape and save setting window
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Save Settings")

        # Shape selection
        tk.Label(settings_window, text="Select area of effect shape:").pack(pady=5)
        shape_var = tk.StringVar(value="Cone")
        shape_options = ["Cone", "Cube", "Cylinder", "Line", "Sphere"]
        tk.OptionMenu(settings_window, shape_var, *shape_options).pack(pady=5)

        # Spell size
        tk.Label(settings_window, text="Enter spell size (e.g., 30 for 30 ft):").pack(pady=5)
        spell_size_entry = tk.Entry(settings_window)
        spell_size_entry.pack(pady=5)

        # Save behavior checkboxes
        tk.Label(settings_window, text="Choose save behavior (only one):").pack(pady=5)
        save_half_var = tk.IntVar()
        save_none_var = tk.IntVar()

        def on_half():
            save_none_var.set(0)

        def on_none():
            save_half_var.set(0)

        tk.Checkbutton(settings_window, text="Save = Half Damage", variable=save_half_var, command=on_half).pack()
        tk.Checkbutton(settings_window, text="Save = No Damage", variable=save_none_var, command=on_none).pack()

    # Sections come in 4 varieties and represent the amount of creatures who make their save via a +/- save
    # This has not been added in and still requires a roll
    # (D20 Roll + sav) +/-5 = amount of sections who made the save
    # DC 15 monster rolled a 15 = 1 save, -5(10) = 1 fail, +5(20) 2 saves. So you choose 2
    # I feel like this makes sense
        tk.Label(settings_window, text="How many sections made their save?").pack(pady=5)
        section_var = tk.StringVar(value="0")
        tk.OptionMenu(settings_window, section_var, "0", "1", "2", "3").pack(pady=5)

        def proceed():
            if not (save_half_var.get() ^ save_none_var.get()):
                messagebox.showerror("Input Error", "Select exactly one save behavior.")
                return

            try:
                spell_size = int(spell_size_entry.get())
            except ValueError:
                messagebox.showerror("Input Error", "Spell size must be an integer.")
                return

            settings_window.destroy()
            self.process_save(
                monster,
                base_damage,
                shape_var.get(),
                spell_size,
                save_half_var.get() == 1,
                int(section_var.get())
            )

        tk.Button(settings_window, text="Calculate Damage", command=proceed).pack(pady=10)

    def process_save(self, monster, base_damage, shape, spell_size, is_half, sections_made_save):
    # This is all math from the book - I dont know why they chose these numbers I just put em in
    # The monsters size and the shape of the spell effects the damage dealt. The small the monster the more can be hit by the aoe an there for the more damage the
    # AoE shape multiplier
        shape_multipliers = {
            "Cone": spell_size / 10,
            "Cube": spell_size / 5,
            "Cylinder": spell_size / 5,
            "Line": spell_size / 30,
            "Sphere": spell_size / 5
        }

        shape_damage = shape_multipliers.get(shape, 1) * base_damage

    # Monster size multiplier
        size_modifiers = {
            "Tiny": 2,
            "Small": 1,
            "Medium": 1,
            "Large": 0.5,
            "Huge": 1 / 3,
            "Gargantuan": 0.25
        }
        size_factor = size_modifiers.get(monster.size.capitalize(), 1)
        adjusted_damage = shape_damage * size_factor

    # Save reductions
        reduction_table_half = {
            0: 1.0,
            1: 5 / 6,
            2: 2 / 3,
            3: 0.5
        }

        reduction_table_none = {
            0: 1.0,
            1: 2 / 3,
            2: 1 / 3,
            3: 0.0
        }

        if is_half:
            reduction = reduction_table_half.get(sections_made_save, 1.0)
        else:
            reduction = reduction_table_none.get(sections_made_save, 1.0)

        final_damage = int(adjusted_damage * reduction)

    # Apply damage to individual monsters
        damage_remaining = final_damage
        killed = 0

    # Apply damage the weakest first
        monster.hp_pool.sort()

        for i in range(len(monster.hp_pool)):
            hp = monster.hp_pool[i]
            if damage_remaining >= hp:
                damage_remaining -= hp
                monster.hp_pool[i] = 0
                killed += 1
            else:
                monster.hp_pool[i] -= damage_remaining
                damage_remaining = 0
                break

        # Remove dead monsters
        monster.hp_pool = [hp for hp in monster.hp_pool if hp > 0]

        # Update or remove monster
        if not monster.hp_pool:
            self.monsters.remove(monster)
            self.update_listbox()
            messagebox.showinfo("Unit Eliminated", f"{monster.name} has been destroyed!")
            return

        self.update_listbox()
        messagebox.showinfo(
            "Damage Applied",
            f"{monster.name} took {final_damage} damage.\n"
            f"{killed} creatures destroyed.\n"
            f"{len(monster.hp_pool)} remain with total {sum(monster.hp_pool)} HP."
        )
    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for monster in self.monsters:
            self.listbox.insert(tk.END, str(monster))


if __name__ == "__main__":
    root = tk.Tk()
    app = HoardCombatApp(root)
    root.mainloop()
