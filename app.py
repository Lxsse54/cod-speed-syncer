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
    "Control": {5: 10.0}
}
MAX_TALENT_POINTS = 49
INNATE_SPEED_BONUS = 6.0

# Big Talents (Keystone) - Main Hero Only
BIG_TALENT_EFFECTS = {
    "Balanced Heart": 5.0,
    "Mighty Power": 0.0,
    "Shield of Stability": -2.0,
    "Backstabber": 0.0
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
    }
]

MarchSetup = namedtuple('MarchSetup', ['main', 'deputy', 'total_speed', 'talent_config', 'synergy_match', 'skill_breakdown'])

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

def get_skill_speed(hero_name, level, is_main):
    hero = next(h for h in HERO_DATABASE if h["Name"] == hero_name)
    
    if hero.get("Special_Rule") == "Main_Only" and not is_main:
        return 0.0
        
    s_list = hero.get("Skill_Speeds", [0]*5)
    if level < 1: 
        return 0.0
    
    idx = max(0, min(level - 1, 4))
    return s_list[idx]

def solve_for_march(main, deputy, user_skill_inputs_levels, target_speed=50.0, use_neya_artifact=False):
    m_data = next(h for h in HERO_DATABASE if h["Name"] == main)
    # d_data = next(h for h in HERO_DATABASE if h["Name"] == deputy) 
    
    m_lvl = user_skill_inputs_levels.get(main, 1)
    d_lvl = user_skill_inputs_levels.get(deputy, 1)
    
    # 1. Skills
    m_skill = get_skill_speed(main, m_lvl, is_main=True)
    d_skill = get_skill_speed(deputy, d_lvl, is_main=False)
    
    # 2. Big Talent (Main Only)
    big_talent_name = m_data.get("Big_Talent", "Mighty Power") 
    big_talent_val = BIG_TALENT_EFFECTS.get(big_talent_name, 0.0)
    
    # 3. Artifacts
    artifact_bonus = 0.0
    if use_neya_artifact and ("Neya" in [main, deputy]):
        artifact_bonus = 40.0
    
    fixed_speed = m_skill + d_skill + big_talent_val + artifact_bonus
    
    # 4. Optimized Tree Search
    gap = target_speed - fixed_speed
    possible_talents = get_achievable_talent_speeds(main)
    
    if not possible_talents:
        best_speed, tal_desc = 0.0, "Err"
    else:
        # Find closest
        best_speed = min(possible_talents.keys(), key=lambda x: abs(x - gap))
        tal_desc, _ = possible_talents[best_speed]
    
    final_speed = fixed_speed + best_speed
    
    d_type = next(h["Type"] for h in HERO_DATABASE if h["Name"] == deputy)
    is_synergy = (m_data["Type"] == d_type)
    
    skill_breakdown = f"Main({m_skill}) + Dep({d_skill}) + {big_talent_name}({big_talent_val})"
    if artifact_bonus > 0:
        skill_breakdown += f" + Lunaris({artifact_bonus})"
    
    return MarchSetup(
        main=main,
        deputy=deputy,
        total_speed=final_speed,
        talent_config=tal_desc,
        synergy_match=is_synergy,
        skill_breakdown=skill_breakdown
    )

def all_pairs_generator(items):
    if len(items) < 2:
        yield []
        return

    first = items[0]
    rest = items[1:]
    
    for i, partner in enumerate(rest):
        pair = (first, partner)
        remaining = rest[:i] + rest[i+1:]
        
        for solution in all_pairs_generator(remaining):
            yield [pair] + solution
            
        pair_flipped = (partner, first)
        for solution in all_pairs_generator(remaining):
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
selected_names = st.sidebar.multiselect("Select Heroes", all_names, default=all_names[:6])

# Artifact Config
has_neya_artifact = False
if "Neya" in selected_names:
    has_neya_artifact = st.sidebar.checkbox("Lunaris Artifact (+40%)", value=False)

user_skill_levels = {}
if selected_names:
    st.sidebar.markdown("---") 
    st.sidebar.subheader("Hero Skill Levels")
    cols = st.sidebar.columns(2)
    for i, name in enumerate(selected_names):
        with cols[i % 2]:
            user_skill_levels[name] = st.number_input(f"{name}", 0, 5, 5, key=f"lvl_{name}")

# --- Force Pairings ---
forced_pairs = []
with st.expander("Force Pairings"):
    st.caption("Select heroes you definitely want paired together.")
    
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
    
    # Collect valid inputs
    raw_inputs = [(p1_main, p1_dep), (p2_main, p2_dep), (p3_main, p3_dep)]
    for m, d in raw_inputs:
        if m != "None" and d != "None" and m != d:
            forced_pairs.append((m, d))

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
    
    # Check for duplicates across pins
    all_pinned_flat = [h for pair in forced_pairs for h in pair]
    if len(all_pinned_flat) != len(set(all_pinned_flat)):
        st.error("❌ Error: Duplicate heroes used in Forced Pairings!")
        return
        
    # Check if forced heroes are actually in the selection roster
    # (Selectbox logic usually ensures this, but good for safety)
    
    for m, d in forced_pairs:
        pinned_heroes.extend([m, d])
        # Pre-calc fixed march
        res = solve_for_march(m, d, user_skill_levels, TARGET_SPEED, has_neya_artifact)
        fixed_results.append(res)
        
    remaining_roster = [h for h in selected_names if h not in pinned_heroes]
    
    # Check if remainder is odd (one will be dropped)
    potential_rosters = []
    if len(remaining_roster) % 2 != 0:
        for i in range(len(remaining_roster)):
                potential_rosters.append(remaining_roster[:i] + remaining_roster[i+1:])
    else:
        potential_rosters = [remaining_roster]
        
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
        for pair_list in all_pairs_generator(list(roster)):
            current_results = list(fixed_results) # Start with pinned
            total_deviation = fixed_dev
            
            for main, deputy in pair_list:
                res = solve_for_march(main, deputy, user_skill_levels, TARGET_SPEED, has_neya_artifact)
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
    
    # De-duplicate? Sometimes logic produces identical march sets in different orders?
    # Our generator preserves order pairs, so distinct sets should be distinct.
    
    st.session_state.optimization_results = all_valid_results[:20]
    st.session_state.result_index = 0

# --- Main Action ---

if len(selected_names) < 2:
    st.info("Select 2+ heroes.")
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
            with st.expander(f"March {i}: {match.main} + {match.deputy}  ({match.total_speed:.1f}%)", expanded=True):
                ic1, ic2 = st.columns(2)
                ic1.markdown(f"**Main:** {match.main}")
                ic1.markdown(f"**Deputy:** {match.deputy}")
                ic1.markdown(f"**Talents:** {match.talent_config}")
                
                ic2.caption("Calculation:")
                ic2.info(match.skill_breakdown)
                diff = match.total_speed - TARGET_SPEED
                ic2.metric(f"Diff from Target", f"{diff:+.1f}%")

    elif len(selected_names) >= 2:
        st.info("Click 'Optimize' to start.")
