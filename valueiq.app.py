import streamlit as st
import pandas as pd
from fpdf import FPDF

# -------------------------------------------------------------
# 1. PAGE SETUP & HEADER
# -------------------------------------------------------------
st.set_page_config(page_title="ValueIQ | Enterprise Business Case", layout="wide")

st.title("📊 ValueIQ | Enterprise ROI & Business Case Calculator")
st.write(
    "Quantify business impact, risk-adjusted value realization, and payback timelines "
    "for enterprise AI deployment."
)

st.divider()

# -------------------------------------------------------------
# SIDEBAR CONTROLS & PRESETS
# -------------------------------------------------------------
st.sidebar.header("🎯 Deal Benchmarks & Presets")
preset = st.sidebar.selectbox(
    "Select Target Profile",
    ["Custom", "Mid-Market Sales Ops (20 Team Members)", "Enterprise Support (75 Team Members)"]
)

if preset == "Mid-Market Sales Ops (20 Team Members)":
    default_team, default_rate, default_hours, default_gain = 20, 65, 10, 30
elif preset == "Enterprise Support (75 Team Members)":
    default_team, default_rate, default_hours, default_gain = 75, 45, 15, 35
else:
    default_team, default_rate, default_hours, default_gain = 20, 65, 10, 30

st.sidebar.divider()
st.sidebar.header("⚙️ Advanced Risk Controls")
adoption_realization = st.sidebar.slider(
    "Realization / Risk Adjustment (%)",
    min_value=50, max_value=100, value=80,
    help="Adjusts expected savings down to account for ramp time and enterprise adoption rates."
)

time_horizon = st.sidebar.radio("Contract Horizon", ["1-Year Horizon", "3-Year Horizon"])
multiplier = 3 if time_horizon == "3-Year Horizon" else 1

# -------------------------------------------------------------
# 2. INPUT PARAMETERS
# -------------------------------------------------------------
st.subheader("Step 1: Financial & Organizational Inputs")

col1, col2, col3 = st.columns(3)

with col1:
    team_size = st.slider("Team Size (FTEs)", 5, 150, default_team, help="Total employees affected.")
    hourly_rate = st.number_input("Blended Hourly Rate ($)", value=default_rate, help="Salary + benefits cost per hour.")

with col2:
    manual_hours = st.slider("Manual Hours/Week", 2, 20, default_hours, help="Hours spent on repeatable tasks.")
    efficiency_gain = st.slider("Target Efficiency Gain (%)", 10, 50, default_gain, help="Estimated workflow reduction.")

with col3:
    annual_software_cost = st.number_input("Annual Software License ($)", value=team_size * 1200)
    one_time_services = st.number_input("One-Time Onboarding / Services ($)", value=5000, help="Initial deployment cost.")

# -------------------------------------------------------------
# 3. VALUE CALCULATION ENGINE
# -------------------------------------------------------------
# Gross potential savings
gross_annual_hours = team_size * (manual_hours * (efficiency_gain / 100)) * 52 * multiplier
gross_savings = gross_annual_hours * hourly_rate

# Risk-adjusted savings
realized_savings = gross_savings * (adoption_realization / 100)
realized_hours = gross_annual_hours * (adoption_realization / 100)

# Total Cost of Ownership (TCO)
total_tco = (annual_software_cost * multiplier) + one_time_services

# Net Financial Impact & ROI
net_savings = realized_savings - total_tco
roi_percentage = (net_savings / total_tco) * 100 if total_tco > 0 else 0

# Calculate Payback Period (Break-Even Month)
payback_month = "No Payback"
cumulative_tracker = -one_time_services
monthly_net = (realized_savings / (12 * multiplier)) - (annual_software_cost / (12 * multiplier))

if monthly_net > 0:
    for m in range(1, (12 * multiplier) + 1):
        cumulative_tracker += monthly_net
        if cumulative_tracker >= 0:
            payback_month = f"Month {m}"
            break

# ------------------------------------------------------------------------------
# SCENARIO COMPARISON CALCULATIONS
# ------------------------------------------------------------------------------
scenarios = {
    "Conservative": 0.50,
    "Target": adoption_realization / 100.0,
    "Aggressive": 0.90
}

scenario_results = {}

for name, factor in scenarios.items():
    # Recaptured hours over the contract horizon (1-Year or 3-Year)
    s_recaptured = (team_size * manual_hours * 52 * multiplier * (efficiency_gain / 100.0)) * factor
    s_savings = (s_recaptured * hourly_rate) - total_tco
    s_roi = (s_savings / total_tco * 100) if total_tco > 0 else 0
    
    # Exact monthly net benefit calculation
    s_monthly_savings = (s_recaptured * hourly_rate) / (12 * multiplier)
    s_monthly_cost = (annual_software_cost * multiplier) / (12 * multiplier)
    monthly_net_benefit = s_monthly_savings - s_monthly_cost
    
    if monthly_net_benefit > 0:
        if one_time_services > 0:
            s_payback = max(1, int((one_time_services / monthly_net_benefit) + 0.99))
        else:
            s_payback = 1
        s_payback_str = f"Month {s_payback}" if s_payback <= (12 * multiplier) else "Out of Range"
    else:
        s_payback_str = "Out of Range"
        
    scenario_results[name] = {
        "Adoption Rate": f"{int(factor * 100)}%",
        "Recaptured Hours": f"{s_recaptured:,.0f} hrs",
        "Net Savings": f"${s_savings:,.2f}",
        "ROI": f"{s_roi:.0f}%",
        "Payback Period": s_payback_str
    }

# ------------------------------------------------------------------------------
# 4. EXECUTIVE METRICS & SCENARIO DISPLAY
# ------------------------------------------------------------------------------
st.divider()
st.subheader(f"Step 2: Value Realization & Scenario Analysis ({time_horizon})")

tab1, tab2 = st.tabs(["🎯 Target Profile Overview", "📊 Multi-Scenario Comparison"])

with tab1:
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Net Cost Savings", f"${net_savings:,.2f}")
    m2.metric("Projected ROI", f"{roi_percentage:.0f}%")
    m3.metric("Recaptured Hours", f"{realized_hours:,.0f} hrs")
    m4.metric("Realization Confidence", f"{adoption_realization}%")
    m5.metric("Payback Period", payback_month)

with tab2:
    st.markdown("**Executive Risk-Sensitivity Analysis**")
    df_scenarios = pd.DataFrame(scenario_results).T
    st.dataframe(df_scenarios, use_container_width=True)
    st.caption("💡 *Comparing a 50% conservative baseline, your target configuration, and a 90% high-adoption rollout.*")

# -------------------------------------------------------------
# 5. VISUALIZATION: CUMULATIVE VALUE REALIZATION
# -------------------------------------------------------------
st.divider()
st.subheader("Step 3: Cumulative Financial Impact Over Time")

months = list(range(1, (12 * multiplier) + 1))
monthly_cost = annual_software_cost / (12 * multiplier)
monthly_savings = realized_savings / (12 * multiplier)

cumulative_data = []
current_net = -one_time_services

for m in months:
    current_net += (monthly_savings - monthly_cost)
    cumulative_data.append({
        "Month": m, 
        "Net Value Realization ($)": round(current_net, 2)
    })

df_chart = pd.DataFrame(cumulative_data)

st.bar_chart(
    df_chart,
    x="Month",
    y="Net Value Realization ($)",
    x_label="Time Period (Month)",
    y_label="Cumulative Net Value ($)"
)

# -------------------------------------------------------------
# PDF GENERATION HELPER FUNCTION
# -------------------------------------------------------------
def generate_pdf_report(time_horizon, team_size, hourly_rate, adoption_realization,
                        realized_hours, total_tco, one_time_services, net_savings,
                        roi_percentage, payback_month, scenario_results):
    pdf = FPDF()
    pdf.add_page()

    metrics = [
        ("Organizational Scope:", f"{team_size} FTEs @ ${hourly_rate}/hr blended cost"),
        ("Adoption & Risk Realization:", f"{adoption_realization}% confidence factor"),
        ("Capacity Recaptured:", f"{realized_hours:,.0f} hours"),
        ("Total Cost of Ownership (TCO):", f"${total_tco:,.2f} (Includes ${one_time_services:,.2f} services)"),
        ("Net Financial Savings:", f"${net_savings:,.2f}"),
        ("Projected Return on Investment (ROI):", f"{roi_percentage:.0f}%"),
        ("Payback Period:", f"Breakeven reached in {payback_month}"),
    ]

    for label, val in metrics:
        pdf.set_font("Helvetica", style="B", size=10)
        pdf.cell(70, 7, label, border=0)
        pdf.set_font("Helvetica", size=10)
        pdf.cell(0, 7, val, border=0, ln=True)

    pdf.ln(10)

    # Narrative Summary Section
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.cell(0, 8, "Executive Narrative", ln=True)
    pdf.set_font("Helvetica", size=10)

    narrative = (
        f"By deploying our AI solution across your {team_size}-person team operating at a "
        f"blended rate of ${hourly_rate}/hr, "
        f"your organization stands to recapture approximately {realized_hours:,.0f} hours of "
        f"operational labor capacity.\n\n"
        f"Accounting for a conservative enterprise adoption and realization rate of "
        f"{adoption_realization}%, the net bottom-line "
        f"savings total ${net_savings:,.2f} after fully factoring in software licensing and "
        f"${one_time_services:,.2f} in deployment overhead. "
        f"This represents an estimated {roi_percentage:.0f}% Return on Investment "
        f"({time_horizon})."
    )
    pdf.multi_cell(0, 6, narrative)

    # Dynamic Scenario Table in PDF
    pdf.ln(5)
    pdf.set_font("Helvetica", style="B", size=11)
    pdf.cell(0, 8, "Risk Sensitivity Scenarios", ln=True)
    
    pdf.set_font("Helvetica", style="B", size=9)
    pdf.cell(35, 6, "Scenario", border=1)
    pdf.cell(30, 6, "Adoption", border=1)
    pdf.cell(45, 6, "Net Savings", border=1)
    pdf.cell(30, 6, "ROI", border=1)
    pdf.cell(35, 6, "Payback", border=1, ln=True)
    
    pdf.set_font("Helvetica", size=9)
    for name, data in scenario_results.items():
        pdf.cell(35, 6, name, border=1)
        pdf.cell(30, 6, data["Adoption Rate"], border=1)
        pdf.cell(45, 6, data["Net Savings"], border=1)
        pdf.cell(30, 6, data["ROI"], border=1)
        pdf.cell(35, 6, data["Payback Period"], border=1, ln=True)

    return bytes(pdf.output())

# ------------------------------------------------------------------------------
# 6. EXECUTIVE SUMMARY & EXPORT
# ------------------------------------------------------------------------------
st.divider()
st.subheader("Step 4: Executive Board Brief")

summary_text = (
    f"Executive Value Realization Brief ({time_horizon}):\n"
    f"• Organizational Scope: {team_size} FTEs operating at a blended cost of ${hourly_rate}/hr.\n"
    f"• Risk-Adjusted Efficiency: Assuming a conservative {adoption_realization}% adoption confidence, "
    f"the organization will recapture {realized_hours:,.0f} hours of labor capacity.\n"
    f"• Total Cost of Ownership (TCO): ${total_tco:,.2f} (Includes software licenses and ${one_time_services:,.2f} in deployment services).\n"
    f"• Net Bottom-Line Impact: ${net_savings:,.2f} net financial savings yielding a {roi_percentage:.0f}% ROI.\n"
    f"• Payback Timeline: Breakeven reached in {payback_month}."
)

st.info(summary_text)

# Generate PDF bytes with scenario_results included
pdf_bytes = generate_pdf_report(
    time_horizon, team_size, hourly_rate, adoption_realization,
    realized_hours, total_tco, one_time_services, net_savings,
    roi_percentage, payback_month, scenario_results
)

# Streamlit Download Button for PDF
st.download_button(
    label="📄 Export Executive Brief (.pdf)",
    data=pdf_bytes,
    file_name=f"ValueIQ_Executive_Brief_{team_size}_FTEs.pdf",
    mime="application/pdf"
)