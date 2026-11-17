"""Run with: streamlit run app.py"""
import json
import pandas as pd
import streamlit as st
from classification import classify_inventory,classification_summary
from inventory_tools import (calculate_eoq, calculate_quantity_discount, calculate_rop,
                             calculate_periodic_review, calculate_newsvendor)

st.set_page_config(page_title='BAN 517 Inventory Decision Agent',layout='wide')
st.title('Inventory Decision Analytics Agent')
st.caption('Deterministic Python inventory models and multicriteria classification')

st.sidebar.header('Inventory CSV')
file=st.sidebar.file_uploader('Upload inventory CSV',type=['csv'])
if file is not None:
    try:
        data=pd.read_csv(file,encoding='utf-8-sig')
        st.session_state['uploaded_inventory']=data
    except Exception as e: st.sidebar.error(f'CSV error: {e}')

page=st.sidebar.radio('Choose tool',['Inventory Classification','Economic Order Quantity','Quantity Discount',
                  'Safety Stock / Reorder Point','Fixed-Period Review','Newsvendor'])

if page=='Inventory Classification':
    st.subheader('Multicriteria Inventory Classification')
    st.write('Sales 65% · POS Hits 35% · independent Pareto classes 60/80/90/100%')
    if 'uploaded_inventory' not in st.session_state:
        st.info('Upload your inventory CSV in the sidebar to classify the items.')
    else:
        try:
            classified=classify_inventory(st.session_state['uploaded_inventory'])
            summary=classification_summary(classified)
            st.subheader('Final classification summary')
            st.dataframe(summary,use_container_width=True,hide_index=True)
            st.metric('Inventory items',len(classified))
            st.metric('Total sales',f"${classified['Sales ($)'].sum():,.2f}")
            st.subheader('Item-level results')
            st.dataframe(classified,use_container_width=True,hide_index=True)
            st.download_button('Download classified inventory CSV',classified.to_csv(index=False).encode('utf-8-sig'),
                               file_name='classified_inventory.csv',mime='text/csv')
            st.download_button('Download summary CSV',summary.to_csv(index=False).encode('utf-8-sig'),
                               file_name='classification_summary.csv',mime='text/csv')
            st.caption('Convention: rank highest first, assign each row using cumulative share including that row; ties by Item Number. Check this boundary convention against your instructor’s examples.')
        except Exception as e: st.error(str(e))
else:
    st.subheader(page)
    st.write('Enter all numerical inputs explicitly; blank or inconsistent inputs are not guessed.')
    with st.form('calculator'):
        if page=='Economic Order Quantity':
            D=st.number_input('Annual demand (units)',min_value=0.0,value=1200.0)
            S=st.number_input('Cost per order ($)',min_value=0.0,value=50.0)
            H=st.number_input('Annual holding cost per unit ($)',min_value=0.0,value=2.0)
        elif page=='Quantity Discount':
            D=st.number_input('Annual demand (units)',min_value=0.0,value=1200.0)
            S=st.number_input('Cost per order ($)',min_value=0.0,value=50.0)
            mode=st.radio('Holding cost method',['Fixed cost per unit','Percentage of unit price'])
            h=st.number_input('Holding cost ($/unit/year) or holding rate (fraction)',min_value=0.0,value=0.2)
            tiers_text=st.text_area('All-units discount tiers (JSON)',value='[{"min_qty": 1, "unit_price": 10}, {"min_qty": 100, "unit_price": 9.5}]')
        elif page=='Safety Stock / Reorder Point':
            d=st.number_input('Mean demand per period',min_value=0.0,value=50.0)
            L=st.number_input('Mean lead time (periods)',min_value=0.0,value=2.0)
            z=st.number_input('Service factor z',min_value=0.0,value=1.65)
            sd=st.number_input('Demand standard deviation per period',min_value=0.0,value=10.0)
            sL=st.number_input('Lead time standard deviation',min_value=0.0,value=0.0)
        elif page=='Fixed-Period Review':
            d=st.number_input('Mean demand per period',min_value=0.0,value=50.0)
            T=st.number_input('Review period',min_value=0.0,value=1.0)
            L=st.number_input('Mean lead time',min_value=0.0,value=2.0)
            ip=st.number_input('Inventory position',value=75.0)
            z=st.number_input('Service factor z',min_value=0.0,value=1.65)
            sd=st.number_input('Demand standard deviation per period',min_value=0.0,value=10.0)
            sL=st.number_input('Lead time standard deviation',min_value=0.0,value=0.0)
        else:
            p=st.number_input('Selling price ($)',min_value=0.0,value=20.0)
            c=st.number_input('Unit cost ($)',min_value=0.0,value=12.0)
            v=st.number_input('Salvage value ($)',min_value=0.0,value=5.0)
            m=st.number_input('Mean demand',min_value=0.0,value=100.0)
            sd=st.number_input('Demand standard deviation',min_value=0.0,value=20.0)
        submitted=st.form_submit_button('Calculate')
    if submitted:
        try:
            if page=='Economic Order Quantity': result=calculate_eoq(D,S,H)
            elif page=='Quantity Discount':
                tiers=json.loads(tiers_text)
                result=calculate_quantity_discount(D,S,tiers,holding_cost=h if mode=='Fixed cost per unit' else None,
                                                   holding_rate=h if mode!='Fixed cost per unit' else None)
            elif page=='Safety Stock / Reorder Point': result=calculate_rop(d,L,z,sd,sL)
            elif page=='Fixed-Period Review': result=calculate_periodic_review(d,T,L,ip,z,sd,sL)
            else: result=calculate_newsvendor(p,c,v,m,sd)
            st.success('Calculated in Python')
            st.json(result)
        except (ValueError,TypeError,KeyError) as e: st.error(f'Check your inputs: {e}')

st.divider()
st.caption('This version uses menu-based model selection. It does not yet include the lecture’s language-model-based natural-language question router.')
