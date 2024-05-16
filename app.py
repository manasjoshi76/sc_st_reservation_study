import branca
import folium
import geopandas as gpd
import pandas as pd
import streamlit as st
from streamlit_folium import folium_static

# Initate Fixed Elements
parameters = {"SC Population": "population_sc", "Approximate Disengagement Rate (ADR)": "adr", "SC Schemes (SJSA Dept)": "sjsa_schemes"}
bar_colors = ["darkgreen", "green", "yellow", "orange", "red", "darkred"]
state_location = {"Maharashtra": [18.95,76.54], "Punjab": [30.9010, 75.8573], "Bihar": [25.7850, 85.4798], "Karnataka": [15.317, 75.73]}
state_zoom = {"Maharashtra": 7, "Punjab": 7.5, "Bihar": 7.5, "Karnataka": 7}

# Create a sidebar
st.sidebar.title("Select Filters")

# Create a selectbox to select a state
state_selectbox = st.sidebar.selectbox("Select State", ["Maharashtra", "Punjab", "Bihar", "Karnataka"])
selected_state = state_selectbox.lower()

# Create a selectbox to check for SC/ADR/Schemes
if selected_state == "maharashtra":
    parameter_selectbox = st.sidebar.selectbox("Select Parameter", ["SC Population", "Approximate Disengagement Rate (ADR)", "SC Schemes (SJSA Dept)"])
else:
    parameter_selectbox = st.sidebar.selectbox("Select Parameter", ["SC Population", "Approximate Disengagement Rate (ADR)"])
selected_parameter = parameters[parameter_selectbox]

# Read the map.geojson file
districts = gpd.read_file(f"{selected_state}/districts.geojson")
districts.crs = {'init': 'epsg:4326'}

# Create a streamlit app
st.markdown(f"<h3 style='text-align: left'>District Wise Analysis of {state_selectbox} State:</h3>", unsafe_allow_html=True)
st.markdown(f"<h4 style='text-align: left'>{parameter_selectbox}</h4>", unsafe_allow_html=True)

if selected_parameter != "sjsa_schemes":
    # Create a selectbox for gender
    selectbox_1 = st.sidebar.selectbox("Select Gender", ["Persons", "Males", "Females"])
    selected_choice_1 = selectbox_1.lower()

    # Create a selectbox for region
    selectbox_2 = st.sidebar.selectbox("Select Region", ["Total", "Rural", "Urban"])
    selected_choice_2 = selectbox_2.lower()

    # Generate the District wise SC-ADR Data
    sc_data = pd.read_csv(f"{selected_state}/adr.csv")
    districts_merged_data = districts.merge(sc_data, how="outer", left_on=["district_code", "district_name"], right_on=["district_code", "district_name"])

else:
    # Create a selectbox for scheme
    selectbox_1 = st.sidebar.selectbox("Select Schemes", ["Total", "22250281-277.1.A.1- MAINT.OF GOVT.HOST.FOR SC.BOYS/GIRLS", "22250352-277.2.A.1- GOVT.OF INDIA POST MATRIC SCHOLARSHIP", "22253262-01/277/(04)(18) - RAJASHRI SHAHU MAHARAJ MERIT AWARD FOR S.C. STUDENTS COMING IN SPL. MERIT LIST", "22253342- Opening and Maintenance of Government Hostels for Schedule Castes Boys and Girls", "2225D117- Opening of Government Residential School for Scheduled Caste Boys & Girls"])
    selected_choice_1 = selectbox_1.split("-")[0].lower()

    # Create a selectbox for year
    selectbox_2 = st.sidebar.selectbox("Select Year", ["Total", "2020-21", "2021-22", "2022-23"])
    selected_choice_2 = selectbox_2.replace('-', '_').lower()

    # Generate the District wise SC-Schemes Datas
    schemes_data = pd.read_csv(f"{selected_state}/sjsa_schemes.csv")
    districts_merged_data = districts.merge(schemes_data, how="outer", left_on=["district_code", "district_name"], right_on=["district_code", "district_name"])

# Filter the data based on the selected choices
selected_choice = f"{selected_parameter}_{selected_choice_1}_{selected_choice_2}"
selected_choice_percent = f"{selected_choice}_percent"

# Add the percentage column in the merged dataframe
if selected_parameter == "population_sc":
    if selected_choice_1 == "persons":
        districts_merged_data[selected_choice_percent] = (
            districts_merged_data[selected_choice] /
            districts_merged_data[f"population_all_persons_{selected_choice_2}"]
        ) * 100
    else:
        districts_merged_data[selected_choice_percent] = (
            districts_merged_data[selected_choice] /
            districts_merged_data[f"{selected_parameter}_persons_{selected_choice_2}"]
        ) * 100
elif selected_parameter == "adr":
    districts_merged_data[selected_choice_percent] = districts_merged_data[selected_choice]
else:
    districts_merged_data[selected_choice_percent] = (
        districts_merged_data[f"{selected_parameter}_{selected_choice_1}_distributed_{selected_choice_2}"] /
        districts_merged_data[f"{selected_parameter}_{selected_choice_1}_received_{selected_choice_2}"]
    ) * 100

# Create a choropleth map
colormap = branca.colormap.LinearColormap(
    vmin=districts_merged_data[selected_choice_percent].quantile(0.0),
    vmax=districts_merged_data[selected_choice_percent].quantile(1.0),
    colors=bar_colors if selected_parameter != "sjsa_schemes" else bar_colors[::-1],
    caption=f"District Wise {parameter_selectbox} of {state_selectbox} State ({selectbox_1} & {selectbox_2}) - Percentage",
)

m = folium.Map(location=state_location[state_selectbox], zoom_start=state_zoom[state_selectbox])

popup = folium.GeoJsonPopup(
    fields=["district_name", selected_choice_percent],
    aliases=["District", f"{parameter_selectbox} ({selected_choice_1} & {selectbox_2}) [%]"],
    localize=True,
    labels=True,
    style="background-color: yellow;",
)

tooltip = folium.GeoJsonTooltip(
    fields=["district_name", selected_choice_percent],
    aliases=["District", f"{parameter_selectbox} ({selected_choice_1} & {selectbox_2}) [%]"],localize=True,
    sticky=False,
    labels=True,
    style="""
        background-color: #F0EFEF;
        border: 2px solid black;
        border-radius: 3px;
        box-shadow: 3px;
    """,
    max_width=800,
)

g = folium.GeoJson(
    districts_merged_data,
    style_function=lambda x: {
        "fillColor": colormap(x["properties"][selected_choice_percent])
        if x["properties"][selected_choice_percent] is not None
        else "transparent",
        "color": "black",
        "fillOpacity": 0.4,
    },
    tooltip=tooltip,
    popup=popup,
).add_to(m)

colormap.add_to(m)

# Add the map to the streamlit app
folium_static(m, width=800, height=700)

if selected_parameter != "sjsa_schemes":
    st.markdown(f"<h5 style='text-align: left'>GENDER: {selectbox_1}</h5>", unsafe_allow_html=True)
    st.markdown(f"<h5 style='text-align: left'>REGION: {selectbox_2}</h5>", unsafe_allow_html=True)
else:
    st.markdown(f"<h5 style='text-align: left'>SCHEME: {selectbox_1}</h5>", unsafe_allow_html=True)
    st.markdown(f"<h5 style='text-align: left'>YEAR: {selectbox_2}</h5>", unsafe_allow_html=True)
