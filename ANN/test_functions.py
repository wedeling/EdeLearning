def get_y_lin(N):

    #N draws from multivariate normal with mean mu and covariance matrix Sigma
    mu = np.array([0, 0])
    Sigma = np.array([[1.0, 0.0], [0.0, 1.0]])
    X = np.random.multivariate_normal(mu, Sigma, size = N)
    
    #create the classification labels
    y = np.zeros(N)
    
    #choose condition for label 1
    idx1 = np.where(X[:, 1] > -X[:,0])
    
    #condition for label -1 is just the complement of the label 1 set
    idxm1 = np.setdiff1d(np.arange(N), idx1)
    
    #set labels
    y[idx1] = 1.0
    y[idxm1] = -1.0

    return X, y, idx1, idxm1

def get_y_quad(N):
    
    #N draws from multivariate normal with mean mu and covariance matrix Sigma
    mu = np.array([0, 0])
    Sigma = np.array([[1.0, 0.0], [0.0, 1.0]])
    X = np.random.multivariate_normal(mu, Sigma, size = N)

    #create the classification labels
    y = np.zeros(N)
    
    #choose condition for label 1
    idx1 = np.where(X[:, 1] > X[:,0]**2)
    
    #condition for label -1 is just the complement of the label 1 set
    idxm1 = np.setdiff1d(np.arange(N), idx1)
    
    #set labels
    y[idx1] = 1.0
    y[idxm1] = -1.0

    return X, y, idx1, idxm1

def get_y_quadrant(N):

    #N draws from multivariate normal with mean mu and covariance matrix Sigma
    mu = np.array([0, 0])
    Sigma = np.array([[1.0, 0.0], [0.0, 1.0]])
    X = np.random.multivariate_normal(mu, Sigma, size = N)

    #create the classification labels
    y = np.zeros(N)
    
    #choose condition for label 1
    idx1 = np.where(np.sign(X[:, 1]) == np.sign(X[:,0]))
    
    #condition for label -1 is just the complement of the label 1 set
    idxm1 = np.setdiff1d(np.arange(N), idx1)
    
    #set labels
    y[idx1] = 1.0
    y[idxm1] = -1.0

    return X, y, idx1, idxm1

def get_lin_regres(N):
    
    a = -1.0; b = 1.0
    X = np.random.rand(N)*(b-a) + a
    noise = np.random.randn(N)*1e-2
    
    y = X + noise + 1.0
    
    return X, y

def get_quad_regres(N):
    
    a = -1.0; b = 1.0
    X = np.random.rand(N)*(b-a) + a
    noise = np.random.randn(N)*1e-2
    
    y = X**2 + noise
    
    return X, y

def get_sin_regres(N):

    a = 0.0; b = 3.0*np.pi
    X = np.random.rand(N)*(b-a) + a
    noise = np.random.randn(N)*1e-2
    y = np.sin(2*X) + np.exp(0.1*X) + noise
    
    return X, y

def get_tau_EZ_regres(n_days, name):
    
    import os
    import h5py
    
    HOME = os.path.abspath(os.path.dirname(__file__))
    
    ###########################
    # load the reference data #
    ###########################
    
    #fname = HOME + '/samples/dE_dZ_training.hdf5'
    fname = HOME + '/samples/training_t_4495.1.hdf5'
    #fname = HOME + '/samples/tau_EZ_training_t_3170.0.hdf5'
    h5f = h5py.File(fname, 'r')
    
    QoI = list(h5f.keys())
    
    print(QoI)
    
    #time scale
    Omega = 7.292*10**-5
    day = 24*60**2*Omega
    dt = 0.01
    N = np.int(n_days*day/dt) 
    
    sub = 1
    
    if name == 'dE':
        y = h5f['e_n_HF'][1:N:sub] - h5f['e_n_LF'][1:N:sub]
    else:
        y = h5f['z_n_HF'][1:N:sub] - h5f['z_n_LF'][1:N:sub]
    
    N_feat = 8
    X = np.zeros([y.size, N_feat])
    X[:, 0] = h5f['z_n_LF'][0:N-1:sub]
    X[:, 1] = h5f['e_n_LF'][0:N-1:sub]
    X[:, 2] = h5f['u_n_LF'][0:N-1:sub]
    X[:, 3] = h5f['s_n_LF'][0:N-1:sub]
    X[:, 4] = h5f['v_n_LF'][0:N-1:sub]
    X[:, 5] = h5f['o_n_LF'][0:N-1:sub]
    X[:, 6] = h5f['tau_E'][0:N-1:sub]*h5f['sprime_n_LF'][0:N-1:sub]*np.sign(h5f['sprime_n_LF'][0:N-1:sub])
    X[:, 7] = h5f['tau_Z'][0:N-1:sub]*h5f['zprime_n_LF'][0:N-1:sub]*np.sign(h5f['zprime_n_LF'][0:N-1:sub])
#    X[:, 6] = h5f['sprime_n_LF'][0:N-1:sub]
#   X[:, 7] = h5f['zprime_n_LF'][0:N-1:sub]
    
    t = h5f['t'][0:N-1:sub]
    
    return X, y, t

def get_tau_EZ_binned(n_days, name, n_bins):
    
    import os
    import h5py
    
    HOME = os.path.abspath(os.path.dirname(__file__))
    
    ###########################
    # load the reference data #
    ###########################
    
    fname = HOME + '/samples/tau_EZ_training_t_3170.0.hdf5'
    #fname = HOME + '/samples/tau_EZ_T4_t_1710.0.hdf5'
    h5f = h5py.File(fname, 'r')
    
    QoI = list(h5f.keys())
    
    print(QoI)
    
    #time scale
    Omega = 7.292*10**-5
    day = 24*60**2*Omega
    dt = 0.01
    #N = h5f['e_n_LF'][:].size
    N = np.int(n_days*day/dt) 
    
    sub = 1
    
    if name == 'dE':
        y = h5f['e_n_HF'][1:N:sub] - h5f['e_n_LF'][1:N:sub]
    else:
        y = h5f['z_n_HF'][1:N:sub] - h5f['z_n_LF'][1:N:sub]
   
    N_feat = 7
    X = np.zeros([y.size, N_feat])
    X[:, 0] = h5f['z_n_LF'][0:N-1:sub]
    X[:, 1] = h5f['e_n_LF'][0:N-1:sub]
    X[:, 2] = h5f['u_n_LF'][0:N-1:sub]
    X[:, 3] = h5f['s_n_LF'][0:N-1:sub]
    X[:, 4] = h5f['v_n_LF'][0:N-1:sub]
#    X[:, 5] = h5f['o_n_LF'][0:N-1:sub]
#    X[:, 6] = h5f['tau_E'][0:N-1:sub]*h5f['sprime_n_LF'][0:N-1:sub]#*np.sign(h5f['sprime_n_LF'][0:N-1:sub])
#    X[:, 7] = h5f['tau_Z'][0:N-1:sub]*h5f['zprime_n_LF'][0:N-1:sub]#*np.sign(h5f['zprime_n_LF'][0:N-1:sub])
    X[:, 5] = h5f['sprime_n_LF'][0:N-1:sub]
    X[:, 6] = h5f['zprime_n_LF'][0:N-1:sub]
#    X[:, 8] = h5f['tau_E'][0:N-1:sub]*h5f['sprime_n_LF'][0:N-1:sub]*np.sign(h5f['sprime_n_LF'][0:N-1:sub]) + h5f['tau_Z'][0:N-1:sub]*h5f['zprime_n_LF'][0:N-1:sub]*np.sign(h5f['zprime_n_LF'][0:N-1:sub])
    
    t = h5f['t'][0:N-1:sub]
    
    bin_idx = np.zeros([y.size, n_bins])
    
    bins = np.linspace(np.min(y), np.max(y), n_bins+1)
    count, _, binnumbers = stats.binned_statistic(y, np.zeros(y.size), statistic='count', bins=bins)
    
    unique_binnumbers = np.unique(binnumbers) 
    
    for i in unique_binnumbers:
        idx = np.where(binnumbers == i)[0]
        bin_idx[idx, i-1] = 1.0    
    
    return X, y, bin_idx, bins, t

##############################################
    
def get_tau_EZ_binned_lagged(n_days, name, n_bins, n_lags):
    
    import os
    import h5py
    
    HOME = os.path.abspath(os.path.dirname(__file__))
    
    ###########################
    # load the reference data #
    ###########################
    
    fname = HOME + '/samples/tau_EZ_training_t_3170.0.hdf5'
    #fname = HOME + '/samples/tau_EZ_T4_t_1710.0.hdf5'
    h5f = h5py.File(fname, 'r')
    
    QoI = list(h5f.keys())
    
    print(QoI)
    
    #time scale
    Omega = 7.292*10**-5
    day = 24*60**2*Omega
    dt = 0.01
    #N = h5f['e_n_LF'][:].size
    N = np.int(n_days*day/dt) 
    
    sub = 1
    
    if name == 'dE':
        y = h5f['e_n_HF'][n_lags:N:sub] - h5f['e_n_LF'][n_lags:N:sub]
    else:
        y = h5f['z_n_HF'][n_lags:N:sub] - h5f['z_n_LF'][n_lags:N:sub]
   
    N_feat = 7
    X = np.zeros([y.size, N_feat, n_lags])
    for i in range(n_lags):
        begin = i
        end = N - n_lags + i
        X[:, 0, i] = h5f['z_n_LF'][begin:end:sub]
        X[:, 1, i] = h5f['e_n_LF'][begin:end:sub]
        X[:, 2, i] = h5f['u_n_LF'][begin:end:sub]
        X[:, 3, i] = h5f['s_n_LF'][begin:end:sub]
        X[:, 4, i] = h5f['v_n_LF'][begin:end:sub]
        X[:, 5, i] = h5f['sprime_n_LF'][begin:end:sub]
        X[:, 6, i] = h5f['zprime_n_LF'][begin:end:sub]
        
    X = X.reshape([y.size, N_feat*n_lags])
    
    #t of y
    t = h5f['t'][n_lags:N:sub]
    
    bin_idx = np.zeros([y.size, n_bins])
    
    bins = np.linspace(np.min(y), np.max(y), n_bins+1)
    count, _, binnumbers = stats.binned_statistic(y, np.zeros(y.size), statistic='count', bins=bins)
    
    unique_binnumbers = np.unique(binnumbers) 
    
    for i in unique_binnumbers:
        idx = np.where(binnumbers == i)[0]
        bin_idx[idx, i-1] = 1.0    
    
    return X, y, bin_idx, bins, t

##############################################

import numpy as np
from scipy import stats
