def mean_value(X):
    return X.mean()

def maximum_value(X):
    return X.max()

def minimum_value(X):
    return X.min()

def percentile(X, q): # When the q_th percentile is needed, 0 < q < 1
    return X.quantile(q)

def nombre_ocurrences_au_dessus_seuil(X,seuil): # Attention à la définition de X
    compteur=0
    for x in X:
        if x>=seuil :
            compteur+=1
    return compteur
    
