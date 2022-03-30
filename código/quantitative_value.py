#%% bibliotecas
import pandas as pd
import numpy as np
import math as mt 
from datetime import date
import matplotlib.pyplot as plt
import quantstats as qt
from scipy import stats

#%%função para tratar as bases de dados
def limp_base(nome_base, legenda1='', legenda2='',legenda3='',legenda4='',legenda5=''):
    base=pd.read_csv(nome_base,delimiter=';')
    base.columns=base.columns.str.replace(legenda1,'')
    base.columns=base.columns.str.replace(legenda2,'')
    base.columns=base.columns.str.replace(legenda3,'')
    base.columns=base.columns.str.replace(legenda4,'')
    base.columns=base.columns.str.replace(legenda5,'')
    base.columns=base.columns.str.replace('*','')
    base.columns=base.columns.str.strip()
    base=base.replace('-',np.nan)
    base.Data=pd.to_datetime(base.Data,dayfirst=True)
    base=base.melt(id_vars='Data')
    base.value=base.value.str.replace('.','')
    base.value=base.value.str.replace(',','.')
    base.value=pd.to_numeric(base.value)
    base.value=base.value.replace(0,np.nan)
    base=base.pivot_table(index='Data',columns='variable',values='value')
    base=base.reset_index()
    return base


#função para selecionar as ações do universo com base em algum critério:
def Factor(data_inicial,rebalanceamento,base,lookback,pos_ativo=(0),qt_ativos=(-1),universo=[0],ordem=True):
        
    data_analise=data_inicial-pd.DateOffset(months=lookback)
    fator=base[(base.Data>data_analise)&(base.Data<=data_inicial)]
    fator=fator.dropna(axis=0,how='all')
    if universo==[0]:
        fator=fator.iloc[-1]
    if not universo==[0]:
        fator=fator.loc[:,universo]
        fator=fator.pct_change()
        fator=fator.std()*252**0.5
    fator=fator[1:]
    fator=fator.sort_values(ascending=ordem)
    fator_valores=pd.DataFrame(fator[pos_ativo:qt_ativos])
    fator_name=list(fator_valores.index)
    
    return fator_valores, fator_name
    
#função para executar o backtest
def backtesting(data_inicial,rebalanceamento,base,universo,longshort=1):
        
    #long,short=1,-1
    peso=1/len(universo)
    backtest=base[(base.Data>data_inicial)&(base.Data<rebalanceamento)]
    backtest=backtest.set_index('Data')
    backtest=backtest.loc[:,universo]
    backtest=backtest.pct_change()
    backtest=backtest.replace(np.nan,0)
    backtest=backtest*(longshort)
    backtest=backtest.add(1)
    backtest[0:1]=backtest[0:1]*peso
    backtest=backtest.cumprod()
    backtest['retorno']=backtest.sum(axis=1)        
    backtest.retorno=backtest.retorno.pct_change()
    backtest_ret=pd.DataFrame(backtest.retorno[1:])
    
    # Perf Atribution
    pcr=backtest.loc[:,backtest.columns!='retorno']
    sp=backtest.retorno
    sp=sp.add(1).cumprod()
    sp=sp.replace(np.nan,1)
    peso_corrido=pcr.div(sp,axis=0)
    ret_at=peso_corrido*pcr.pct_change()
    ret_at=ret_at.add(1).cumprod().add(-1)
    ret_at=ret_at*100
    
    return backtest_ret,ret_at
    
#função comboaccrual: capítulo 3
def comboaccrual(rebal, data_inicial,rebalanceamento):
    
    
     universo_valores, universo_list=Factor(data_inicial,rebalanceamento,base=ineg,lookback=1,qt_ativos=100,ordem=False)        
     sta=pd.DataFrame()
     data_analise=data_inicial-pd.DateOffset(months=3)
     caixaopf=caixaoper[(caixaoper.Data>=data_analise)&(caixaoper.Data<=data_inicial)]
     atcircf=atcirc[(atcirc.Data>=data_analise)&(atcirc.Data<=data_inicial)]
     atf=at[(at.Data>=data_analise)&(at.Data<=data_inicial)]
     lucroliqf=lucroliq[(lucroliq['Data']>=data_analise)&(lucroliq['Data']<=data_inicial)]
     pascircf=pascirc[(pascirc.Data>=data_analise)&(pascirc.Data<=data_inicial)]
     caixaopf, atf, lucroliqf,atcircf, pascircf= caixaopf.T, atf.T, lucroliqf.T, atcircf.T, pascircf.T
 
     staf=pd.merge(pd.merge(caixaopf,atf,on='variable'),lucroliqf,on='variable')
     staf=staf.reset_index()
     staf=staf[staf.variable.isin(universo_list)]
     staf.columns=['Ticker','Caixa_Op','Ativo','Lucro_liq']
     staf['STA']=(staf.Lucro_liq-staf.Caixa_Op)/staf.Ativo
     staf=staf.replace(0,np.nan)
     staf=staf.dropna(axis='rows')
     staf=staf.sort_values(by='STA',ascending=False)
     staf=staf.reset_index()
     staf=staf.reset_index()
     n=len(staf.Ticker)
     staf['p_sta']=(staf['level_0']+1)/n
     staf=staf.drop(['Lucro_liq','Caixa_Op','Ativo','index','level_0', 'STA' ],axis=1)
     
     snoa=pd.DataFrame()
     snoa=pd.merge(pd.merge(atcircf,pascircf,on='variable'),atf,on='variable')
     snoa=snoa.reset_index()
     snoa=snoa[snoa.variable.isin(universo_list)]
     snoa.columns=['Ticker','Ativo_Circ','Passivo_Circ','Ativo']
     snoa['SNOA']=(snoa.Ativo_Circ-snoa.Passivo_Circ)/snoa.Ativo
     snoa=snoa.replace(0,np.nan)
     snoa=snoa.dropna(axis='rows')
     snoa=snoa.sort_values(by='SNOA',ascending=False)
     snoa=snoa.reset_index()
     snoa=snoa.reset_index()
     p=len(snoa.Ticker)
     snoa['p_snoa']=(snoa['level_0']+1)/p
     snoa=snoa.drop(['Ativo_Circ','Passivo_Circ','Ativo','index','level_0', 'SNOA' ],axis=1)
 
     comboaccrual=pd.DataFrame()
     comboaccrual=pd.merge(snoa, staf,on='Ticker')
     comboaccrual['media']=(comboaccrual['p_sta']+comboaccrual['p_snoa'])/2
     comboaccrual=comboaccrual.sort_values(by='media', ascending=True)
     
 #Elimine todas as empresas entre os 5% melhores da amostra com base no COMBOACCRUAL.    
     del_comboaccrual=pd.DataFrame()
     del_comboaccrual=comboaccrual[:int(0.05*len(comboaccrual))]
     del_comboaccrual=list(del_comboaccrual.Ticker)
     
     return del_comboaccrual   


#função PMAN (probabilidade de manipulação): capítulo 3

def pman(rebal, data_inicial,rebalanceamento):
    
     universo_valores, universo_list=Factor(data_inicial,rebalanceamento,base=ineg,lookback=1,qt_ativos=100,ordem=False)        
     data_analise=data_inicial-pd.DateOffset(months=3)
     data_inicial2=data_inicial-pd.DateOffset(months=12)
     data_analise2=data_analise-pd.DateOffset(months=12)
     
     receblpf=receblp[(receblp.Data>=data_analise)&(receblp.Data<=data_inicial)]
     recebcpf=recebcp[(recebcp.Data>=data_analise)&(recebcp.Data<=data_inicial)]
     receblp_a=receblp[(receblp.Data>=data_analise2)&(receblp.Data<=data_inicial2)]
     recebcp_a=recebcp[(recebcp.Data>=data_analise2)&(recebcp.Data<=data_inicial2)]
    
     margembf=margembruta[(margembruta.Data>=data_analise)&(margembruta.Data<=data_inicial)]
     margemb_a=margembruta[(margembruta.Data>=data_analise2)& (margembruta.Data<=data_inicial2)]  
     
     atintangf=at_intang[(at_instang.Data>=data_analise)&(at_intang.Data<=data_inicial)]
     atncirc=atncirc[(atncirc.Data>=data_analise)&(atncirc.Data<=data_inicial)]
    
     receitaf=receita[(receita.Data>=data_analise)&(receita.Data<=data_inicial)]
     receita_a=receita[(receita.Data>=data_analise2)& (receita.Data<=data_inicial2)]  
     
     tdepref=taxa_depreciacao[(taxa_depreciacao.Data>=data_analise)&(taxa_depreciacao.Data<=data_inicial)]
     tdepre_a=taxa_depreciacao[(taxa_depreciacao.Data>=data_analise2)& (taxa_depreciacao.Data<=data_inicial2)] 
     
     despsgaf=despsga[(despsga.Data>=data_analise)&(despsga.Data<=data_inicial)]
     despsga_a=despsga[(despsga.Data>=data_analise2)& (despsga.Data<=data_inicial2)]  
     
     atf=at[(at.Data>=data_analise)&(at.Data<=data_inicial)]
     at_a=at[(at.Data>=data_analise2)& (at.Data<=data_inicial2)] 
     
     pastf=passivo_total[(passivo_total.Data>=data_analise)&(passivo_total.Data<=data_inicial)]
     past_a=passivo_total[(passivo_total.Data>=data_analise2)&(passivo_total.Data<=data_inicial2)] 
     
     pasncircf=pasncirc[(pasncirc.Data>=data_analise)&(pasncirc.Data<=data_inicial)]
     pasncirc_a=pasncirc[(pasncirc.Data>=data_analise2)&(pasncirc.Data<=data_inicial2)] 
     
     atcircf=atcirc[(atcirc.Data>=data_analise)&(atcirc.Data<=data_inicial)]
     atcirc_a=atcirc[(atcirc.Data>=data_analise2)&(atcirc.Data<=data_inicial2)] 
     
     caixaf=caixa[(caixa.Data>=data_analise)&(caixa.Data<=data_inicial)]
     caixa_a=caixa[(caixa.Data>=data_analise2)&(caixa.Data<=data_inicial2)] 
     
     deprecf=caixa[(depreciacao.Data>=data_analise)&(depreciacao.Data<=data_inicial)]
     
    
     
     receblp, recebcp,recebcp_a, receblp_a = receblp.T, recebcp.T, recebcp_a.T, receblp_a.T
     margembf, margemb_a, atintangf, atncirc= margembf.T, margemb_a.T, atintangf.T, atncirc.T
     receitaf, receita_a, tdepref, tdepre_a= receitaf.T, receita_a.T, tdepref.T, tdepre_a.T
     despsgaf, despsga_a, pasncircf, pasncirc_a= despsgaf.T, despsga_a.T, pasncircf.T, pasncirc_a.T
     atcircf,  atcirc_a, caixaf, caixa_a, deprecf=  atcircf.T,  atcirc_a.T, caixaf.T, caixa_a.T, deprecf.T
     
     
     dsri=pd.DataFrame()
     dsri=pd.merge(pd.merge(pd.merge(receblpf,recebcpf,on='variable'),recebcp_a,on='variable'), receblp_a, on='variable')
     dsri=dsri.reset_index()
     dsri=dsri[dsri.variable.isin(universo_list)]
     dsri.columns=['ticker','receb_lp','receb_cp','recebcp_a','receblp_a']
     dsri['DSRI']=(dsri.receb_lp+dsri.receb_cp)/(dsri.recebcp_a+dsri.receblp_a)
     dsri=dsri.replace(0,np.nan)
     dsri=dsri.dropna(axis='rows')
     dsri=dsri.drop(['receb_lp','receb_cp','recebcp_a','receblp_a' ],axis=1)
     
     gmi=pd.DataFrame()
     gmi=pd.merge(margembf, margemb_a, on='variable')
     gmi=gmi.reset_index()
     gmi=gmi[gmi.variable.isin(universo_list)]
     gmi.columns=['ticker', 'margemb','margemb_a']
     gmi['GMI']=gmi.margemb_a/gmi.margemb     
     gmi=gmi.replace(0,np.nan)
     gmi=gmi.dropna(axis='rows')
     gmi=gmi.drop(['margemb','margemb_a'])
     
     aqi=pd.DataFrame()
     aqi=pd.merge(atintangf, atncirc, on='variable')
     aqui=aqui.reset_index()
     aqi=aqi[aqi.variable.isin(universo_list)]
     aqi.columns=['ticker', 'atintang','atncirc']
     aqi['AQI']=aqi.atintang/aqi.atncirc
     aqi=aqi.replace(0,np.nan)
     aqi=aqi.dropna(axis='rows')
     aqi=aqi.drop(['atintang','atncirc'])
     
     sgi=pd.DtaFrame()
     sgi=pd.merge(receitaf, receita_a, on='variable')
     sgi=sgi.reset_index()
     sgi=sgi[sgi.variable.isin(universo_list)]
     sgi.columns=['receitaf','receita_a']
     sgi['SGI']=sgi.receitaf/sgi.receita_a
     sgi=sgi.replace(0,np.nan)
     sgi=sgi.dropna(axis='rows')
     sgi=sgi.drop(['receitaf','receita_a'])
     
     depi=depi.pd.DataFrame()
     depi=pd.merge(tdepref, tdepre_a, on='variable')
     depi=depi.reset_index()
     depi=depi[depi.variable.isin(universo_list)]
     depi.columns=['ticker', 'tdepref','tdepre_a']
     depi['DEPI']=depi.tdepre_a/depi.tdepref
     depi=depi.replace(0,np.nan)
     depi=depi.dropna(axis='rows')
     depi=depi.drop(['tdepref','tdepre_a'])
     
     sgai=pd.DataFrame()
     sgai=pd.merge(despsgaf, despsga_a, on='variable')
     sgai=sgai.reset_index()
     sgai=sgai[sgai.variable.isin(universo_list)]
     sgai.columns=['ticker', 'despsgaf','despsga_a']
     sgai['SGAI']=sgai.despsgaf/sgai.despsga_a
     sgai=sgai.replace(0,np.nan)
     sgai=sgai.dropna(axis='rows')
     sgai=sgai.drop(['despsgaf','despsga_a'])
     
     lvgi=pd.DataFrame()
     lvgi=pd.merge(pd.merge(pd.merge(atf,at_a,on='variable'),pastf,on='variable'), past_a, on='variable')
     lvgi=lvgi.reset_index()
     lvgi=lvgi[lvgi.variable.isin(universo_list)]
     lvgi.columns=['ticker','atf','at_a','pastf','past_a']
     lvgi['LVGI']=(lvgi.pastf/lvgi.atf)/(lvgi.past_a/lvgi.at_a)
     lvgi=lvgi.replace(0,np.nan)
     lvgi=lvgi.dropna(axis='rows')
     lvgi=lvgi.drop(['atf','at_a','pastf','past_a'],axis=1)
     
     tata=pd.DataFrame()
     tata=pd.merge(pd.merge(pd.merge(pd.merge(pd.merge(pd.merge(atcircf,atcirc_a,on='variable'),pasncircf,on='variable'), pasncirc_a, on='variable'),caixaf, on='variable'), caixa_a, on='variable'), deprecf, on='variable')
     tata=tata.reset_index()
     tata=tata[tata.variable.isin(universo_list)]
     tata.columns=['ticker','atcircf','atcirc_a','pasncircf','pasncirc_a','caixaf', 'caixa_a', 'deprecf']
     tata['TATA']= (tata.atcircf-tata.pasncircf-tata.caixaf)-(tata.atcirc_a- tata.pasncirc_a- tata.caixa_a)- (tata.deprecf)
     tata=tata.replace(0,np.nan)
     tata=tata.dropna(axis='rows')
     tata=tata.drop(['atcircf','atcirc_a','pasncircf','pasncirc_a','caixaf', 'caixa_a', 'deprecf'],axis=1)
     
     probm=pd.DataFrame()
     probm=pd.merge(pd.merge(pd.merge(pd.merge(pd.merge(pd.merge(pd.merge(dsri,gmi, on='ticker'), aqi, on='ticker'), sgi, on='ticker'), depi, on='ticker'), sgai, on='ticker'), lvgi, on='ticker'), tata, on='ticker')
     probm=probm.reset_index()
     
     probm['PROBM']= − 4.84 + 0.92*probm.DSRI + 0.528*probm.GMI + 0.404*probm.AQI + 0.892*probm.SGI + 0.115*probm.DEPI − 0.172*probm.SGAI + 4.679*probm.TATA − 0.327*probm.LVGI       
     tata=tata.reset_index()
     probm['PMAN']= stats.norm.cdf(probm['PROBM'],loc=probm['PROBM'].mean(), scale=probm['PROBM'].std())
     
     probm=probm.sort_values(by='PMAN', ascending=True)
     
 #Elimine todas as empresas entre os 5% melhores da amostra com base no probm.    
     del_probm=pd.DataFrame()
     del_probm=probm[:int(0.05*len(probm))]
     del_probm=list(del_probm.Ticker)
     
     return del_probm  

# função pdf, probabilidade de dificuldade financeira: capítulo 4
def pfd():
    
    
    universo_valores, universo_list=Factor(data_inicial,rebalanceamento,base=ineg,lookback=1,qt_ativos=100,ordem=False)        
    data_analise=data_inicial-pd.DateOffset(months=3)
    data_inicial2=data_inicial-pd.DateOffset(months=3)
    data_analise2=data_analise-pd.DateOffset(months=3)
    data_inicial3=data_inicial-pd.DateOffset(months=6)
    data_analise3=data_analise-pd.DateOffset(months=6)
    data_inicial4=data_inicial-pd.DateOffset(months=9)
    data_analise4=data_analise-pd.DateOffset(months=9)

    
    pastf=passivo_total[(passivo_total.Data>=data_analise)&(passivo_total.Data<=data_inicial)]
    past1=passivo_total[(passivo_total.Data>=data_analise2)&(passivo_total.Data<=data_inicial2)] 
    past2=passivo_total[(passivo_total.Data>=data_analise3)&(passivo_total.Data<=data_inicial3)] 
    past3=passivo_total[(passivo_total.Data>=data_analise4)&(passivo_total.Data<=data_inicial4)] 
     
    lucroliqf=lucroliq[(lucroliq.Data>=data_analise)&(lucroliq.Data<=data_inicial)]
    lucroliq1=lucroliq[(lucroliq.Data>=data_analise2)&(lucroliq.Data<=data_inicial2)] 
    lucroliq2=lucroliq[(lucroliq.Data>=data_analise3)&(lucroliq.Data<=data_inicial3)] 
    lucroliq3=lucroliq[(lucroliq.Data>=data_analise4)&(lucroliq.Data<=data_inicial4)] 
    
    
      
    nimtaavg=pd.dataFrae()
    
    
#%%tratando todas os dados que serão utilizados
at=limp_base(r'C:\PC_IQFC\dados_quantitative_value\ativo.csv')
atcirc=limp_base(r'C:\PC_IQFC\dados_quantitative_value\ativocirc.csv')
receita=limp_base(r'C:\PC_IQFC\dados_quantitative_value\receitaliq.csv')
pascirc=limp_base(r'C:\PC_IQFC\dados_quantitative_value\pascirc.csv')
caixaoper=limp_base(r'C:\PC_IQFC\dados_quantitative_value\caixaoper.csv')
close=limp_base(r'C:\PC_IQFC\dados_quantitative_value\fechamento (1).csv')
lucroliq=limp_base(r'C:\PC_IQFC\dados_quantitative_value\lucroliquido.csv')
ineg=limp_base(r'C:\PC_IQFC\dados_quantitative_value\ineg_fim.csv')
recebl_CP=limp_base(r'C:\PC_IQFC\dados_quantitative_value\recebiveis_CP.csv')
recebl_LP=limp_base(r'C:\PC_IQFC\dados_quantitative_value\recebiveis_LP.csv')
receita=limp_base(r'C:\PC_IQFC\dados_quantitative_value\receitabruta.csv')
passivo_total=limp_base(r'C:\PC_IQFC\dados_quantitative_value\passivo_total.csv')
caixa=limp_base(r'C:\PC_IQFC\dados_quantitative_value\caixa.csv')
depreciacao=limp_base(r'C:\PC_IQFC\dados_quantitative_value\depreciacao.csv')
taxa_depreciacao=limp_base(r'C:\PC_IQFC\dados_quantitative_value\taxa_depreciacao.csv')
receita_liq=limp_base(r'C:\PC_IQFC\dados_quantitative_value\receitaliq.csv')
at_intang=limp_base(r'C:\PC_IQFC\dados_quantitative_value\ativos_intangiveis.csv')
atncirc=limp_base(r'C:\PC_IQFC\dados_quantitative_value\ativoncirc.csv')
despsga=limp_base(r'C:\PC_IQFC\dados_quantitative_value\desp_op_liq.csv')

    

    
    
    
    
    
    
    
    
    
    
    
    
    
    