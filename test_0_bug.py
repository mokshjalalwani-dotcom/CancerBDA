import pandas as pd
df=pd.read_csv('target_ready_dataset.tsv', sep='\t', low_memory=False)
genes=['ENSG00000276168.1', 'ENSG00000198886.2', 'ENSG00000198712.1']
for g in genes:
  med = df[g].median()
  valid = df[df[g] >= med]
  valid_surv = valid[valid['survival_label'].notna()]
  rate = (valid_surv['survival_label'] == 0).sum() / len(valid_surv) * 100 if len(valid_surv) > 0 else 0
  print(f'{g} median: {med}, valid len: {len(valid_surv)}, 0 count: {(valid_surv["survival_label"] == 0).sum()}, Rate: {rate}%')
