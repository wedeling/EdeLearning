import numpy as np
import os, pickle
from .Layer import Layer

class ANN:

    def __init__(self, X = np.zeros(1), y = np.zeros(0), alpha = 0.001, decay_rate = 1.0, decay_step = 10**4, beta1 = 0.9, beta2 = 0.999, lamb = 0.0, \
                 param_specific_learn_rate = False, loss = 'squared', activation = 'tanh', n_layers = 2, n_neurons = 16, \
                 bias = True, neuron_based_compute = False, batch_size = 1, save = True, name='ANN'):

        #the features
        self.X = X
        
        #number of training data points
        self.n_train = X.shape[0]
        
        #the training outputs
        self.y = y
        
        #number of input nodes
        try:
            self.n_in = X.shape[1]
        except IndexError:
            self.n_in = 1
        
        #number of layers (hidden + output)
        self.n_layers = n_layers

        #number of neurons in a hidden layer
        self.n_neurons = n_neurons

        #number of output neurons
        self.n_out = 1
        
        #use bias neurons
        self.bias = bias
        
        #loss function type
        self.loss = loss

        #training rate
        self.alpha = alpha

        #the rate of decay abd decay step for alpha
        self.decay_rate = decay_rate        
        self.decay_step = decay_step

        #momentum parameter
        self.beta1 = beta1
        
        #squared gradient parameter
        self.beta2 = beta2
        
        #penalty parameter
        self.lamb = lamb
        
        #use parameter specific learning rate
        self.param_specific_learn_rate = param_specific_learn_rate

        #activation function of the hidden layers
        self.activation = activation
        
        #save the neural network after training
        self.save = save
        self.name = name
        
        #determines where to compute the neuron outputs and gradients 
        #True: locally at the neuron, False: on the Layer level in one shot via linear algebra)
        self.neuron_based_compute = neuron_based_compute

        #size of the mini batch used in stochastic gradient descent
        self.batch_size = batch_size

        self.loss_vals = []
        self.mean_loss_vals = []

        self.layers = []
        
        #add the input layer
        self.layers.append(Layer(self.n_in, 0, self.n_layers, 'linear', \
                                 self.loss, self.bias, batch_size = batch_size, \
                                 neuron_based_compute=neuron_based_compute)) 
        
        #add the hidden layers
        for r in range(1, self.n_layers):
            self.layers.append(Layer(self.n_neurons, r, self.n_layers, self.activation, \
                                     self.loss, self.bias, batch_size=batch_size, \
                                     neuron_based_compute=neuron_based_compute))
        
        #add the output layer
        self.layers.append(Layer(self.n_out, self.n_layers, self.n_layers, \
                                 'linear', self.loss, batch_size=batch_size, \
                                 neuron_based_compute = neuron_based_compute))
        
        self.connect_layers()
   
    #connect each layer in the NN with its previous and the next      
    def connect_layers(self):
        
        self.layers[0].meet_the_neighbors(None, self.layers[1])
        self.layers[-1].meet_the_neighbors(self.layers[-2], None)
        
        for i in range(1, self.n_layers):
            self.layers[i].meet_the_neighbors(self.layers[i-1], self.layers[i+1])
    
    #run the network forward
    def feed_forward(self, X_i, batch_size = 1):
        
        X_i = X_i.reshape([batch_size, self.n_in])
               
        #set the features at the output of in the input layer
        if self.bias == False:
            self.layers[0].h = X_i
        else:
            self.layers[0].h = np.ones([self.n_in + 1, batch_size])
            self.layers[0].h[0:self.n_in, :] = X_i.T
                    
        for i in range(1, self.n_layers+1):
            if self.neuron_based_compute:
                #compute the output locally in each neuron
                self.layers[i].compute_output_local()
            else:
                #compute the output on the layer lavel, using matric-vector multiplication for a 
                self.layers[i].compute_output(batch_size)
            
        return self.layers[-1].h
        
    def back_prop(self, y_i):

        #start back propagation over hidden layers, starting with layer before output layer
        for i in range(self.n_layers, 0, -1):
            self.layers[i].back_prop(y_i)
        
    #update step of the weights
    def batch(self, X_i, y_i, alpha, beta1, beta2, t):
        
        self.feed_forward(X_i, self.batch_size)
        self.back_prop(y_i)
        
        for r in range(1, self.n_layers+1):

            layer_r = self.layers[r]
            
            #momentum 
            layer_r.V = beta1*layer_r.V + (1.0 - beta1)*layer_r.L_grad_W
            
            #moving average of squared gradient magnitude
            layer_r.A = beta2*layer_r.A + (1.0 - beta2)*layer_r.L_grad_W**2
            
            #gradient descent update step
            if self.param_specific_learn_rate == False:
                #Lamb = self.lamb*np.ones([self.layers[i].W.shape[0], self.layers[i].W.shape[1]])
                #Lamb[-1, :] = 0.0
                #self.layers[i].W = (1.0 - alpha*Lamb)*self.layers[i].W - alpha*self.layers[i].V    #same alpha for all weights
                layer_r.W = layer_r.W - alpha*layer_r.V    #same alpha for all weights
            else:
                #RMSProp
                alpha_scaled = alpha/(np.sqrt(layer_r.A + 1e-8))
                #Adam
                #alpha_t = alpha*np.sqrt(1.0 - beta2**t)/(1.0 - beta1**t)
                #alpha_scaled = alpha_t/(np.sqrt(layer_r.A + + 1e-8))
                layer_r.W = layer_r.W - alpha_scaled*layer_r.V
            
            #Nesterov momentum
            #layer_r[i].W += -alpha*beta1*layer_r.V
    
    #train the neural network        
    def train(self, n_epoch, store_loss = False, check_derivative = False):
        
        for i in range(n_epoch):

            #select a random training instance (X, y)
            rand_idx = np.random.randint(0, self.n_train, self.batch_size)
            
            #compute learning rate
            alpha = self.alpha*self.decay_rate**(np.int(i/self.decay_step))

            #run the batch
            self.batch(self.X[rand_idx], self.y[rand_idx], alpha, self.beta1, self.beta2, i+1)
            
            if check_derivative == True and np.mod(i, 1000) == 0:
                self.check_derivative(self.X[rand_idx], self.y[rand_idx], 10)
            
            #store the loss value 
            if store_loss == True:
                l = 0.0
                for k in range(self.n_out):
                    if self.neuron_based_compute:
                        l += self.layers[-1].neurons[k].L_i
                    else:
                        l += self.layers[-1].L_i
                self.loss_vals.append(l)
                
                if np.mod(i, 1000) == 0:
                    self.mean_loss_vals.append(np.mean(self.loss_vals[-1000:]))
                    print('Batch', i, 'learning rate', alpha ,'loss:', self.mean_loss_vals[-1])
                    
        if self.save == True:
            self.save_ANN()

    #save using pickle (maybe too slow for very large ANNs?)
    def save_ANN(self):
        
        #absolute path
        home = os.path.abspath(os.path.dirname(__file__))
        path = home + '/../saved_networks/'
        
        print('Saving ANN to', path + '/' + self.name + '.pickle')
        
        if os.path.exists(path) == False:
            os.makedirs(path)
        
        file = open(path + self.name + '.pickle', 'wb')
        pickle.dump(self.__dict__, file)
        file.close()

    #load using pickle
    def load_ANN(self):

        #absolute path
        home = os.path.abspath(os.path.dirname(__file__))
        path = home + '/../saved_networks/'

        print('Loading ANN from', path + '/' + self.name + '.pickle')

        file = open(path + self.name + '.pickle', 'rb')
        self.__dict__ = pickle.load(file)
        file.close()

    #compare a random back propagation derivative with a finite-difference approximation
    def check_derivative(self, X_i, y_i, n_checks):
        
        eps = 1e-6
        print('==============================================')
        print('Performing derivative check of', n_checks, 'randomly selected neurons.')
        
        for i in range(n_checks):
            
            #'align' the netwrok with the newly computed gradient and compute the loss function
            self.feed_forward(X_i)
            self.layers[-1].neurons[0].compute_loss(y_i)            
            L_i_old = self.layers[-1].neurons[0].L_i

            #select a random neuron which has a nonzero gradient            
            L_grad_W_old = 0.0
            while L_grad_W_old == 0.0:

                #select a random neuron
                layer_idx = np.random.randint(1, self.n_layers+1)
                neuron_idx = np.random.randint(self.layers[layer_idx].n_neurons)
                weight_idx = np.random.randint(self.layers[layer_idx-1].n_neurons)
             
                #the unperturbed weight and gradient
                w_old = self.layers[layer_idx].W[weight_idx, neuron_idx]
                L_grad_W_old = self.layers[layer_idx].L_grad_W[weight_idx, neuron_idx]
            
            #perturb weight
            self.layers[layer_idx].W[weight_idx, neuron_idx] += eps
            
            #run the netwrok forward and compute loss
            self.feed_forward(X_i)
            self.layers[-1].neurons[0].compute_loss(y_i)            
            L_i_new = self.layers[-1].neurons[0].L_i
                        
            #simple FD approximation of the gradient
            L_grad_W_FD = (L_i_new - L_i_old)/eps
  
            print('Back-propogation gradient:', L_grad_W_old)
            print('FD approximation gradient:', L_grad_W_FD)
           
            #reset weights and network
            self.layers[layer_idx].W[weight_idx, neuron_idx] = w_old
            self.feed_forward(X_i)

        print('==============================================')
      
    #compute the number of misclassifications
    def compute_misclass(self):
        
        n_misclass = 0.0
        
        for i in range(self.n_train):
            y_hat_i = np.sign(self.feed_forward(self.X[i]))
            
            if y_hat_i != self.y[i]:
                n_misclass += 1
                
        print('Number of misclassifications = ', n_misclass)
        
    #return the number of weights
    def get_n_weights(self):
        
        n_weights = 0
        
        for i in range(1, self.n_layers+1):
            n_weights += self.layers[i].W.size
            
        print('This neural network has', n_weights, 'weights.')
