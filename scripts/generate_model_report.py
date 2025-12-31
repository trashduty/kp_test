# /// script
# dependencies = [
#   "pandas",
#   "pytz"
# ]
# ///
\"\"\"
Generate model record reports from graded bet results.

This script reads graded_results.csv from the cbb repository and generates:
1. model_record.csv - Full season running record by edge tier
2. docs/model_record.md - Markdown report for GitHub Pages

Edge tiers: 0-1.9%, 2-3.9%, 4-5.9%, 6%+
Consensus filtering is applied to duplicate sections for each bet type.
\"\"\"

import pandas as pd
import os
import sys
from datetime import datetime
import pytz

# Project paths
script_dir = os.path.dirname(os.path.abspath(__file__))
# Assuming script is in kp_test/scripts/, project_root is kp_test/
project_root = os.path.dirname(script_dir)

# Path to cbb repository (assumed sibling to kp_test)
cbb_root = os.path.abspath(os.path.join(project_root, '..', 'cbb'))
graded_results_path = os.path.join(cbb_root, 'graded_results.csv')

# Paths within kp_test
model_record_csv_path = os.path.join(project_root, 'model_record.csv')
docs_dir = os.path.join(project_root, 'docs')
model_record_md_path = os.path.join(docs_dir, 'model_record.md')

# Edge tier definitions (in decimal, e.g., 0.02 = 2%)
EDGE_TIERS = [
    {'name': '0-1.9%', 'min': 0.00, 'max': 0.02},
    {'name': '2-3.9%', 'min': 0.02, 'max': 0.04},
    {'name': '4-5.9%', 'min': 0.04, 'max': 0.06},
    {'name': '6%+', 'min': 0.06, 'max': float('inf')},
]


def load_graded_results():
    \"\"\"Load graded results from CSV.\"\"\"
    if not os.path.exists(graded_results_path):
        print(f\"Error: {graded_results_path} not found\")
        # Fallback to local graded_results if available for testing
        local_fallback = os.path.join(project_root, 'graded_results.csv')
        if os.path.exists(local_fallback):
            print(f\"Using local fallback: {local_fallback}\")
            return pd.read_csv(local_fallback)
        return None

    try:
        df = pd.read_csv(graded_results_path)
        print(f\"Loaded {len(df)} graded results from {graded_results_path}\")
        return df
    except Exception as e:
        print(f\"Error loading graded results: {e}\")
        return None


def calculate_record(df, edge_col, outcome_col, bet_type, consensus_flag_col=None):
    \"\"\"
    Calculate win/loss record by edge tier.
    \"\"\"
    records = []
    
    # Filter for consensus if specified
    if consensus_flag_col and consensus_flag_col in df.columns:
        tier_df_base = df[df[consensus_flag_col] == 1].copy()
    else:
        tier_df_base = df.copy()

    for tier in EDGE_TIERS:
        # Filter to this tier
        tier_mask = (
            (tier_df_base[edge_col] >= tier['min']) &
            (tier_df_base[edge_col] < tier['max']) &
            (tier_df_base[outcome_col].notna())
        )
        tier_df = tier_df_base[tier_mask]

        if len(tier_df) == 0:
            records.append({
                'bet_type': bet_type,
                'edge_tier': tier['name'],
                'wins': 0,
                'losses': 0,
                'total': 0,
                'win_rate': None,
                'profit_units': 0
            })
            continue

        wins = (tier_df[outcome_col] == 1).sum()
        losses = (tier_df[outcome_col] == 0).sum()
        total = wins + losses
        win_rate = wins / total if total > 0 else None

        # Calculate profit assuming -110 standard juice
        profit_units = (wins * 0.909) - losses

        records.append({
            'bet_type': bet_type,
            'edge_tier': tier['name'],
            'wins': wins,
            'losses': losses,
            'total': total,
            'win_rate': win_rate,
            'profit_units': round(profit_units, 2)
        })

    return records


def generate_model_record(df):
    \"\"\"Generate model record for all bet types by edge tier, including consensus.\"\"\"
    all_records = []

    # Opening edge columns
    spread_edge_col = 'opening_spread_edge'
    ml_edge_col = 'opening_moneyline_edge'
    over_edge_col = 'opening_over_edge'
    under_edge_col = 'opening_under_edge'

    # Fallback if opening versions don't exist
    if spread_edge_col not in df.columns: spread_edge_col = 'spread_edge'
    if ml_edge_col not in df.columns: ml_edge_col = 'moneyline_edge'
    if over_edge_col not in df.columns: over_edge_col = 'over_edge'
    if under_edge_col not in df.columns: under_edge_col = 'under_edge'

    # Bet configurations: (bet_name, outcome_col, edge_col, consensus_col)
    bet_configs = [
        ('Spread', 'spread_covered', spread_edge_col, 'spread_consensus_flag'),
        ('Moneyline', 'moneyline_won', ml_edge_col, 'moneyline_consensus_flag'),
        ('Over', 'over_hit', over_edge_col, 'over_consensus_flag'),
        ('Under', 'under_hit', under_edge_col, 'under_consensus_flag')
    ]

    for bet_type, outcome_col, edge_col, consensus_col in bet_configs:
        # All bets for this type
        all_records.extend(calculate_record(df, edge_col, outcome_col, bet_type))
        # Consensus only for this type
        all_records.extend(calculate_record(df, edge_col, outcome_col, f\"{bet_type} (Consensus)\", consensus_col))

    return pd.DataFrame(all_records)


def render_table(type_df):
    \"\"\"Helper to render a record table in markdown.\"\"\"
    if len(type_df) == 0: return \"No data available.\\n\\n\"
    md = \"| Edge Tier | Record | Win Rate | Profit (Units) |\\n|-----------|--------|----------|----------------|\\n\"
    total_wins = total_losses = total_profit = 0
    for _, row in type_df.iterrows():
        wins, losses, profit = int(row['wins']), int(row['losses']), row['profit_units']
        win_rate = f\"{row['win_rate']*100:.1f}%\" if pd.notna(row['win_rate']) else \"N/A\"
        profit_str = f\"+{profit:.2f}\" if profit >= 0 else f\"{profit:.2f}\"
        total_wins += wins; total_losses += losses; total_profit += profit
        md += f\"| {row['edge_tier']} | {wins}-{losses} | {win_rate} | {profit_str} |\\n\"
    total_games = total_wins + total_losses
    total_win_rate = f\"{total_wins/total_games*100:.1f}%\" if total_games > 0 else \"N/A\"
    total_profit_str = f\"+{total_profit:.2f}\" if total_profit >= 0 else f\"{total_profit:.2f}\"
    md += f\"| **Total** | **{total_wins}-{total_losses}** | **{total_win_rate}** | **{total_profit_str}** |\\n\\n\"
    return md


def generate_markdown_report(record_df, graded_df):
    \"\"\"Generate markdown report with duplicated sections for consensus.\"\"\"
    et = pytz.timezone('US/Eastern')
    now_et = datetime.now(et)

    if len(graded_df) > 0:
        min_date = graded_df['date'].min()
        max_date = graded_df['date'].max()
        date_range = f\"{min_date} to {max_date}\"
    else:
        date_range = \"No data\"

    md = f\"\"\"# CBB Model Record (Consensus Enhanced)

**Last Updated:** {now_et.strftime('%B %d, %Y at %I:%M %p ET')}

**Season Record Period:** {date_range}

---

\"\"\"

    for bet_type in ['Spread', 'Moneyline', 'Over', 'Under']:
        md += f\"## {bet_type} Bets\\n\\n\"
        md += f\"### All {bet_type} Bets\\n\\n\"
        md += render_table(record_df[record_df['bet_type'] == bet_type])
        md += f\"### {bet_type} Bets (Consensus Only)\\n\\n\"
        md += render_table(record_df[record_df['bet_type'] == f\"{bet_type} (Consensus)\"])
        md += \"---\\n\\n\"

    md += \"## Methodology Notes\\n- Assumes flat betting at -110 juice.\\n\"
    return md


def main():
    df = load_graded_results()
    if df is None: sys.exit(0)
    record_df = generate_model_record(df)
    record_df.to_csv(model_record_csv_path, index=False)
    os.makedirs(docs_dir, exist_ok=True)
    md_content = generate_markdown_report(record_df, df)
    with open(model_record_md_path, 'w') as f: f.write(md_content)

if __name__ == \"__main__\":
    main()
