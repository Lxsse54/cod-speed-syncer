import streamlit as st
import pandas as pd
import itertools
import statistics
from collections import namedtuple

# ==========================================
# 1. Configuration & Constants
# ==========================================

# Talent Tree Definitions
TALENT_TREES_DEF = {
    "Cavalry": {5: 15.0},
    "Pvp": {10: 10.0, 21: 20.0},
    "Tank": {10: 10.0, 21: 20.0},
    "Mobility": {5: 10.0, 15: 20.0, 26: 25.0},
    "Overall": {10: 10.0},
    "Peacekeeping": {10: 10.0},
    "Control": {5: 10.0},
    "Support": {},
    "Skills": {}
}
MAX_TALENT_POINTS = 49
INNATE_SPEED_BONUS = 6.0

# Big Talents (Keystone) - Main Hero Only
BIG_TALENT_EFFECTS = {
    "Balanced Heart": 5.0,
    "Mighty Power": 0.0,
    "Shield of Stability": -2.0,
    "Backstabber": 0.0,
    "Transforming Spirit": 0.0
}

HERO_DATABASE = [
    {
        "Name": "Neya",
        "Type": "Cavalry",
        "Trees": ["Cavalry", "Pvp", "Mobility"],
        "Skill_Speeds": [4.0, 5.0, 6.0, 8.0, 10.0],
        "Big_Talent": "Balanced Heart"
    },
    {
        "Name": "Lieh-Shan Yen",
        "Type": "Cavalry",
        "Trees": ["Cavalry"],
        "Skill_Speeds": [0.0] * 5,
        "Big_Talent": "Mighty Power"
    },
    {
        "Name": "Urag",
        "Type": "Cavalry",
        "Trees": ["Cavalry", "Pvp"],
        "Skill_Speeds": [4.0, 5.0, 6.0, 8.0, 10.0],
        "Big_Talent": "Mighty Power"
    },
    {
        "Name": "Emrys",
        "Type": "Cavalry",
        "Trees": ["Cavalry", "Pvp", "Mobility"],
        "Skill_Speeds": [3.0, 4.5, 6.0, 8.0, 10.0],
        "Big_Talent": "Balanced Heart"
    },
    {
        "Name": "Forondil",
        "Type": "Cavalry",
        "Trees": ["Cavalry", "Pvp", "Control"],
        "Skill_Speeds": [10.0, 12.0, 14.0, 16.0, 20.0],
        "Special_Rule": "Main_Only",
        "Big_Talent": "Balanced Heart"
    },
    {
        "Name": "Tobin",
        "Type": "Cavalry",
        "Trees": ["Cavalry", "Tank"],
        "Skill_Speeds": [0.0] * 5,
        "Big_Talent": "Shield of Stability"
    },
    {
        "Name": "Bakshi",
        "Type": "Cavalry",
        "Trees": ["Cavalry", "Peacekeeping"],
        "Skill_Speeds": [0.0] * 5,
        "Big_Talent": "Mighty Power"
    },
    {
        "Name": "Theodore",
        "Type": "Cavalry",
        "Trees": ["Cavalry"],
        "Skill_Speeds": [4.0, 5.0, 6.0, 8.0, 10.0],
        "Big_Talent": "Mighty Power"
    },
    {
        "Name": "Mardok",
        "Type": "Cavalry",
        "Trees": ["Cavalry", "Pvp", "Mobility"],
        "Skill_Speeds": [4.0, 5.0, 6.0, 8.0, 10.0],
        "Big_Talent": "Balanced Heart"
    },
    {
        "Name": "Freya",
        "Type": "Cavalry",
        "Trees": ["Cavalry", "Control"],
        "Skill_Speeds": [0.0] * 5,
        "Big_Talent": "Backstabber"
    },
    {
        "Name": "Agnar",
        "Type": "Cavalry",
        "Trees": ["Cavalry", "Pvp"],
        "Skill_Speeds": [0.0] * 5,
        "Big_Talent": "Mighty Power"
    },
    {
        "Name": "Mu Hsiang",
        "Type": "Cavalry",
        "Trees": ["Overall", "Pvp", "Support"],
        "Skill_Speeds": [0.0] * 5,
        "Big_Talent": "Transforming Spirit"
    },
    {
        "Name": "Theia",
        "Type": "Cavalry", # Conditional Flying
        "Trees": ["Overall", "Pvp", "Support"],
        "Skill_Speeds": [0.0] * 5, # Special rule handling needed
        "Big_Talent": "Transforming Spirit", # Guessing? User didn't specify. Assuming neutral like others or user can correct.
        # Wait, user didn't specify big talent for Theia/Seluna. I'll default to "Mighty Power" (0) or similar to be safe.
        # Actually user said "Mu Hsiang has a new big talent...". 
        # I will assume "Mighty Power" (0 impact) for Theia/Seluna unless told otherwise.
        "Special_Rule": "Theia_Flying" 
    },
    {
        "Name": "Seluna",
        "Type": "Cavalry",
        "Trees": ["Overall", "Pvp", "Skills"],
        "Skill_Speeds": [8.0, 10.0, 12.0, 16.0, 20.0],
        "Big_Talent": "Mighty Power" # Default
    },
    {
        "Name": "Falgrim",
        "Type": "Cavalry",
        "Trees": ["Pvp"],
        "Skill_Speeds": [4.0, 5.0, 6.0, 8.0, 10.0],
        "Big_Talent": "Mighty Power" # Default
    },
    {
        "Name": "Alistair",
        "Type": "Cavalry",
        "Trees": ["Cavalry", "Tank"],
        "Skill_Speeds": [0.0] * 5,
        "Big_Talent": "Mighty Power" # Default
    }
]

# Synergy Definitions (Bidirectional or Directional)
# Format: "HeroName": {"PartnerName": "Type"}
# Types: "Synergy" (Green), "Anti-Synergy" (Red)
HERO_SYNERGIES = {
    # Placeholders - User to provide
}

MarchSetup = namedtuple('MarchSetup', ['main', 'deputy', 'total_speed', 'talent_config', 'synergy_match', 'skill_breakdown', 'specific_synergy'])

# ==========================================
# 2. Logic
# ==========================================

@st.cache_data
def get_achievable_talent_speeds(hero_name):
    hero = next((h for h in HERO_DATABASE if h["Name"] == hero_name), None)
    if not hero:
        return {}
    
    available_branches = []
    
    for tree_name in hero["Trees"]:
        if tree_name in TALENT_TREES_DEF:
            branch_options = [(0, 0.0, "None")] 
            
            milestones = TALENT_TREES_DEF[tree_name]
            for cost, speed in milestones.items():
                branch_options.append((cost, speed, f"{tree_name}({int(speed)}%)"))
            
            available_branches.append(branch_options)
            
    valid_configs = {}
    
    for combination in itertools.product(*available_branches):
        total_cost = sum(c[0] for c in combination)
        total_speed_talents = sum(c[1] for c in combination)
        description_parts = [c[2] for c in combination if c[2] != "None"]
        
        if total_cost <= MAX_TALENT_POINTS:
            desc_a = ", ".join(description_parts) if description_parts else "No Talents"
            if total_speed_talents not in valid_configs or valid_configs[total_speed_talents][1] > total_cost:
                valid_configs[total_speed_talents] = (desc_a, total_cost)
            
            speed_b = total_speed_talents + INNATE_SPEED_BONUS
            desc_b = (desc_a + " + Innate(6%)") if desc_a != "No Talents" else "Innate(6%)"
            if speed_b not in valid_configs or valid_configs[speed_b][1] > total_cost:
                valid_configs[speed_b] = (desc_b, total_cost)
                
    return valid_configs

def get_skill_speed(hero_name, level, is_main, is_theia_flying=False):
    if hero_name.startswith("Generic"):
        return 0.0
        
    hero = next(h for h in HERO_DATABASE if h["Name"] == hero_name)
    
    if hero.get("Special_Rule") == "Main_Only" and not is_main:
        return 0.0
        
    if hero.get("Special_Rule") == "Theia_Flying":
        if is_theia_flying:
            # Special array for Theia Flying
            s_list = [10.0, 12.0, 14.0, 16.0, 20.0]
            # Use logic below to pick level
        else:
            return 0.0
    else:
        s_list = hero.get("Skill_Speeds", [0]*5)
        
    if level < 1: 
        return 0.0
    
    idx = max(0, min(level - 1, 4))
    return s_list[idx]

def solve_for_march(main, deputy, user_skill_inputs_levels, target_speed=50.0, neya_artifact_bonus=0.0, is_theia_flying=False):
    if main.startswith("Generic"):
        m_data = {"Name": main, "Type": "Cavalry", "Big_Talent": "None"} # Dummy
    else:
        m_data = next(h for h in HERO_DATABASE if h["Name"] == main)
    
    # Deputy data fetch not strictly needed for speed calc, but needed for type check if we wanted detailed synergy
    d_type = "Cavalry"
    if not deputy.startswith("Generic"):
        d_type = next(h["Type"] for h in HERO_DATABASE if h["Name"] == deputy)

    m_lvl = user_skill_inputs_levels.get(main, 1)
    d_lvl = user_skill_inputs_levels.get(deputy, 1)
    
    # 1. Skills
    m_skill = get_skill_speed(main, m_lvl, is_main=True, is_theia_flying=is_theia_flying)
    d_skill = get_skill_speed(deputy, d_lvl, is_main=False, is_theia_flying=is_theia_flying)
    
    # 2. Big Talent (Main Only)
    big_talent_name = m_data.get("Big_Talent", "Mighty Power") 
    big_talent_val = BIG_TALENT_EFFECTS.get(big_talent_name, 0.0)
    
    # 3. Artifacts
    artifact_bonus = 0.0
    if neya_artifact_bonus > 0 and ("Neya" in [main, deputy]):
        artifact_bonus = neya_artifact_bonus
    
    fixed_speed = m_skill + d_skill + big_talent_val + artifact_bonus
    
    # 4. Optimized Tree Search
    possible_talents = {}
    if not main.startswith("Generic"):
        gap = target_speed - fixed_speed
        possible_talents = get_achievable_talent_speeds(main)
    
    if not possible_talents:
        # Fallback if generic or error
        # Generics have 0 talents
        best_speed, tal_desc = 0.0, "None"
    else:
        # Find closest
        gap = target_speed - fixed_speed
        best_speed = min(possible_talents.keys(), key=lambda x: abs(x - gap))
        tal_desc, _ = possible_talents[best_speed]
    
    final_speed = fixed_speed + best_speed
    
    # Logic: Generic is assumed Cavalry for synergy purposes (or whatever user prefers)
    # User said "favor real heroes".
    # We will assume Generic matches type to avoid synergy penalty noise, since they are fillers.
    is_synergy = (m_data.get("Type", "Cavalry") == d_type)
    
    skill_breakdown = f"Main({m_skill}) + Dep({d_skill}) + {big_talent_name}({big_talent_val})"
    if artifact_bonus > 0:
        skill_breakdown += f" + Lunaris({artifact_bonus})"
        
    # Synergy Check
    syn_type = HERO_SYNERGIES.get(main, {}).get(deputy)
    if not syn_type:
        syn_type = HERO_SYNERGIES.get(deputy, {}).get(main) # Bidirectional check
    
    return MarchSetup(
        main=main,
        deputy=deputy,
        total_speed=final_speed,
        talent_config=tal_desc,
        synergy_match=is_synergy,
        skill_breakdown=skill_breakdown,
        specific_synergy=syn_type
    )

def all_pairs_generator(items, forced_mains=None):
    if forced_mains is None:
        forced_mains = set()

    if len(items) < 2:
        yield []
        return

    first = items[0]
    rest = items[1:]
    
    for i, partner in enumerate(rest):
        pair = (first, partner)
        remaining = rest[:i] + rest[i+1:]
        
        # Check: Is partner allowed to be deputy? (i.e. not in forced_mains)
        if partner not in forced_mains:
            for solution in all_pairs_generator(remaining, forced_mains):
                yield [pair] + solution
            
        # Check: Is first allowed to be deputy?
        if first not in forced_mains:
            pair_flipped = (partner, first)
            for solution in all_pairs_generator(remaining, forced_mains):
                yield [pair_flipped] + solution

# ==========================================
# 3. UI
# ==========================================

st.set_page_config(page_title="CoD Speed Syncer 3.1", layout="wide")
st.title("🐎 Speed Synchronizer")
st.markdown("Enter your heroes and goal speed on the left. Force pairings below if wanted.")

# --- Sidebar ---
st.sidebar.header("Settings")
TARGET_SPEED = st.sidebar.number_input("Target Speed (%)", min_value=10.0, max_value=100.0, value=50.0, step=1.0)

all_names = [h["Name"] for h in HERO_DATABASE]
select_all = st.sidebar.checkbox("Select All Heroes")
default_sel = all_names if select_all else []
selected_names = st.sidebar.multiselect("Select Heroes", all_names, default=default_sel, key=f"hero_sel_{select_all}")
num_fillers = st.sidebar.number_input("Add Generic Deputies / Temu Cav Deputies", min_value=0, max_value=10, value=0, help="Use these to fill empty slots in your marches. Can be archer heroes like Nico, or inf like Mogro")

# Artifact Config
neya_artifact_bonus = 0.0
if "Neya" in selected_names:
    use_lunaris = st.sidebar.checkbox("Lunaris Artifact", value=False, help="Lunaris only gives move speed when paired with Neya and might not be ideal because it only out of combat.")
    if use_lunaris:
        lunaris_level = st.sidebar.select_slider("Lunaris Level", options=[1, 2, 3, 4, 5], value=5)
        # Map level to speed: 1=20, 2=25, 3=30, 4=35, 5=40
        neya_artifact_bonus = 15.0 + (lunaris_level * 5.0)
    
is_theia_flying = False
if "Theia" in selected_names:
    is_theia_flying = st.sidebar.checkbox("Theia uses Flying Cavs (Eagles)?", value=False, help="Enable if Theia is leading a Flying unit.")

user_skill_levels = {}
if selected_names:
    st.sidebar.markdown("---") 
    st.sidebar.subheader("Hero March speed Skill Levels (ignore if hero doesn't have one)")
    cols = st.sidebar.columns(2)
    for i, name in enumerate(selected_names):
        with cols[i % 2]:
            user_skill_levels[name] = st.number_input(f"{name}", 0, 5, 5, key=f"lvl_{name}")

# --- Force Pairings ---
forced_pairs = []
forced_mains_only = set()

with st.expander("Force Pairings"):
    st.caption("Select heroes you definitely want paired together. If you select ONLY Main, that hero is forced to be Main (with any deputy).")
    
    # helper to filter choices? No, just show all selected to allow user flexibility, validate later
    # Slot 1
    c1, c2 = st.columns(2)
    p1_main = c1.selectbox("Pair 1 Main", ["None"] + selected_names, key="fp1m")
    p1_dep = c2.selectbox("Pair 1 Deputy", ["None"] + selected_names, key="fp1d")
    
    # Slot 2
    c3, c4 = st.columns(2)
    p2_main = c3.selectbox("Pair 2 Main", ["None"] + selected_names, key="fp2m")
    p2_dep = c4.selectbox("Pair 2 Deputy", ["None"] + selected_names, key="fp2d")
    
    # Slot 3
    c5, c6 = st.columns(2)
    p3_main = c5.selectbox("Pair 3 Main", ["None"] + selected_names, key="fp3m")
    p3_dep = c6.selectbox("Pair 3 Deputy", ["None"] + selected_names, key="fp3d")

    # Slot 4
    c7, c8 = st.columns(2)
    p4_main = c7.selectbox("Pair 4 Main", ["None"] + selected_names, key="fp4m")
    p4_dep = c8.selectbox("Pair 4 Deputy", ["None"] + selected_names, key="fp4d")

    # Slot 5
    c9, c10 = st.columns(2)
    p5_main = c9.selectbox("Pair 5 Main", ["None"] + selected_names, key="fp5m")
    p5_dep = c10.selectbox("Pair 5 Deputy", ["None"] + selected_names, key="fp5d")
    
    # Collect valid inputs
    raw_inputs = [
        (p1_main, p1_dep), (p2_main, p2_dep), (p3_main, p3_dep),
        (p4_main, p4_dep), (p5_main, p5_dep)
    ]
    for m, d in raw_inputs:
        if m != "None" and d != "None" and m != d:
            forced_pairs.append((m, d))
        elif m != "None" and d == "None":
            forced_mains_only.add(m)

# --- Initialize Session State ---
if 'optimization_results' not in st.session_state:
    st.session_state.optimization_results = []
if 'result_index' not in st.session_state:
    st.session_state.result_index = 0

# --- Helper Logic ---
def run_optimization():
    # 1. Validate Forced Pairs
    pinned_heroes = []
    fixed_results = []
    
    # Check for duplicates across pins and constraints
    all_pinned_flat = [h for pair in forced_pairs for h in pair]
    # Check intersection with forced_mains
    overlap = set(all_pinned_flat).intersection(forced_mains_only)
    
    if len(all_pinned_flat) != len(set(all_pinned_flat)) or overlap:
        st.error("❌ Error: Duplicate heroes used in Forced Pairings/Constraints!")
        return
        
    for m, d in forced_pairs:
        pinned_heroes.extend([m, d])
        res = solve_for_march(m, d, user_skill_levels, TARGET_SPEED, neya_artifact_bonus, is_theia_flying)
        fixed_results.append(res)
        
    remaining_roster = [h for h in selected_names if h not in pinned_heroes]
    
    # Add Generics to remaining roster
    for i in range(num_fillers):
        remaining_roster.append(f"Generic {i+1}")
        
    # Check if remainder is odd (one will be dropped)
    potential_rosters = []
    if len(remaining_roster) % 2 != 0:
        # Optimization: Priority drop Generics first.
        # If we have any generic, we create only 1 potential roster: the one where the last Generic is dropped.
        generics_in_roster = [h for h in remaining_roster if h.startswith("Generic")]
        
        if generics_in_roster:
            # Remove the last added generic
            # Find index of last generic
            bad_hero = generics_in_roster[-1]
            idx = remaining_roster.index(bad_hero)
            potential_rosters.append(remaining_roster[:idx] + remaining_roster[idx+1:])
        else:
            # No generics, standard round-robin drop
            for i in range(len(remaining_roster)):
                if remaining_roster[i] not in forced_mains_only:
                    potential_rosters.append(remaining_roster[:i] + remaining_roster[i+1:])
    else:
        potential_rosters = [remaining_roster]
        
    if not potential_rosters:
        st.error("❌ Error: Constraints impossible to satisfy (e.g. forced Odd number of Main-Only heroes).")
        return
        
    count_eval = 0
    MAX_CHECKS = 100000 
    
    # Store tuples of (deviation_score, result_set)
    all_valid_results = []
    
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    # Base deviation from fixed results
    fixed_dev = 0
    for res in fixed_results:
        dev = abs(res.total_speed - TARGET_SPEED)
        if dev > 1.5: fixed_dev += (dev * 10)
        else: fixed_dev += dev
    
    if not remaining_roster and fixed_results:
         # Edge case: All heroes are pinned, no optimization needed
         all_valid_results.append((fixed_dev, fixed_results))
    
    for roster in potential_rosters:
        for pair_list in all_pairs_generator(list(roster), forced_mains_only):
            current_results = list(fixed_results) # Start with pinned
            total_deviation = fixed_dev
            
            for main, deputy in pair_list:
                res = solve_for_march(main, deputy, user_skill_levels, TARGET_SPEED, neya_artifact_bonus, is_theia_flying)
                current_results.append(res)
                
                dev = abs(res.total_speed - TARGET_SPEED)
                if dev > 1.5: 
                        total_deviation += (dev * 10)
                else:
                    total_deviation += dev
            
            all_valid_results.append((total_deviation, current_results))
            
            # Pruning logic could go here
            
            count_eval += 1
            if count_eval % 2000 == 0:
                    if count_eval < MAX_CHECKS:
                        progress_bar.progress(count_eval / MAX_CHECKS)
                        status_text.text(f"Checked {count_eval} combos...")
            if count_eval > MAX_CHECKS: break
        if count_eval > MAX_CHECKS: break
        
    progress_bar.empty()
    status_text.empty()
    
    # Sort and keep top 20 unique-ish results
    # Sort by score ascending (lower deviation is better)
    all_valid_results.sort(key=lambda x: x[0])
    
    st.session_state.optimization_results = all_valid_results[:20]
    st.session_state.result_index = 0

# --- Main Action ---

total_heroes = len(selected_names) + num_fillers

if total_heroes > 10:
    st.warning("⚠️ You have selected more than 10 heroes. This will attempt to create more than 5 marches, which may produce non-ideal results.")

if total_heroes < 2:
    st.info("Select 2+ heroes (or add fillers).")
else:
    if st.button("Optimize", type="primary"):
        with st.spinner("Processing..."):
            run_optimization()

    # --- Display Logic ---
    if st.session_state.optimization_results:
        results = st.session_state.optimization_results
        idx = st.session_state.result_index
        
        # Ensure index is in bounds (if roster changed and results cleared, this block might be skipped, but safe check)
        if idx >= len(results):
            idx = 0
            st.session_state.result_index = 0
            
        score, best_set = results[idx]
        
        st.divider()
        st.header("Results")
        
        # -- Navigation Controls --
        col_prev, col_info, col_next = st.columns([1, 2, 1])
        
        with col_prev:
            if st.button("< Prev"):
                st.session_state.result_index = max(0, idx - 1)
                st.rerun()
                
        with col_next:
            if st.button("Next >"):
                st.session_state.result_index = min(len(results) - 1, idx + 1)
                st.rerun()
                
        with col_info:
            st.markdown(f"<div style='text-align: center'><b>Option {idx + 1} of {len(results)}</b><br>Score/Deviation: {score:.2f}</div>", unsafe_allow_html=True)
            
        # -- Metrics --
        speeds = [m.total_speed for m in best_set]
        avg = statistics.mean(speeds)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Average Speed", f"{avg:.2f}%")
        m2.metric("Variance", f"{max(speeds)-min(speeds):.2f}%")
        m3.metric("Target Error", f"{abs(avg-TARGET_SPEED):.2f}%")
        
        # -- Details --
        for i, match in enumerate(best_set, 1):
            # Format title with synergy indicator
            syn_icon = ""
            if match.specific_synergy == "Synergy": syn_icon = "✅ "
            elif match.specific_synergy == "Anti-Synergy": syn_icon = "❌ "
            
            with st.expander(f"March {i}: {syn_icon}{match.main} + {match.deputy}  ({match.total_speed:.1f}%)", expanded=True):
                ic1, ic2 = st.columns(2)
                ic1.markdown(f"**Main:** {match.main}")
                ic1.markdown(f"**Deputy:** {match.deputy}")
                if match.specific_synergy:
                    color = "green" if match.specific_synergy == "Synergy" else "red"
                    ic1.markdown(f"**Synergy:** :{color}[{match.specific_synergy}]")
                else:
                     ic1.caption("No Synergy")
                
                ic1.markdown(f"**Talents:** {match.talent_config}")
                
                ic2.caption("Calculation:")
                ic2.info(match.skill_breakdown)
                diff = match.total_speed - TARGET_SPEED
                ic2.metric(f"Diff from Target", f"{diff:+.1f}%")

    elif len(selected_names) >= 2:
        st.info("Click 'Optimize' to start.")
