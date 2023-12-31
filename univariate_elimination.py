def univariate_analysis(data, key_var, corr_type='spearman', na_th=1, gini_th=0.20, corr_th=0.60):
    """
    
    
    """
    import pandas as pd
    import numpy as np
    from tqdm import tqdm
    import time
    from lightgbm import LGBMClassifier
    from sklearn import metrics
    from sklearn import preprocessing
    import warnings
    warnings.filterwarnings("ignore")
    from sklearn.metrics import roc_auc_score
    
    start = time.time()
    

    ews_analiz = pd.DataFrame(columns = ["column","auc", "gini","DOLULUK"]) 
    X=data.drop('TARGET' ,axis=1)
    y=data["TARGET"]
    
    print('Gini Hesaplanıyor...')
    for column in tqdm(data.columns):
        if esnaf_df[column].dtype != '<M8[ns]':
            if column not in key_var: 
                temp=pd.DataFrame(data[column])
                columnType = temp[column].dtype
                if columnType == 'O' : ## object type
                    temp=temp.fillna('Missing')
                    temp[column]=temp[column].astype('str')
                    labelEncoder = preprocessing.LabelEncoder()
                    labelEncoder.fit(temp[column])
                    temp[column] = labelEncoder.transform(temp[column])
                else :
                    temp=temp.fillna(-999999999999) 
                        
                temp = temp.values.reshape(-1,1)
                temp_count=temp.shape[0]            
                clf = LGBMClassifier(verbose=-1)
                clf = clf.fit(temp,y)
        
                predictions = clf.predict_proba(temp)
        
                auc=roc_auc_score(y, predictions[:,1])
                gini = 2*auc - 1  
                doluluk=data[column].notna().mean()*100
                #corr=data[column].corr()['TARGET']
                dfColumn = pd.DataFrame({'column':column,'auc':auc, 'gini':gini,   'DOLULUK':doluluk ,  'columntype':columnType}, index = [column])
                #i = i + 1
                ews_analiz = pd.concat([ews_analiz, dfColumn], ignore_index=True)
                
                
    desc_data = data.describe([0.01, 0.25,0.50, 0.75, 0.99]).T
    desc_data = desc_data.reset_index()
    desc_data = desc_data.rename(columns={'index': 'column'})
    ews_analiz_bireysel = ews_analiz.reset_index(drop=True)
    detail = pd.DataFrame()
    detail["column"] = data.columns
    ews_analiz_bireysel_1 = pd.merge(detail, ews_analiz_bireysel, how='left', on='column')
    data_final = pd.merge(ews_analiz_bireysel_1, desc_data, how='left', on='column')
    ##data_final.to_excel("0_250k_Esnaf_Univarite.xlsx")
    print('Gini Hesaplaması', round(((time.time()-start)/60),2), 'Dakika Sürdü')
    print('##############################')
    start_1 = time.time()
    
    print('Korelasyon Hesaplanıyor...')
    data_final.loc[(data_final["columntype"].isna()), "ELEME"] = 'ON_ELEME'
    data_final.loc[(data_final["DOLULUK"]<na_th), "ELEME"] = 'NA_ELEME' 
    data_final.loc[(data_final["gini"]<gini_th), "ELEME"] = 'GINI_ELEME' 
    features = data_final["column"].loc[(data_final["ELEME"].isna()) & (data_final["columntype"]!='object')]
    data_corr = data[features].corr(method='spearman')
    print('Korelasyon Matrisi', round(((time.time()-start_1)/60),2), 'Dakika Sürdü')
    
    corr_unstack = data_corr.abs().unstack().reset_index()
    corr_unstack.columns = ['SOL', 'SAĞ', 'CORR']
    corr_unstack.to_excel("EWS_ESNAF_0_250K_KKB_Korelasyon.xlsx")
    corr_unstack_1 = corr_unstack.loc[(corr_unstack["CORR"]>corr_th) & (corr_unstack["CORR"]<1)]
    sol_gini = data_final[["column", "gini"]].rename(columns={"column": "SOL", "gini":"gini_sol"})
    sağ_gini = data_final[["column", "gini"]].rename(columns={"column": "SAĞ", "gini":"gini_sağ"})
    corr_unstack_2 = pd.merge(corr_unstack_1, sol_gini, how='left', on='SOL')
    corr_unstack_3 = pd.merge(corr_unstack_2, sağ_gini, how='left', on='SAĞ')
    corr_unstack_3["RANK"] = corr_unstack_3.groupby(["SOL"])["gini_sağ"].rank(method="first", ascending=False)
    corr_unstack_3.loc[corr_unstack_3["gini_sol"] <= corr_unstack_3["gini_sağ"] , "ELEME_NEDENI"] = "CORR_ELEME"
    corr_unstack_4 = corr_unstack_3.loc[corr_unstack_3["RANK"]==1]
    corr_unstack_4.loc[corr_unstack_4["ELEME_NEDENI"]=='CORR_ELEME', 'CORR_NEDENI'] = corr_unstack_4["SAĞ"].loc[corr_unstack_4["ELEME_NEDENI"]=='CORR_ELEME'] 
    corr_unstack_5 = corr_unstack_4[["SOL", "ELEME_NEDENI", "CORR", "CORR_NEDENI"]].rename(columns={"SOL": "column"})
    corr_unstack_6 = pd.merge(data_final, corr_unstack_5, how='left', on='column' )
    corr_unstack_6["ELEME_NEDENI"].fillna(corr_unstack_6["ELEME"], inplace=True)
    corr_unstack_7 = corr_unstack_6.drop('ELEME' ,axis=1)
    corr_unstack_7.to_excel("EWS_ESNAF_0_250K_KKB_LongList.xlsx")
    
    return corr_unstack_7
