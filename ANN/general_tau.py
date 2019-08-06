
##########################
# S U B R O U T I N E S  #
##########################

#pseudo-spectral technique to solve for Fourier coefs of Jacobian
def compute_VgradW_hat(w_hat_n, P):
    
    #compute streamfunction
    psi_hat_n = w_hat_n/k_squared_no_zero
    psi_hat_n[0,0] = 0.0
    
    #compute jacobian in physical space
    u_n = np.fft.irfft2(-ky*psi_hat_n)
    w_x_n = np.fft.irfft2(kx*w_hat_n)

    v_n = np.fft.irfft2(kx*psi_hat_n)
    w_y_n = np.fft.irfft2(ky*w_hat_n)
    
    VgradW_n = u_n*w_x_n + v_n*w_y_n
    
    #return to spectral space
    VgradW_hat_n = np.fft.rfft2(VgradW_n)
    
    VgradW_hat_n *= P
    
    return VgradW_hat_n

#get Fourier coefficient of the vorticity at next (n+1) time step
def get_w_hat_np1(w_hat_n, w_hat_nm1, VgradW_hat_nm1, P, norm_factor, sgs_hat = 0.0):
    
    #compute jacobian
    VgradW_hat_n = compute_VgradW_hat(w_hat_n, P)
    
    #solve for next time step according to AB/BDI2 scheme
    w_hat_np1 = norm_factor*P*(2.0/dt*w_hat_n - 1.0/(2.0*dt)*w_hat_nm1 - \
                               2.0*VgradW_hat_n + VgradW_hat_nm1 + mu*F_hat - sgs_hat)
    
    return w_hat_np1, VgradW_hat_n

#compute spectral filter
def get_P(cutoff):
    
    P = np.ones([N, int(N/2+1)])
    
    for i in range(N):
        for j in range(int(N/2+1)):
            
            if np.abs(kx[i, j]) > cutoff or np.abs(ky[i, j]) > cutoff:
                P[i, j] = 0.0
                
    return P

#store samples in hierarchical data format, when sample size become very large
def store_samples_hdf5():
  
    fname = HOME + '/samples/' + store_ID + '_t_' + str(np.around(t_end/day, 1)) + '.hdf5'
    
    print('Storing samples in ', fname)
    
    if os.path.exists(HOME + '/samples') == False:
        os.makedirs(HOME + '/samples')
    
    #create HDF5 file
    h5f = h5py.File(fname, 'w')
    
    #store numpy sample arrays as individual datasets in the hdf5 file
    for q in QoI:
        h5f.create_dataset(q, data = samples[q])
        
    h5f.close()    

def draw():
    plt.subplot(131, title=r'$E$', xlabel=r'$t\;[day]$')
    plt.plot(np.array(T)/day, E_HF, 'o')
    plt.plot(np.array(T)/day, E_LF)
    plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
    plt.subplot(132, title=r'$Z$', xlabel=r'$t\;[day]$')
    plt.plot(np.array(T)/day, Z_HF, 'o')
    plt.plot(np.array(T)/day, Z_LF)
    plt.subplot(133, title=r'$W3$', xlabel=r'$t\;[day]$')
    plt.plot(np.array(T)/day, W3_HF, 'o')
    plt.plot(np.array(T)/day, W3_LF)
    
    plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
    plt.tight_layout()

#return the fourier coefs of the stream function
def get_psi_hat(w_hat_n):

    psi_hat_n = w_hat_n/k_squared_no_zero
    psi_hat_n[0,0] = 0.0

    return psi_hat_n

###############################
# DATA-DRIVEN TAU SUBROUTINES #
###############################

def compute_cij(T_hat, V_hat):

    n_scalar = T_hat.shape[0]
    c_ij = np.zeros([n_scalar, n_scalar-1])

    for i in range(n_scalar):
        A = np.zeros([n_scalar-1, n_scalar-1])
        b = np.zeros(n_scalar-1)

        k = np.delete(np.arange(n_scalar), i)

        for j1 in range(n_scalar-1):
            for j2 in range(n_scalar-1):
                integral = compute_int(V_hat[k[j1]], T_hat[i, j2+1])
                A[j1, j2] = integral

        for j1 in range(n_scalar-1):
            integral = compute_int(V_hat[k[j1]], T_hat[i, 0])
            b[j1] = integral

        if n_scalar == 2:
            c_ij[i,:] = b/A
        else:
            c_ij[i,:] = np.linalg.solve(A, b)
            
    return c_ij

def get_data_driven_tau_src_EZ(w_hat_n_LF, w_hat_n_HF, P, tau_max_E, tau_max_Z):
    
    E_LF, Z_LF, S_LF = get_EZS(w_hat_n_LF)

    src_E = E_LF**2/Z_LF - S_LF
    src_Z = -E_LF**2/S_LF + Z_LF

    E_HF = compute_E(P*w_hat_n_HF)
    Z_HF = compute_Z(P*w_hat_n_HF)

    dE = (E_HF - E_LF)#/E_LF
    dZ = (Z_HF - Z_LF)#/Z_LF

    tau_E = tau_max_E*np.tanh(dE/E_LF)*np.sign(src_E)
    tau_Z = tau_max_Z*np.tanh(dZ/Z_LF)*np.sign(src_Z)
    
    return tau_E, tau_Z, dE, dZ

def get_surrogate_tau_src_EZ(w_hat_n_LF, r, tau_max_E, tau_max_Z):
    
    E_LF, Z_LF, S_LF = get_EZS(w_hat_n_LF)

    src_E = E_LF**2/Z_LF - S_LF
    src_Z = -E_LF**2/S_LF + Z_LF

    dE = r[0] 
    dZ = r[1]

    tau_E = tau_max_E*np.tanh(dE/E_LF)*np.sign(src_E)
    tau_Z = tau_max_Z*np.tanh(dZ/Z_LF)*np.sign(src_Z)
    
    return tau_E, tau_Z

def get_EZS(w_hat_n):

    psi_hat_n = w_hat_n/k_squared_no_zero
    psi_hat_n[0,0] = 0.0
    psi_n = np.fft.irfft2(psi_hat_n)
    w_n = np.fft.irfft2(w_hat_n)
    
    e_n = -0.5*psi_n*w_n
    z_n = 0.5*w_n**2
    w3_n = w_n**3/3.0 

    E = simps(simps(e_n, axis), axis)/(2*np.pi)**2
    Z = simps(simps(z_n, axis), axis)/(2*np.pi)**2
    W3 = simps(simps(w3_n, axis), axis)/(2*np.pi)**2

    return E, Z, W3

#compute the energy at t_n
def compute_E(w_hat_n):
    
    psi_hat_n = w_hat_n/k_squared_no_zero
    psi_hat_n[0,0] = 0.0
    psi_n = np.fft.irfft2(psi_hat_n)
    w_n = np.fft.irfft2(w_hat_n)
    
    e_n = -0.5*psi_n*w_n

    E = simps(simps(e_n, axis), axis)/(2*np.pi)**2
    
    return E

#compute the enstrophy at t_n
def compute_Z(w_hat_n):
    
    w_n = np.fft.irfft2(w_hat_n)
    
    z_n = 0.5*w_n**2

    Z = simps(simps(z_n, axis), axis)/(2*np.pi)**2
    
    return Z

def compute_int(X1_hat, X2_hat):
    
    X1 = np.fft.irfft2(X1_hat)
    X2 = np.fft.irfft2(X2_hat)
    
    return simps(simps(X1*X2, axis), axis)/(2*np.pi)**2

#######################
# ORTHOGONAL PATTERNS #
#######################

def get_psi_hat_prime(w_hat_n):
    
    psi_hat_n = w_hat_n/k_squared_no_zero
    psi_hat_n[0, 0] = 0.

    psi_n = np.fft.irfft2(psi_hat_n)
    w_n = np.fft.irfft2(w_hat_n)

    nom = simps(simps(w_n*psi_n, axis), axis)
    denom = simps(simps(w_n*w_n, axis), axis)

    return psi_hat_n - nom/denom*w_hat_n

def get_w_hat_prime(w_hat_n):
    
    psi_hat_n = w_hat_n/k_squared_no_zero
    psi_hat_n[0, 0] = 0.

    psi_n = np.fft.irfft2(psi_hat_n)
    w_n = np.fft.irfft2(w_hat_n)

    nom = simps(simps(w_n*psi_n, axis), axis)
    denom = simps(simps(psi_n*psi_n, axis), axis)

    return w_hat_n - nom/denom*psi_hat_n

#compute the (temporal) correlation coeffient 
def corr_coef(X, Y):
    return np.mean((X - np.mean(X))*(Y - np.mean(Y)))/(np.std(X)*np.std(Y))

#recursive formulas for the mean and variance
def recursive_moments(X_np1, mu_n, sigma2_n, N):

    mu_np1 = mu_n + (X_np1 - mu_n)/(N+1)

    sigma2_np1 = sigma2_n + mu_n**2 - mu_np1**2 + (X_np1**2 - sigma2_n - mu_n**2)/(N+1)

    return mu_np1, sigma2_np1

###########################
# M A I N   P R O G R A M #
###########################

import numpy as np
import matplotlib.pyplot as plt
import os
import h5py
from scipy.integrate import simps
import sys
from drawnow import drawnow
from scipy import stats

plt.close('all')
plt.rcParams['image.cmap'] = 'seismic'

HOME = os.path.abspath(os.path.dirname(__file__))

plt.close('all')
plt.rcParams['image.cmap'] = 'seismic'

#number of gridpoints in 1D
I = 7
N = 2**I

#2D grid
h = 2*np.pi/N
axis = h*np.arange(1, N+1)
axis = np.linspace(0, 2.0*np.pi, N)
[x , y] = np.meshgrid(axis , axis)

#frequencies
k = np.fft.fftfreq(N)*N

kx = np.zeros([N, int(N/2+1)]) + 0.0j
ky = np.zeros([N, int(N/2+1)]) + 0.0j

for i in range(N):
    for j in range(int(N/2+1)):
        kx[i, j] = 1j*k[j]
        ky[i, j] = 1j*k[i]

k_squared = kx**2 + ky**2
k_squared_no_zero = np.copy(k_squared)
k_squared_no_zero[0,0] = 1.0

#cutoff in pseudospectral method
Ncutoff = N/3
Ncutoff_LF = 2**(I-1)/3 

#spectral filter
P = get_P(Ncutoff)
P_LF = get_P(Ncutoff_LF)
P_U = P - P_LF

#time scale
Omega = 7.292*10**-5
day = 24*60**2*Omega

#viscosities
decay_time_nu = 5.0
decay_time_mu = 90.0
nu = 1.0/(day*Ncutoff**2*decay_time_nu)
nu_LF = 1.0/(day*Ncutoff**2*decay_time_nu)
mu = 1.0/(day*decay_time_mu)

#start, end time, end time of data (training period), time step
dt = 0.01
t = 250.0*day
t_end = t + 250*day
n_steps = np.int(np.round((t_end-t)/dt))

#############
# USER KEYS #
#############

#simulation name
sim_ID = 'gen_tau'
#framerate of storing data, plotting results, computing correlations (1 = every integration time step)
store_frame_rate = 1
plot_frame_rate = np.floor(1.0*day/dt).astype('int')
corr_frame_rate = np.floor(0.25*day/dt).astype('int')
#length of data array
S = np.floor(n_steps/store_frame_rate).astype('int')

#Manual specification of flags 
state_store = True       #store the state at the end
restart = True           #restart from prev state
store = False            #store data
plot = True              #plot results while running, requires drawnow package
compute_ref = True       #compute the reference solution as well, keep at True, will automatically turn off in surrogate mode

eddy_forcing_type = 'tau_ortho'  

store_ID = sim_ID 
    
###############################
# SPECIFY WHICH DATA TO STORE #
###############################

#QoI to store, First letter in caps implies an NxN field, otherwise a scalar 

#TRAINING DATA SET
QoI = ['z_n_HF', 'e_n_HF', \
       'z_n_LF', 'e_n_LF', 'u_n_LF', 's_n_LF', 'v_n_LF', 'o_n_LF', \
       'sprime_n_LF', 'zprime_n_LF', \
       'tau_E', 'tau_Z', 't', 'r[0]', 'r[1]', 'dE_train', 'dZ_train']

#PREDICTION DATA SET
#QoI = ['z_n_LF', 'e_n_LF', 't']

Q = len(QoI)

#allocate memory
samples = {}

if store == True:
    samples['S'] = S
    samples['N'] = N
    
    for q in range(Q):
        
        #a field
        if QoI[q][0].isupper():
            samples[QoI[q]] = np.zeros([S, N, int(N/2+1)]) + 0.0j
        #a scalar
        else:
            samples[QoI[q]] = np.zeros(S)

#forcing term
F = 2**1.5*np.cos(5*x)*np.cos(5*y);
F_hat = np.fft.rfft2(F);

if restart == True:
    
    fname = HOME + '/restart/' + sim_ID + '_t_' + str(np.around(t/day,1)) + '.hdf5'
    
    #create HDF5 file
    h5f = h5py.File(fname, 'r')
    
    for key in h5f.keys():
        print(key)
        vars()[key] = h5f[key][:]
        
    h5f.close()

else:
    
    #initial condition
    w = np.sin(4.0*x)*np.sin(4.0*y) + 0.4*np.cos(3.0*x)*np.cos(3.0*y) + \
        0.3*np.cos(5.0*x)*np.cos(5.0*y) + 0.02*np.sin(x) + 0.02*np.cos(y)

    #initial Fourier coefficients at time n and n-1
    w_hat_n_HF = P*np.fft.rfft2(w)
    w_hat_nm1_HF = np.copy(w_hat_n_HF)
    
    w_hat_n_LF = P_LF*np.fft.rfft2(w)
    w_hat_nm1_LF = np.copy(w_hat_n_LF)
    
    #initial Fourier coefficients of the jacobian at time n and n-1
    VgradW_hat_n_HF = compute_VgradW_hat(w_hat_n_HF, P)
    VgradW_hat_nm1_HF = np.copy(VgradW_hat_n_HF)
    
    VgradW_hat_n_LF = compute_VgradW_hat(w_hat_n_LF, P_LF)
    VgradW_hat_nm1_LF = np.copy(VgradW_hat_n_LF)

#constant factor that appears in AB/BDI2 time stepping scheme   
norm_factor = 1.0/(3.0/(2.0*dt) - nu*k_squared + mu)        #for reference solution
norm_factor_LF = 1.0/(3.0/(2.0*dt) - nu_LF*k_squared + mu)  #for Low-Fidelity (LF) or resolved solution

#some counters
j = 0; j2 = 0; idx = 0;

T = []; E_LF = []; Z_LF = []; E_HF = []; Z_HF = []; W3_HF = []; W3_LF = []

fig = plt.figure(figsize=[12, 4])

#time loop
for n in range(n_steps):
    
    #orthogonal patterns
    psi_hat_n_prime = get_psi_hat_prime(w_hat_n_LF)
    w_hat_n_prime = get_w_hat_prime(w_hat_n_LF)

    if compute_ref == True:
        
        #solve for next time step
        w_hat_np1_HF, VgradW_hat_n_HF = get_w_hat_np1(w_hat_n_HF, w_hat_nm1_HF, VgradW_hat_nm1_HF, P, norm_factor)
        
        #exact eddy forcing
        EF_hat_nm1_exact = P_LF*VgradW_hat_nm1_HF - VgradW_hat_nm1_LF 
 
        #exact tau_E and tau_Z
        tau_E, tau_Z, dE, dZ = get_data_driven_tau_src_EZ(w_hat_n_LF, w_hat_n_HF, P_LF, 1.0, 1.0)
    
        #E & Z tracking eddy forcing
        EF_hat_n_ortho = -tau_E*psi_hat_n_prime - tau_Z*w_hat_n_prime 

        #reference energy and enstrophy
        #e_np1_HF, z_np1_HF, _ = get_EZS(P_LF*w_hat_np1_HF)
        e_n_HF, z_n_HF, w3_n_HF = get_EZS(P_LF*w_hat_n_HF)
        
    #######################################
    # covariates (conditioning variables) #
    #######################################
    e_n_LF, z_n_LF, w3_n_LF = get_EZS(w_hat_n_LF)
#    psi_n_LF = np.fft.irfft2(get_psi_hat(w_hat_n_LF))
#    u_n_LF = 0.5*simps(simps(psi_n_LF*F, axis), axis)/(2.0*np.pi)**2
#    w_n_LF = np.fft.irfft2(w_hat_n_LF)
#    v_n_LF = 0.5*simps(simps(w_n_LF*F, axis), axis)/(2.0*np.pi)**2
#    nabla2_w_n_LF = np.fft.irfft2(k_squared*w_hat_n_LF)
#    o_n_LF = 0.5*simps(simps(nabla2_w_n_LF*w_n_LF, axis), axis)/(2.0*np.pi)**2

    ###############################
    # generalized scalar tracking #
    ###############################
    
    psi_hat_n_LF = get_psi_hat(w_hat_n_LF)
    w_n_LF = np.fft.irfft2(w_hat_n_LF)
    w_hat_n_LF_squared = P_LF*np.fft.rfft2(w_n_LF**2)
    
    V_hat_1 = -psi_hat_n_LF
    V_hat_2 = w_hat_n_LF
    V_hat_3 = w_hat_n_LF_squared
    
    T_hat_11 = psi_hat_n_LF
    T_hat_12 = w_hat_n_LF
    T_hat_13 = w_hat_n_LF_squared
    
    T_hat_21 = w_hat_n_LF
    T_hat_22 = psi_hat_n_LF
    T_hat_23 = w_hat_n_LF_squared
    
    T_hat_31 = w_hat_n_LF_squared
    T_hat_32 = psi_hat_n_LF
    T_hat_33 = w_hat_n_LF    
    
    ##############################
    
    T_hat = np.zeros([3,3,N,int(N/2+1)]) + 0.0j
    T_hat[0,0] = T_hat_11
    T_hat[0,1] = T_hat_12
    T_hat[0,2] = T_hat_13

    T_hat[1,0] = T_hat_21
    T_hat[1,1] = T_hat_22
    T_hat[1,2] = T_hat_23

    T_hat[2,0] = T_hat_31
    T_hat[2,1] = T_hat_32
    T_hat[2,2] = T_hat_33
    
    V_hat = np.zeros([3,N,int(N/2+1)]) + 0.0j
    V_hat[0] = V_hat_1
    V_hat[1] = V_hat_2
    V_hat[2] = V_hat_3
    
    c_ij = compute_cij(T_hat, V_hat)
    c_12 = c_ij[0,0]; c_13 = c_ij[0,1]
    c_22 = c_ij[1,0]; c_23 = c_ij[1,1]
    c_32 = c_ij[2,0]; c_33 = c_ij[2,1]
    
    P_hat_1 = T_hat_11 - c_12*T_hat_12 - c_13*T_hat_13
    P_hat_2 = T_hat_21 - c_22*T_hat_22 - c_23*T_hat_23
    P_hat_3 = T_hat_31 - c_32*T_hat_32 - c_33*T_hat_33

#    src_E = compute_int(V_hat_1, P_hat_1)
#    src_Z = compute_int(V_hat_2, P_hat_2)
#    src_W3 = compute_int(V_hat_3, P_hat_3)

    dE = e_n_HF - e_n_LF
    dZ = z_n_HF - z_n_LF
    dW3 = w3_n_HF - w3_n_LF
    
#    tau_1 = np.tanh(dE/e_n_LF)*np.sign(src_E)
#    tau_2 = np.tanh(dZ/z_n_LF)*np.sign(src_Z)
#    tau_3 = 10**-4*np.tanh(dW3/w3_n_LF)*np.sign(src_W3)
    
    _tau_1 = dE/compute_int(V_hat_1, P_hat_1)
    _tau_2 = dZ/compute_int(V_hat_2, P_hat_2)
    _tau_3 = dW3/compute_int(V_hat_3, P_hat_3)
   
    #exact orthogonal pattern surrogate
    if eddy_forcing_type == 'tau_ortho':
        #EF_hat = -tau_E*psi_hat_n_prime - tau_Z*w_hat_n_prime
        EF_hat = -_tau_1*P_hat_1 - _tau_2*P_hat_2 - _tau_3*P_hat_3

    #unparameterized solution
    elif eddy_forcing_type == 'unparam':
        EF_hat = np.zeros([N, int(N/2+1)])
    #exact, full-field eddy forcing
    elif eddy_forcing_type == 'exact':
        EF_hat = EF_hat_nm1_exact
    else:
        print('No valid eddy_forcing_type selected')
        sys.exit()
   
    #########################
    #LF solve
    w_hat_np1_LF, VgradW_hat_n_LF = get_w_hat_np1(w_hat_n_LF, w_hat_nm1_LF, VgradW_hat_nm1_LF, P_LF, norm_factor_LF, EF_hat)

    t += dt
    j += 1
    j2 += 1    
    
    #plot solution every plot_frame_rate. Requires drawnow() package
    if j == plot_frame_rate and plot == True:
        j = 0

        e_n_HF, z_n_HF, w3_n_HF = get_EZS(P_LF*w_hat_n_HF)
        e_n_LF, z_n_LF, w3_n_LF = get_EZS(w_hat_n_LF)
        
        T.append(t)
        E_LF.append(e_n_LF); Z_LF.append(z_n_LF)
        E_HF.append(e_n_HF); Z_HF.append(z_n_HF)
        W3_HF.append(w3_n_HF); W3_LF.append(w3_n_LF)
        
        print('e_n_HF: %.4f' % e_n_HF, 'z_n_HF: %.4f' % z_n_HF, 'w3_n_HF: %.4f' % w3_n_HF)
        print('e_n_LF: %.4f' % e_n_LF, 'z_n_LF: %.4f' % z_n_LF, 'w3_n_LF: %.4f' % w3_n_LF)
        
        drawnow(draw)
        
    #store samples to dict
    if j2 == store_frame_rate and store == True:
        j2 = 0
        
        if np.mod(n, np.round(day/dt)) == 0:
            print('n = ', n, ' of ', n_steps)

        for qoi in QoI:
            samples[qoi][idx] = eval(qoi)

        idx += 1  

    #update variables
    if compute_ref == True: 
        w_hat_nm1_HF = np.copy(w_hat_n_HF)
        w_hat_n_HF = np.copy(w_hat_np1_HF)
        VgradW_hat_nm1_HF = np.copy(VgradW_hat_n_HF)

    w_hat_nm1_LF = np.copy(w_hat_n_LF)
    w_hat_n_LF = np.copy(w_hat_np1_LF)
    VgradW_hat_nm1_LF = np.copy(VgradW_hat_n_LF)
    
####################################

#store the state of the system to allow for a simulation restart at t > 0
if state_store == True:
    
    keys = ['w_hat_nm1_HF', 'w_hat_n_HF', 'VgradW_hat_nm1_HF', \
            'w_hat_nm1_LF', 'w_hat_n_LF', 'VgradW_hat_nm1_LF']
    
    if os.path.exists(HOME + '/restart') == False:
        os.makedirs(HOME + '/restart')
    
    #cPickle.dump(state, open(HOME + '/restart/' + sim_ID + '_t_' + str(np.around(t_end/day,1)) + '.pickle', 'w'))
    
    fname = HOME + '/restart/' + sim_ID + '_t_' + str(np.around(t_end/day,1)) + '.hdf5'
    
    #create HDF5 file
    h5f = h5py.File(fname, 'w')
    
    #store numpy sample arrays as individual datasets in the hdf5 file
    for key in keys:
        qoi = eval(key)
        h5f.create_dataset(key, data = qoi)
        
    h5f.close()   

####################################

#store the samples
if store == True:
    store_samples_hdf5() 

plt.show()