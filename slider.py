import streamlit as st
import numpy as np
from scipy.special import expit

# Define optimal ranges with sensitivity and base impacts
OPTIMAL_RANGES = {
    't2': {
        'min': 195, 'max': 205, 'optimal': 200,
        'weight': 0.27,
        'sensitivity': 0.217985,
        'base_impact': 30
    },
    't3': {
        'min': 195, 'max': 205, 'optimal': 200,
        'weight': 0.25,
        'sensitivity': 0.136957,
        'base_impact': 25
    },
    't4': {
        'min': 195, 'max': 205, 'optimal': 200,
        'weight': 0.40,
        'sensitivity': 0.181967,
        'base_impact': 25
    },
    't1': {
        'min': 190, 'max': 200, 'optimal': 195,
        'weight': 0.10,
        'sensitivity': 0.069769,
        'base_impact': 10
    },
    't5': {
        'min': 190, 'max': 200, 'optimal': 195,
        'weight': 0.05,
        'sensitivity': 0.003058,
        'base_impact': 10
    },
    'lhsv': {
        'min': 0.5, 'max': 0.7, 'optimal': 0.6,
        'weight': 0.05,
        'sensitivity': 0.016678,
        'base_impact': 5
    },
    'h2gly_ratio': {
        'min': 6, 'max': 7, 'optimal': 6.5,
        'weight': 0.05,
        'sensitivity': 0.004925,
        'base_impact': 5
    },
    'liquid_feed': {
        'min': 50, 'max': 150, 'optimal': 100,
        'weight': 0.05,
        'sensitivity': 0.000073,
        'base_impact': 5
    },
    'hydrogen_flow': {
        'min': 300, 'max': 600, 'optimal': 450,
        'weight': 0.05,
        'sensitivity': 0.000058,
        'base_impact': 5
    },
    'top_pressure': {
        'min': 20, 'max': 40, 'optimal': 30,
        'weight': 0.05,
        'sensitivity': 0.003176,
        'base_impact': 5
    },
    'bottom_pressure': {
        'min': 15, 'max': 35, 'optimal': 25,
        'weight': 0.05,
        'sensitivity': 0.001230,
        'base_impact': 5
    },
    'feed_ph': {
        'min': 6, 'max': 8, 'optimal': 7,
        'weight': 0.05,
        'sensitivity': 0.010348,
        'base_impact': 5
    }
}

def smooth_transition(x, center, sensitivity):
    """Create a smooth transition using sigmoid function"""
    return expit(-(x - center) * sensitivity)

def calculate_parameter_impact(value, param_info):
    """Calculate normalized impact with smooth transitions"""
    optimal = param_info['optimal']
    min_val = param_info['min']
    max_val = param_info['max']
    sensitivity = param_info['sensitivity']
    base_impact = param_info['base_impact']

    # Normalize distance from optimal
    range_size = max_val - min_val
    normalized_distance = abs(value - optimal) / range_size

    # Calculate base effect using smooth transition
    base_effect = smooth_transition(normalized_distance, 0, 1/sensitivity)

    # Scale effect by base impact
    impact = base_impact * base_effect

    # Apply small penalty for being outside optimal range
    if value < min_val or value > max_val:
        excess = min(abs(value - optimal) / range_size, 1)
        impact *= (1 - 0.2 * excess)

    return impact

def calculate_total_conversion(params):
    """Calculate glycerol conversion with normalized impacts"""
    # Calculate derived parameters
    pressure_diff = params['top_pressure'] - params['bottom_pressure']
    temps = [params['t1'], params['t2'], params['t3'], params['t4'], params['t5']]
    avg_temperature = sum(temps) / len(temps)
    temp_range = max(temps) - min(temps)

    # Calculate individual impacts
    impacts = {name: calculate_parameter_impact(value, OPTIMAL_RANGES[name])
              for name, value in params.items()}

    # Calculate base conversion with temperature average effect
    base_conversion = 60  # Minimum expected conversion

    # Sum weighted impacts
    total_impact = sum(impacts.values())

    # Calculate final conversion with smoother scaling
    conversion = base_conversion + total_impact

    # Ensure realistic bounds
    conversion = np.clip(conversion, 0, 100)

    return conversion, impacts

def main():
    # Custom CSS
    st.markdown("""
        <style>
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 10px 20px;
        }
        .metric-container {
            background-color: #e8f4f8;
            padding: 20px;
            border-radius: 5px;
            border: 2px solid #2c3e50;
            text-align: center;
            margin: 20px 0;
        }
        .info-text {
            color: #2980b9;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.title("Glycerol Conversion Calculator")
    st.markdown("Advanced model with normalized parameter impacts")

    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Temperature Control", "Process Parameters", "Pressure & pH Control"])

    # Temperature Control Tab
    with tab1:
        st.markdown("### Temperature Parameters")
        t2 = st.slider("T2 (°C) - Critical:", 180.0, 220.0, 200.0)
        t3 = st.slider("T3 (°C):", 180.0, 220.0, 200.0)
        t4 = st.slider("T4 (°C):", 180.0, 220.0, 200.0)
        t1 = st.slider("T1 (°C):", 180.0, 220.0, 195.0)
        t5 = st.slider("T5 (°C):", 180.0, 220.0, 195.0)

    # Process Parameters Tab
    with tab2:
        st.markdown("### Process Parameters")
        lhsv = st.slider("LHSV (1/h):", 0.4, 0.8, 0.6, 0.1)
        h2gly_ratio = st.slider("H2:GLY Ratio:", 5.0, 8.0, 6.5, 0.1)
        liquid_feed = st.slider("Liquid Feed (g/h):", 50, 150, 100)
        hydrogen_flow = st.slider("Hydrogen Flow (mL/min):", 300, 600, 450, 10)

    # Pressure & pH Control Tab
    with tab3:
        st.markdown("### Pressure & pH Parameters")
        top_pressure = st.slider("Top Pressure (bar):", 20, 40, 30)
        bottom_pressure = st.slider("Bottom Pressure (bar):", 15, 35, 25)
        feed_ph = st.slider("Feed pH:", 6.0, 8.0, 7.0, 0.1)

    # Calculate conversion and impacts
    params = {
        't2': t2,
        't3': t3,
        't4': t4,
        't1': t1,
        't5': t5,
        'lhsv': lhsv,
        'h2gly_ratio': h2gly_ratio,
        'liquid_feed': liquid_feed,
        'hydrogen_flow': hydrogen_flow,
        'top_pressure': top_pressure,
        'bottom_pressure': bottom_pressure,
        'feed_ph': feed_ph
    }

    conversion, impacts = calculate_total_conversion(params)

    # Display prediction
    st.markdown(f"""
        <div class="metric-container">
            <h2>Predicted Glycerol Conversion</h2>
            <h1>{conversion:.1f}%</h1>
        </div>
    """, unsafe_allow_html=True)

    # Display parameter impacts
    st.markdown("### Parameter Contributions")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### Temperature Impacts")
        for temp in ['t2', 't3', 't4', 't1', 't5']:
            st.write(f"{temp.upper()}: +{impacts[temp]:.1f}%")

    with col2:
        st.markdown("#### Process Parameters")
        st.write(f"LHSV: +{impacts['lhsv']:.1f}%")
        st.write(f"H2:GLY Ratio: +{impacts['h2gly_ratio']:.1f}%")
        st.write(f"Liquid Feed: +{impacts['liquid_feed']:.1f}%")
        st.write(f"Hydrogen Flow: +{impacts['hydrogen_flow']:.1f}%")

    with col3:
        st.markdown("#### Pressure & pH")
        st.write(f"Top Pressure: +{impacts['top_pressure']:.1f}%")
        st.write(f"Bottom Pressure: +{impacts['bottom_pressure']:.1f}%")
        st.write(f"Feed pH: +{impacts['feed_ph']:.1f}%")

    # Operating Guidelines
    st.markdown("### Operating Guidelines")
    st.markdown("""
    - Maintain T2-T4 within 195-205°C for optimal conversion
    - Keep pressure differential balanced for system stability
    - Monitor pH within optimal range of 6-8
    - Maintain proper H2:GLY ratio for reaction efficiency
    """)

if __name__ == "__main__":
    main()