import pandas as pd
import os
import streamlit as st
import folium
from streamlit_folium import folium_static
import branca

# Set working directory (modify as needed)
os.chdir("C:/Users/nilst/streamlit")

# Load the data
df = pd.read_csv("df_5.csv")

# Drop rows with missing 'Probability' values and filter out invalid construction years
df = df.dropna(subset=['Probability'])
df = df[~df['CONSTRUCTION_YEAR'].isin([11, 111, 999])]

df['Probability'] = df['Probability'].astype(float)

# Initialize session state variables
if 'bundesland' not in st.session_state:
    st.session_state['bundesland'] = []
if 'ortplz' not in st.session_state:
    st.session_state['ortplz'] = []
if 'construction_design' not in st.session_state:
    st.session_state['construction_design'] = []
if 'construction_year' not in st.session_state:
    st.session_state['construction_year'] = []
if 'wfl' not in st.session_state:
    st.session_state['wfl'] = []
if 'corporate_division' not in st.session_state:
    st.session_state['corporate_division'] = []
if 'damage_heavy_rain_zone' not in st.session_state:
    st.session_state['damage_heavy_rain_zone'] = []
if 'underwriter' not in st.session_state:
    st.session_state['underwriter'] = []
if 'prior_damages' not in st.session_state:
    st.session_state['prior_damages'] = []
if 'productline' not in st.session_state:
    st.session_state['productline'] = []

# Customize sidebar appearance
st.markdown("""
    <style>
    .main {
        background-color: #f0f0f0;
        font-family: Arial, sans-serif;
        padding: 20px;
        border-radius: 10px;
    }
    #logo {
        position: fixed;
        top: 80px;
        right: 300px;
        width: 50px; /* Breite des Logos */
    }
    .css-1d391kg {
        background-color: #111111; /* Hintergrundfarbe einer anderen Klasse */
    }
    </style>
    <div id="logo">
        <img src="https://seeklogo.com/images/G/gothaer-logo-A550232076-seeklogo.com.png" alt="Logo" >
    </div>
""", unsafe_allow_html=True)

# Header for the Streamlit app
st.title('Risk Score Prediction')

# Function to update Bundesland based on postal code selection
def update_bundesland():
    if st.session_state['ortplz']:
        selected_ortplz = st.session_state['ortplz']
        bundesland = df[df['ORTPLZ'].astype(str).isin(selected_ortplz)]['Bundesland'].unique()
        if len(bundesland) > 0:
            st.session_state['bundesland'] = list(bundesland)
        else:
            st.session_state['bundesland'] = []
    else:
        st.session_state['bundesland'] = []

# Function to update postal codes based on selected state
def update_ortplz_options():
    if st.session_state['bundesland']:
        sorted_ortplz = ['NONE'] + sorted(df[df['Bundesland'].isin(st.session_state['bundesland'])]['ORTPLZ'].astype(str).unique())
    else:
        sorted_ortplz = ['NONE'] + sorted(df['ORTPLZ'].astype(str).unique())
    return sorted_ortplz

# Sidebar for filters
with st.sidebar:
    st.header('Filter Options')

    # Dropdown menu to select Bundesland (Federal State)
    sorted_bundesland = ['NONE'] + sorted(df['Bundesland'].unique())
    bundesland = st.multiselect('Select State:', sorted_bundesland, key='bundesland_multiselect', default=st.session_state['bundesland'])

    # Dynamically filter postal codes based on Bundesland selection
    if bundesland:
        sorted_ortplz = ['NONE'] + sorted(df[df['Bundesland'].isin(bundesland)]['ORTPLZ'].astype(str).unique())
    else:
        sorted_ortplz = ['NONE'] + sorted(df['ORTPLZ'].astype(str).unique())
    
    ortplz = st.multiselect('Select Postal code:', sorted_ortplz, key='ortplz_multiselect', default=st.session_state['ortplz'])

    # Update Bundesland based on postal code selection
    update_bundesland()

    # Dropdown menu to select Corporate Division
    sorted_corporate_division = ['NONE'] + sorted(df['CORPORATE_DEVISION'].unique())
    corporate_division = st.multiselect('Select Corporate Division:', sorted_corporate_division, key='corporate_division_multiselect', default=st.session_state['corporate_division'])

    # Define bins and labels for Construction Year
    bins = [0, 1800, 1810, 1820, 1830, 1840, 1850, 1860, 1870, 1880, 1890, 1900, 1910, 1920, 1930, 1940, 1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020, float('inf')]
    labels = ['Before 1800', '1800-1809', '1810-1819', '1820-1829', '1830-1839', '1840-1849', '1850-1859', '1860-1869',
              '1870-1879', '1880-1889', '1890-1899', '1900-1909', '1910-1919', '1920-1929', '1930-1939', '1940-1949',
              '1950-1959', '1960-1969', '1970-1979', '1980-1989', '1990-1999', '2000-2009', '2010-2019', 'After 2020']

    # Apply binning to Construction Year
    df['CONSTRUCTION_YEAR_BINNED'] = pd.cut(df['CONSTRUCTION_YEAR'], bins=bins, labels=labels, right=False)

    sorted_construction_year = ['NONE'] + sorted(df['CONSTRUCTION_YEAR_BINNED'].astype(str).unique())
    construction_year = st.multiselect('Select Construction Year:', sorted_construction_year, key='construction_year_multiselect', default=st.session_state['construction_year'])

    # Add dropdown for DAMAGE_HEAVY_RAIN_ZONE with predefined ranges
    rain_zone_ranges = {
        "1": (1.0, 1.5),
        "2": (1.5, 2.5),
        "3": (2.5, 3.0)
    }
    damage_heavy_rain_zone = st.multiselect('Select Heavy Rain Zone:', ['NONE'] + list(rain_zone_ranges.keys()), key='damage_heavy_rain_zone_multiselect', default=st.session_state['damage_heavy_rain_zone'])

    # Define bins and labels for Wohnfläche (WFL)
    wfl_bins = range(0, 1000, 10)
    wfl_labels = [f'{start}-{start+9}' for start in wfl_bins[:-1]]

    # Conditionally filter Wohnfläche (WFL) based on Construction Year selection
    if construction_year:
        df_filtered_construction = df[df['CONSTRUCTION_YEAR_BINNED'].astype(str).isin(construction_year)]
    else:
        df_filtered_construction = df.copy()

    if not df_filtered_construction.empty:
        df_filtered_construction['WFL_BINNED'] = pd.cut(df_filtered_construction['WFL'], bins=wfl_bins, labels=wfl_labels, right=False)

    sorted_wfl = ['NONE'] + sorted(df_filtered_construction['WFL_BINNED'].astype(str).unique()) if 'WFL_BINNED' in df_filtered_construction.columns else ['NONE']
    wfl = st.multiselect('Select Living Space in sqm:', sorted_wfl, key='wfl_multiselect', default=st.session_state['wfl'])

    # Add dropdown for PRIOR_DAMAGES
    sorted_prior_damages = ['NONE'] + sorted(df['PRIOR_DAMAGES'].unique())
    prior_damages = st.multiselect('Select Prior Damages:', sorted_prior_damages, key='prior_damages_multiselect', default=st.session_state['prior_damages'])

    # Add dropdown for PRODUCTLINE
    sorted_productline = ['NONE'] + sorted(df['PRODUCTLINE'].unique())
    productline = st.multiselect('Select Product Line:', sorted_productline, key='productline_multiselect', default=st.session_state['productline'])

    # Add dropdown for underwriter with options "Y" and "N" if the column exists
    if 'UNDERWRITER' in df.columns:
        underwriter = st.multiselect('Select Underwriter:', ['NONE', 'Y', 'N'], key='underwriter_multiselect', default=st.session_state['underwriter'])
    else:
        underwriter = ['NONE']

    # Dropdown menu to select Construction Design
    sorted_construction_design = ['NONE'] + sorted(df['CONSTRACTION_DESIGN'].unique())
    construction_design = st.multiselect('Select the Construction design:', sorted_construction_design, key='construction_design_multiselect', default=st.session_state['construction_design'])

# Results display
st.subheader('Select your features, then press submit: ')

# Button to refresh and calculate probability
if st.button('Submit with selected features'):
    # Filter DataFrame based on the selected filters
    df_filtered = df.copy()

    if bundesland:
        df_filtered = df_filtered[df_filtered['Bundesland'].isin(bundesland)]

    if ortplz:
        df_filtered = df_filtered[df_filtered['ORTPLZ'].astype(str).isin(ortplz)]

    if construction_design:
        df_filtered = df_filtered[df_filtered['CONSTRACTION_DESIGN'].isin(construction_design)]

    if corporate_division:
        df_filtered = df_filtered[df_filtered['CORPORATE_DEVISION'].isin(corporate_division)]

    if construction_year:
        df_filtered = df_filtered[df_filtered['CONSTRUCTION_YEAR_BINNED'].astype(str).isin(construction_year)]

    if wfl and 'WFL_BINNED' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['WFL_BINNED'].astype(str).isin(wfl)]

    if damage_heavy_rain_zone:
        for zone in damage_heavy_rain_zone:
            rain_zone_min, rain_zone_max = rain_zone_ranges[zone]
            df_filtered = df_filtered[(df_filtered['DAMAGE_HEAVY_RAIN_ZONE'] >= rain_zone_min) & (df_filtered['DAMAGE_HEAVY_RAIN_ZONE'] <= rain_zone_max)]

    if underwriter and 'UNDERWRITER' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['UNDERWRITER'].isin(underwriter)]

    if prior_damages:  # Filter based on PRIOR_DAMAGES selection
        df_filtered = df_filtered[df_filtered['PRIOR_DAMAGES'].isin(prior_damages)]

    if productline:
        df_filtered = df_filtered[df_filtered['PRODUCTLINE'].isin(productline)]

    # Calculate mean probability based on selected filters
    if not df_filtered.empty:
        mean_probability = df_filtered['Probability'].mean() * 100
        st.markdown(f'<h3 style="color: black;">The Risk Score for the selected filters is: {mean_probability:.2f}%</h3>', unsafe_allow_html=True)

        # Get the first 10 ANO_SID and Probability values that were used in the calculation
        #first_10_observations = df_filtered.head(10)[['ANO_SID', 'Probability']]
        #st.write('First 10 observations included in the calculation:')
       # st.write(first_10_observations)
    else:
        st.write('No data available for the selected filters.')

    # Store the filtered dataframe in session state for later use
    st.session_state['df_filtered'] = df_filtered

# Button to display the list of used properties (ANO_SID)
if st.button('List of used properties'):
    if 'df_filtered' in st.session_state and not st.session_state['df_filtered'].empty:
        num_used_observations = st.session_state['df_filtered'].shape[0]
        st.write(f'Number of used observations: {num_used_observations}')

        used_properties = st.session_state['df_filtered']['ANO_SID'].unique()
        st.write('List of used properties (ANO_SID):')
        st.write(used_properties)
    else:
        st.write('No data available for the selected filters.')

# Button to display the map
if st.button('Map'):
    # Filtered DataFrame and calculation of probabilities
    if 'df_filtered' in st.session_state and not st.session_state['df_filtered'].empty:
        filtered_df = st.session_state['df_filtered']
        mean_probability = filtered_df['Probability'].mean() * 100
        
        # Number of used properties
        used_properties_count = len(filtered_df['ANO_SID'].unique())
        
        # Calculate the count of properties in each probability range
        count_0_5 = filtered_df[(filtered_df['Probability'] >= 0) & (filtered_df['Probability'] <= 0.05)].shape[0]
        count_5_10 = filtered_df[(filtered_df['Probability'] > 0.05) & (filtered_df['Probability'] <= 0.10)].shape[0]
        count_10_15 = filtered_df[(filtered_df['Probability'] > 0.10) & (filtered_df['Probability'] <= 0.15)].shape[0]
        count_15_20 = filtered_df[(filtered_df['Probability'] > 0.15) & (filtered_df['Probability'] <= 0.20)].shape[0]
        count_20_25 = filtered_df[(filtered_df['Probability'] > 0.20) & (filtered_df['Probability'] <= 0.25)].shape[0]
        count_over_75 = filtered_df[filtered_df['Probability'] > 0.25].shape[0]
        
        # Display the results in Streamlit
        st.markdown(f'<h3 style="color: black;">The Risk Score for the selected filters is: {mean_probability:.2f}%</h3>', unsafe_allow_html=True)
        st.markdown(f'<h4 style="color: black; font-size: 20px;">Number of used properties: {used_properties_count}</h4>', unsafe_allow_html=True)
        
        # Format the text for the legend with colors specified directly
        properties_count_text = (
            f"0-5%: <span style='color:#8BC34A;'>{count_0_5}</span>  |  "
            f"5-15%: <span style='color:#4CAF50;'>{count_5_10}</span>  |  "
            f"15-25%: <span style='color:#006400;'>{count_10_15}</span>  |  "
            f"25-50%: <span style='color:#FF9800;'>{count_15_20}</span>  |  "
            f"Over 50%: <span style='color:#FF5722;'>{count_over_75}</span>"
        )

        st.markdown(f'<h4 style="color: black; font-size: 16px;">{properties_count_text}</h4>', unsafe_allow_html=True)


        # Create a folium map centered around Germany
        map = folium.Map(location=[51.2657, 10.4515], zoom_start=6)

        # Function to determine marker color based on probability
        def get_marker_color(probability):
            # Probability range: 0% to 5% -> lightgreen
            if 0 <= probability <= 0.05:
                return ('lightgreen')  # '#4CAF50' -> lightgreen RGBA
            
            # Probability range: >5% to 10% -> green
            elif 0.05 < probability <= 0.15:
                return ('green')  # '#8BC34A' -> green RGBA
            
            # Probability range: >10% to 15% -> lightblue
            elif 0.15 < probability <= 0.25:
                return ('darkgreen')  # '#CDDC39' -> lightblue RGBA
                        
            # Probability range: >20% to 25% -> orange
            elif 0.25 < probability <= 0.5:
                return ('orange')   # '#FF5722' -> orange RGBA
            else:
                return ('red')   # '#B71C1C' -> darkred RGBA



        # Add markers for each property in the filtered dataframe
        for index, row in filtered_df.iterrows():
            # Determine marker color based on Probability
            marker_color = get_marker_color(row['Probability'])

            # Create popup content
            popup_content = f"""
            <b>ANO_SID:</b> {row['ANO_SID']}<br>
            <b>Bundesland:</b> {row['Bundesland']}<br>
            <b>Postal Code:</b> {row['ORTPLZ']}<br>
            <b>Construction Design:</b> {row['CONSTRACTION_DESIGN']}<br>
            <b>Construction Year:</b> {row['CONSTRUCTION_YEAR']}<br>
            <b>Living Space (WFL):</b> {row['WFL']} sqm<br>
            <b>Heavy Rain Zone Damage:</b> {row['DAMAGE_HEAVY_RAIN_ZONE']}<br>
            <b>Prior Damages:</b> {row['PRIOR_DAMAGES']}<br>
            <b>Underwriter:</b> {row['UNDERWRITER']}<br>
            <b>Product Line:</b> {row['PRODUCTLINE']}<br>
            <b>Latitude:</b> {row['LATITUDE']}<br>
            <b>Longitude:</b> {row['LONGITUDE']}<br>
            <b>Probability:</b> {row['Probability']}<br>
            """

            # Add marker to map with the determined color
            folium.Marker(
                [row['LATITUDE'], row['LONGITUDE']],
                popup=popup_content,
                icon=folium.Icon(color=marker_color)
            ).add_to(map)
        
        folium_static(map, width=750, height=650)  # folium_static(map, width=1000, height=800)  # Adjust width and height as needed

        # Display legend for probability colors
        st.markdown("""
            <style>
            .legend-container {
                margin-top: 20px;
            }
            .legend-title {
                font-weight: bold;
                font-size: 16px;
                margin-bottom: 5px;
            }
            .legend {
                display: flex;
                flex-wrap: wrap;
                justify-content: space-between;
            }
            .legend-item {
                display: flex;
                align-items: center;
                margin-bottom: 5px;
                width: 45%;
            }
            .legend-item div {
                width: 20px;
                height: 20px;
                margin-right: 5px;
                border-radius: 50%;
            }
            </style>
        """, unsafe_allow_html=True)

        legend_html = """
            <div class="legend-container">
                <div class="legend-title">Probability Legend:</div>
                <div class="legend">
                    <div class="legend-item">
                        <div style="background-color: lightgreen;"></div> 0% - 5%
                    </div>
                    <div class="legend-item">
                        <div style="background-color: green;"></div> >5% - 15%
                    </div>
                    <div class="legend-item">
                        <div style="background-color: darkgreen;"></div> >15% - 25%
                    </div>
                    <div class="legend-item">
                        <div style="background-color: orange;"></div> >25% - 50%
                    </div>
                    <div class="legend-item">
                        <div style="background-color: red;"></div> >50%
                    </div>
                </div>
            </div>
        """
        st.markdown(legend_html, unsafe_allow_html=True)
        
    else:
        st.write('No data available to display on the map.')

