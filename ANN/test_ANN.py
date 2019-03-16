#create labels associated with X
def get_y(X):
    
    #create the classification labels
    y = np.zeros(N)
    
    #choose condition for label 1
    idx1 = np.where(X[:, 1] > -X[:,0])
    
    #condition for label -1 is just the complement of the label 1 set
    idxm1 = np.setdiff1d(np.arange(N), idx1)
    
    #set labels
    y[idx1] = 1.0
    y[idxm1] = -1.0

    return y, idx1, idxm1

import numpy as np
import matplotlib.pyplot as plt

plt.close('all')

##########################################################
#generate synthetic LINEARLY SEPERABLE classification data
##########################################################

#number of data points
N = 100

#N draws from multivariate normal with mean mu and covariance matrix Sigma
mu = np.array([0, 0])
Sigma = np.array([[1, 0.0], [0.0, 1.0]])
X = np.random.multivariate_normal(mu, Sigma, size = N)

#get the labels
y, idx1, idxm1 = get_y(X)
