import os
import random
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
from google import genai

load_dotenv(Path(__file__).resolve().with_name(".env"))
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

# ================================================================
# 1. PAGE SETUP & 10-SCENE SEQUENCE
# ================================================================
st.set_page_config(
    page_title="Ursa Major: The White-Haired Calamity",
    page_icon="🏴‍☠️",
    layout="centered",
)
st.title("🏴‍☠️ Ursa Major: The White-Haired Calamity")

SCENES = [
    "quarterdeck",
    "galley",
    "misty_cove",
    "crows_nest",
    "seastone_grotto",
    "driftwood_dock",
    "rival_ambush",
    "storm_squall",
    "blockade_strait",
    "open_horizon",
]

# ================================================================
# 2. STATE & REUSABLE HELPER FUNCTIONS
# ================================================================
if "game_started" not in st.session_state:
    st.session_state.game_started = False


def init_crew_game(
    crew_name: str,
    race: str,
    gender: str,
    df_category: str,
    df_name: str,
    weapon: str,
):
    """Initialize state once when the player sets sail with Captain Seraph."""
    st.session_state.game_started = True
    st.session_state.scene = SCENES[0]
    st.session_state.crew_name = crew_name
    st.session_state.race = race
    st.session_state.gender = gender
    st.session_state.df_category = df_category
    st.session_state.df_name = df_name if df_category != "None (No Devil Fruit)" else "None"
    st.session_state.weapon = weapon

    st.session_state.health = 5
    st.session_state.max_health = 5
    st.session_state.inventory = ["Log Pose", weapon]
    st.session_state.result_type = ""
    st.session_state.result_message = ""
    st.session_state.result_value = ""
    st.session_state.action_complete = False
    st.session_state.escaped = False


def restart_game():
    st.session_state.clear()
    st.rerun()


def add_item(item: str):
    if item not in st.session_state.inventory:
        st.session_state.inventory.append(item)


def has_item(item: str) -> bool:
    return item in st.session_state.inventory


def remove_item(item: str):
    if item in st.session_state.inventory:
        st.session_state.inventory.remove(item)


def take_damage(amount: int):
    st.session_state.health = max(0, st.session_state.health - amount)


def heal_player(amount: int) -> int:
    before = st.session_state.health
    st.session_state.health = min(st.session_state.max_health, st.session_state.health + amount)
    return st.session_state.health - before


def roll_dice() -> int:
    return random.randint(1, 6)


def generate_story(scene_label: str, action: str, outcome: str, fallback: str) -> str:
    """Use Gemini to narrate a Python-decided outcome, with safe fallback text."""
    if client is None:
        return fallback

    crew_summary = (
        f"{st.session_state.crew_name} "
        f"({st.session_state.race}, {st.session_state.gender}, "
        f"Devil Fruit: {st.session_state.df_name}, "
        f"Weapon: {st.session_state.weapon})"
    )
    inv_text = ", ".join(st.session_state.inventory) if st.session_state.inventory else "Empty"

    prompt = f"""
You are the narrator for a One Piece-inspired dark-sea adventure called
'Ursa Major: The White-Haired Calamity', featuring Captain Seraph D. Orion.

Crewmate: {crew_summary}
Scene: {scene_label}
Health: {st.session_state.health}/{st.session_state.max_health}
Inventory: {inv_text}
Action: {action}
Outcome: {outcome}

Write 200-300 words in second person with graphic nautical/pirate atmosphere.
Do NOT change the outcome, health, inventory, or introduce new choices.
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text.strip() if response.text else fallback
    except Exception:
        return fallback


def set_result(result_type: str, message: str, value: str = ""):
    st.session_state.result_type = result_type
    st.session_state.result_message = message
    st.session_state.result_value = value
    st.session_state.action_complete = True
    st.rerun()


def show_result():
    kind = st.session_state.result_type
    val = st.session_state.result_value

    if kind == "item":
        st.success(f"🎒 Acquired: {val}")
    elif kind == "damage":
        st.error(f"💥 Health lost: {val}")
    elif kind == "heal":
        st.success(f"💚 Health restored: {val}")
    elif kind == "success":
        st.success("✅ Action succeeded!")
    else:
        st.info("🌊 The voyage continues...")

    st.write(st.session_state.result_message)


def move_to_next_scene():
    idx = SCENES.index(st.session_state.scene)
    st.session_state.result_type = ""
    st.session_state.result_message = ""
    st.session_state.result_value = ""
    st.session_state.action_complete = False
    if idx + 1 < len(SCENES):
        st.session_state.scene = SCENES[idx + 1]
    st.rerun()


def show_continue_button(label: str = "Next Scene ➡️"):
    if st.button(label):
        move_to_next_scene()


def show_scene_header(title: str, description: str):
    scene_num = SCENES.index(st.session_state.scene) + 1
    st.caption(f"Scene {scene_num} of {len(SCENES)} — Ship: Ursa Major")
    st.header(title)
    st.write(description)


def show_crew_sidebar():
    st.sidebar.subheader("🏴‍☠️ Crewmate Profile")
    st.sidebar.write(f"**Name:** {st.session_state.crew_name}")
    st.sidebar.write(f"**Race:** {st.session_state.race}")
    st.sidebar.write(f"**Gender:** {st.session_state.gender}")
    st.sidebar.write(f"**Devil Fruit:** {st.session_state.df_name} ({st.session_state.df_category})")
    st.sidebar.write(f"**Weapon:** {st.session_state.weapon}")
    st.sidebar.divider()
    st.sidebar.write(f"❤️ **Health:** {st.session_state.health}/{st.session_state.max_health}")
    st.sidebar.write(f"🎒 **Inventory:** {', '.join(st.session_state.inventory)}")
    st.sidebar.divider()
    if st.sidebar.button("🔄 Restart Voyage"):
        restart_game()


# ================================================================
# 3. START SCREEN — CUSTOM CREWMATE CREATION
# ================================================================
if not st.session_state.game_started:
    st.write(
        "Join **Captain Seraph D. Orion** (*The White-Haired Calamity*) aboard the "
        "**Ursa Major** across perilous *One Piece* seas. please Create your crewmate to begin."
    )

    crew_name = st.text_input("Crewmate Name")

    race_choice = st.selectbox(
        "Race",
        ["Human", "three eyed tribe", "Fish-Man", "merefolk", "Skypiean", "Mink", "Giant", "buaccanaer", "Custom"],
    )
    custom_race = st.text_input("Custom Race (if selected)") if race_choice == "Custom" else ""
    final_race = (
        custom_race.strip() if race_choice == "Custom" and custom_race.strip() else race_choice
    )

    gender = st.selectbox(
        "Gender",
        ["Male", "Female", "Non-binary", "Other"],
    )

    df_category = st.selectbox(
        "Devil Fruit",
        ["None (No Devil Fruit)", "Canon Devil Fruit", "Unique / Custom Devil Fruit"],
    )
    df_name = ""
    if df_category != "None (No Devil Fruit)":
        df_name = st.text_input("Devil Fruit Name & Power (e.g., Paramecia / Zoan / Logia)")

    weapon_choice = st.selectbox(
        "Preferred Weapon",
        ["Cutlass", "greatsword", "katana", "Twin Daggers", "Flintlock Pistol", "rifle", "blunderbuss", "Polearm / Naginata", "Bo Staff", "Custom"],
    )
    custom_weapon = (
        st.text_input("Custom Weapon (if selected)") if weapon_choice == "Custom" else ""
    )
    final_weapon = (
        custom_weapon.strip() if weapon_choice == "Custom" and custom_weapon.strip() else weapon_choice
    )

    if st.button("⚓ Set Sail with Captain Seraph"):
        if not crew_name.strip():
            st.warning("Please enter your new crewmate's name first.")
        elif df_category != "None (No Devil Fruit)" and not df_name.strip():
            st.warning("Please enter a Devil Fruit name or select 'None (No Devil Fruit)'.")
        else:
            init_crew_game(
                crew_name=crew_name.strip(),
                race=final_race,
                gender=gender,
                df_category=df_category,
                df_name=df_name.strip(),
                weapon=final_weapon,
            )
            st.rerun()

# ================================================================
# 4. MAIN GAMEPLAY — ALL 10 SCENES
# ================================================================
else:
    show_crew_sidebar()
    scene = st.session_state.scene

    if st.session_state.health <= 0:
        show_scene_header(
            "💀 Voyage Lost",
            f"The seas is claim for now {st.session_state.crew_name} and push the Ursa Major off course.",
        )
        st.error("Game Over — Your health reached 0.")
        if st.button("🔄 Try Again"):
            restart_game()
        st.stop()

    # SCENE 1 — QUARTERDECK OF THE URSA MAJOR
    if scene == "quarterdeck":
        show_scene_header(
            "⚓ Scene 1: Quarterdeck of the Ursa Major",
            "White hair whipping in the fresh salt wind, Captain Seraph D. Orion stands at the helm "
            "as storm clouds start to gather ahead on the Grand Line.",
        )
        show_continue_button("Head Below to the Galley please to continue ➡️")

    # SCENE 2 — GALLEY & SUPPLY HOLD
    elif scene == "galley":
        show_scene_header(
            "🍲 Scene 2: Galley & Supply Hold",
            "Lanterns swing back and forward over ration barrels, gun powder barrels and crates strapped down against rough swells.",
        )
        if not st.session_state.action_complete:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Search the Supply Crates"):
                    add_item("Soothe-healing-Brew")
                    story = generate_story(
                        "Galley & Supply Hold",
                        "searching the supply crates",
                        "You find a Soothe-healing-Brew tonic.",
                        "Tucked behind a stack of hardtack barrels, you uncover a sealed bottle of Soothe-healing-Brew.",
                    )
                    set_result("item", story, "Soothe-Brew")
            with col2:
                if st.button("Skip & Head to the Cove"):
                    story = generate_story(
                        "Galley & Supply Hold",
                        "leaving the crates untouched",
                        "You keep moving without opening the crates.",
                        "You leave the swaying crates untouched and head toward the deck exit.",
                    )
                    set_result("story", story)
        else:
            show_result()
            show_continue_button()

    # SCENE 3 — MISTY COVE & WRECKED HULL
    elif scene == "misty_cove":
        show_scene_header(
            "🌫️ Scene 3: Misty Cove & Wrecked Hull",
            "Sea fog clings to a splintered warped hull wedged between dark rocks and foaming white surf.",
        )
        if not st.session_state.action_complete:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Salvage the Wreckage"):
                    add_item("Log Pose Clamp")
                    story = generate_story(
                        "Misty Cove & Wrecked Hull",
                        "salvaging gear from the wrecked hull",
                        "You recover a Log Pose Clamp.",
                        "Bracing against the cold swell, you pry loose a sturdy Log Pose Clamp from the broken deck.",
                    )
                    set_result("item", story, "Log Pose Clamp")
            with col2:
                if st.button("Stay in Safe Waters"):
                    story = generate_story(
                        "Misty Cove & Wrecked Hull",
                        "staying clear of the jagged wreckage",
                        "You avoid the hazardous rocks safely.",
                        "You steer clear of the jagged hull, letting the fog drift past without risk.",
                    )
                    set_result("story", story)
        else:
            show_result()
            show_continue_button()

    # SCENE 4 — CROW'S NEST & ARMOURY
    elif scene == "crows_nest":
        show_scene_header(
            "🔭 Scene 4: Crow's Nest & Armoury",
            "High above the deck, you check the horizon and inspect your gear alongside Seraph.",
        )
        if not st.session_state.action_complete:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Scout Distant Sails"):
                    story = generate_story(
                        "Crow's Nest & Armoury",
                        "scouting the horizon for threats",
                        "You spot rival silhouettes early and prepare.",
                        "From the high perch, you spot faint sails on the horizon and warn the deck.",
                    )
                    set_result("success", story)
            with col2:
                if st.button("Ready Weapon & Stance"):
                    story = generate_story(
                        "Crow's Nest & Armoury",
                        "checking your weapon and stance",
                        "You steady your grip and prepare for trouble.",
                        "You test your balance and grip on your weapon as the Ursa Major rides the swell.",
                    )
                    set_result("story", story)
        else:
            show_result()
            show_continue_button()

    # SCENE 5 — SUNKEN SEA-STONE GROTTO
    elif scene == "seastone_grotto":
        show_scene_header(
            "🪨 Scene 5: Sunken Sea-Stone Grotto",
            "Faintly humming sea-stone veins line the damp cavern walls above dark tide pools.",
        )
        if not st.session_state.action_complete:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Harvest Sea-Stone Bolt"):
                    add_item("Sea-Stone Bolt")
                    story = generate_story(
                        "Sunken Sea-Stone Grotto",
                        "harvesting a Sea-Stone Bolt from the cavern vein",
                        "You claim a Sea-Stone Bolt.",
                        "You chip free a dense Sea-Stone Bolt from the cool stone wall and stow it safely.",
                    )
                    set_result("item", story, "Sea-Stone Bolt")
            with col2:
                if st.button("Pass by Quietly"):
                    story = generate_story(
                        "Sunken Sea-Stone Grotto",
                        "passing through the grotto without harvesting",
                        "You move through the cavern undisturbed.",
                        "You keep your distance from the humming stone and slip past the dark water.",
                    )
                    set_result("story", story)
        else:
            show_result()
            show_continue_button()

    # SCENE 6 — SMUGGLER'S DRIFTWOOD DOCK
    elif scene == "driftwood_dock":
        show_scene_header(
            "🪵 Scene 6: Smuggler's Driftwood Dock",
            "Creaking timber jetties jut out over restless currents beneath a heavy sky.",
        )
        if not st.session_state.action_complete:
            has_brew = has_item("Soothe-Brew")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Drink Soothe-Brew", disabled=not has_brew):
                    remove_item("Soothe-Brew")
                    healed = heal_player(2)
                    story = generate_story(
                        "Smuggler's Driftwood Dock",
                        "drinking a Soothe-Brew to recover",
                        f"You drink the Soothe-Brew and recover {healed} health.",
                        f"The warm Soothe-Brew settles your breath, restoring {healed} health before you push on.",
                    )
                    set_result("heal", story, str(healed))
            with col2:
                if st.button("Keep Watch & Move On"):
                    story = generate_story(
                        "Smuggler's Driftwood Dock",
                        "staying alert at the dock and moving ahead",
                        "You keep watch and press toward open water.",
                        "You stay sharp on the creaking planks and signal to weigh anchor.",
                    )
                    set_result("story", story)
        else:
            show_result()
            show_continue_button()

    # SCENE 7 — RIVAL AMBUSH & SEA HAZARD (DICE ROLL)
    elif scene == "rival_ambush":
        show_scene_header(
            "🎲 Scene 7: Rival Ambush & Sea Hazard",
            "Pursuers close in through chopping waves—Captain Seraph calls for decisive action!",
        )
        if not st.session_state.action_complete:
            bonus = 2 if (has_item("Sea-Stone Bolt") or has_item("Log Pose Clamp")) else 0
            if bonus > 0:
                st.info("✨ Gear bonus active (+2 to dice roll) from your collected item.")
            if st.button("Roll Die to Break Through (Target 4+)"):
                roll = roll_dice() + bonus
                if roll >= 4:
                    story = generate_story(
                        "Rival Ambush & Sea Hazard",
                        "breaking through the ambush with a successful roll",
                        "You overcome the ambush and keep the ship moving.",
                        "Timing the swell with Captain Seraph, you break through the ambush cleanly.",
                    )
                    set_result("success", story)
                else:
                    take_damage(1)
                    story = generate_story(
                        "Rival Ambush & Sea Hazard",
                        "clashing with pursuers in rough seas",
                        "You take 1 damage during the rough clash.",
                        "A heavy blow and crashing spray hit hard—you lose 1 health fighting through.",
                    )
                    set_result("damage", story, "1")
        else:
            show_result()
            show_continue_button()

    # SCENE 8 — STORM SQUALL & RIGGING TRIAL
    elif scene == "storm_squall":
        show_scene_header(
            "⛈️ Scene 8: Storm Squall & Rigging Trial",
            "Gale winds howl and lightning flashes as the Ursa Major hits a sudden squall.",
        )
        if not st.session_state.action_complete:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Secure the Rigging"):
                    story = generate_story(
                        "Storm Squall & Rigging Trial",
                        "securing the rigging against gale winds",
                        "The sails hold firm through the squall.",
                        "Bracing against the gale, you haul the lines tight and keep the mast steady.",
                    )
                    set_result("success", story)
            with col2:
                if st.button("Ride Out the Gusts"):
                    take_damage(1)
                    story = generate_story(
                        "Storm Squall & Rigging Trial",
                        "riding out a fierce gust on deck",
                        "A sudden squall knocks you back for 1 damage.",
                        "A sudden gust slams the deck, leaving you bruised for 1 health before the squall eases.",
                    )
                    set_result("damage", story, "1")
        else:
            show_result()
            show_continue_button()

    # SCENE 9 — BLOCKADE STRAIT
    elif scene == "blockade_strait":
        show_scene_header(
            "🚧 Scene 9: Blockade Strait",
            "Steep sea cliffs and patrolling vessels narrow the final channel toward open sea.",
        )
        if not st.session_state.action_complete:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Chart Narrow Channel"):
                    story = generate_story(
                        "Blockade Strait",
                        "navigating the narrow strait toward the exit",
                        "You thread the strait and spot the open horizon ahead.",
                        "Guiding the Ursa Major through the tight channel, you sight clear water ahead.",
                    )
                    set_result("success", story)
            with col2:
                if st.button("Make a Reckless Dash"):
                    take_damage(1)
                    story = generate_story(
                        "Blockade Strait",
                        "dashing straight through the narrow strait",
                        "Rough water costs 1 health on the way through.",
                        "You charge through the narrow strait; rough spray and impact cost 1 health.",
                    )
                    set_result("damage", story, "1")
        else:
            show_result()
            show_continue_button()

    # SCENE 10 — OPEN HORIZON
    elif scene == "open_horizon":
        show_scene_header(
            "🌅 Scene 10: Open Horizon",
            "The storm breaks at last, opening onto wide, sunlit sea beyond the blockade.",
        )
        if not st.session_state.action_complete:
            if st.button("⛵ Break Into Open Sea"):
                st.session_state.escaped = True
                story = generate_story(
                    "Open Horizon",
                    "breaking out into open sea with Captain Seraph",
                    "You and the Ursa Major escape into open waters.",
                    "With Captain Seraph at the helm, the Ursa Major surges past the final barrier into open sea.",
                )
                set_result("success", story)
        else:
            show_result()
            if st.session_state.escaped:
                st.header("🏆 VICTORY — YOU ESCAPED INTO THE OPEN SEA!")
                st.balloons()
            if st.button("🔄 Play Again"):
                restart_game()