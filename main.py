from altair.vegalite.v4.api import value
from matplotlib.pyplot import step, xlabel
import streamlit as st 
import skrf as rf
import plotly.figure_factory as ff
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from numpy import shape
from itertools import product
from os import remove
pd.options.plotting.backend = "plotly"
st.set_option('deprecation.showPyplotGlobalUse', False)
st.set_page_config(layout="wide")
file = st.sidebar.file_uploader('Upload Touchstone File Here',)
if file:
    filename = 'file.'+file.name.split('.')[-1]
    with open(filename,"wb") as f:
        f.write((file).getbuffer())
    ntwk = rf.Network(filename)
    remove(filename)
    ntwk.name = file.name
    plot = ntwk.s_db
    plot_shape = shape(plot[0])
    df = pd.DataFrame(data=[])
    columns = ['S{}{}'.format(x+1,y+1) for (x,y) in list(product(range(plot_shape[0]), repeat=2))]
    vswr_columns = ['S{}{}'.format(x+1,y+1) for (x,y) in list(product(range(plot_shape[0]), repeat=2)) if x==y]
    result_dict = {k:[] for k in columns}
    temp_list = []
    for x in plot:
        for y in range(shape(x)[1]):
            for z in range(shape(x)[0]):
                temp = result_dict['S{}{}'.format(y+1,z+1)]
                temp.append(x[y,z])
                result_dict['S{}{}'.format(y+1,z+1)] = temp
    df = df.from_dict(result_dict)
    df['freq'] = ntwk.f/1E9
    #smooth_size = st.sidebar.number_input('Enter Smoothing Factor',min_value=1,max_value=20,value=1,step=1)
    title = st.sidebar.text_input('Enter Plot Title Here')
    selected_columns = st.sidebar.multiselect('Select Parameters to Plot',options=[x for x in df.columns.values if x != 'freq'],default=[x for x in df.columns.values if x != 'freq'])
    vswr_columns = ['S{}{}'.format(x+1,y+1) for (x,y) in list(product(range(plot_shape[0]), repeat=2)) if x==y]
    vswr_columns = [x for x in vswr_columns if x in selected_columns]
    vswr_bool = st.sidebar.checkbox('Display Return Loss as VSWR?')
    dual_bool = st.sidebar.checkbox('Display Return Loss with Secondary Axis?')
    # upper_freq_limit = st.sidebar.select_slider('Upper Frequency Range',options = df['freq'],value=df['freq'].max())
    # lower_freq_limit = st.sidebar.select_slider('Lower Frequency Range',options = df['freq'],value=df['freq'].min())
    # df = df[(df['freq'] >= lower_freq_limit) & (df['freq']<=upper_freq_limit)]
    # nearest = alt.selection(type='single', nearest=True, on='mouseover',
    #                         fields=['freq'], empty='none')
    # source = df.reset_index().melt(id_vars=['freq'], value_vars=[x for x in df.columns.values if x != 'freq'])
    # selection = alt.selection_multi(fields=[x for x in df.columns.values if x != 'freq'], bind='legend')
    # line = alt.Chart(source).mark_line(interpolate='basis').encode(
    #      x='freq:Q', y='value:Q', tooltip='variable:N',color='variable:N')
    # selectors = alt.Chart(source).mark_point().encode(
    #     x='freq:Q',
    #     opacity=alt.value(0),
    # ).add_selection(
    #     nearest
    # )

    # # Draw points on the line, and highlight based on selection
    # points = line.mark_point().encode(
    #     opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    # )

    # # Draw text labels near the points, and highlight based on selection
    # text = line.mark_text(align='left', dx=.01, dy=-.01).encode(
    #     text=alt.condition(nearest, 'value:Q', alt.value(' '))
    # )

    # # Draw a rule at the location of the selection
    # rules = alt.Chart(source).mark_rule(color='gray').encode(
    #     x='freq:Q',
    # ).transform_filter(
    #     nearest
    # )

    # # Put the five layers into a chart and bind the data
    # c = alt.layer(
    #     line, selectors, points, rules, text
    # ).properties(
    #     height=750
    # )
    if vswr_bool:
        for x in vswr_columns:
            df[x] = df[x].apply(lambda t: (10**(abs(t)/20)+1)/(10**(abs(t)/20)-1))
        dual_bool = True
    if not dual_bool:
        fig = df.plot(x='freq',y= selected_columns,kind = 'line',title=title,
                        labels=dict(freq="Frequency (GHz)",value="Magnitude (dB)",variable='S Parameter'))
    else:
        non_vswr_columns = [x for x in selected_columns if x not in vswr_columns]
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        if non_vswr_columns:
            fig1 = df.plot(x='freq',y= non_vswr_columns,kind = 'line',title=title,
                            labels=dict(freq="Frequency (GHz)",value="Magnitude (dB)",variable='S Parameter'))
        else:
            fig1 = None
        if vswr_columns:
            fig2 = df.plot(x='freq',y= vswr_columns,kind = 'line',title=title,
                            labels=dict(freq="Frequency (GHz)",value="VSWR",variable='S Parameter'))
        else:
            fig2 = None
        if not fig1 and not fig2:
            st.error('No Parameters Selected')
        elif not fig1:
            fig.add_traces(fig2.data)  
            fig.layout.xaxis.title="Frequency (GHz)"
            fig.layout.yaxis.title="VSWR"
            fig.layout.title = title 
        elif not fig2:
            fig.add_traces(fig1.data)  
            fig.layout.xaxis.title="Frequency (GHz)"
            fig.layout.yaxis.title="Magnitude (dB)"
            fig.layout.title = title 
        else:
            fig2.update_traces(yaxis="y2")
            fig.add_traces(fig1.data + fig2.data)
            fig.layout.xaxis.title="Frequency (GHz)"
            fig.layout.yaxis.title="Magnitude (dB)"
            fig.layout.yaxis2.title="VSWR"
            fig.layout.title = title
        # recoloring is necessary otherwise lines from fig und fig2 would share each color
        # e.g. Linear-, Log- = blue; Linear+, Log+ = red... we don't want this
        fig.for_each_trace(lambda t: t.update(line=dict(color=t.marker.color)))
    fig.update_layout(height=750)
    st.plotly_chart(fig, use_container_width=True,height=800)
