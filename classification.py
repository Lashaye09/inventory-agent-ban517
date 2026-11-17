"""BAN 517 classification: ranks by descending Sales and Hits independently."""
import pandas as pd

COLS=['Item Number','Item Name','UoM','Sales ($)','Hits']
SCORE={'A':4,'B':3,'C':2,'D':1}


def _pareto_class(p):
    if p <= .60+1e-12: return 'A'
    if p <= .80+1e-12: return 'B'
    if p <= .90+1e-12: return 'C'
    return 'D'


def _independent_classes(df, metric):
    # Stable tie-breaking by item number. Each item is classified using its
    # cumulative percentage AFTER its contribution, with thresholds at 60/80/90%.
    ranked=df.sort_values([metric,'Item Number'],ascending=[False,True],kind='stable').copy()
    total=ranked[metric].sum()
    if total <= 0: raise ValueError(f'{metric} must have positive total')
    ranked['cumulative']=ranked[metric].cumsum()/total
    ranked['class']=ranked['cumulative'].map(_pareto_class)
    return ranked[['class','cumulative']].reindex(df.index)


def classify_inventory(df):
    missing=[x for x in COLS if x not in df.columns]
    if missing: raise ValueError(f'Missing columns: {missing}')
    result=df.copy().reset_index(drop=True)
    for col in ('Sales ($)','Hits'):
        result[col]=pd.to_numeric(result[col],errors='raise')
        if result[col].isna().any() or (result[col]<0).any():
            raise ValueError(f'{col} must contain nonnegative, nonmissing numbers')
    if result['Item Number'].duplicated().any(): raise ValueError('Duplicate Item Number values')
    if result[['Item Number','Item Name','UoM']].isna().any().any(): raise ValueError('Missing item identification data')
    for metric, prefix in [('Sales ($)','Sales'),('Hits','Hits')]:
        classified=_independent_classes(result,metric)
        result[f'{prefix} Cumulative %']=classified['cumulative']*100
        result[f'{prefix} Class']=classified['class']
        result[f'{prefix} Score']=result[f'{prefix} Class'].map(SCORE)
    result['Weighted Score']=(.65*result['Sales Score']+.35*result['Hits Score']).round(10)
    result['Final Class']=result['Weighted Score'].map(lambda v:'A' if v>=3.25 else 'B' if v>=2.5 else 'C' if v>=1.75 else 'D')
    return result


def classification_summary(result):
    summary=(result.groupby('Final Class').agg(Items=('Item Number','count'),Total_Sales=('Sales ($)','sum'))
             .reindex(list('ABCD'),fill_value=0).reset_index())
    return summary.rename(columns={'Total_Sales':'Total Sales ($)'})
