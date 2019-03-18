import numpy as np
from .Layer import Layer

class ANN:

    def __init__(self, X, y, alpha = 1.0):

        #the features
        self.X = X
        
        #the training outputs
        self.y = y
        
        #number of input nodes
        try:
            self.n_in = X.shape[1]
        except IndexError:
            self.n_in = 1
        
        #number of layers (hidden + output)
        self.n_layers = 3

        #number of neurons in a hidden layer
        self.n_neurons_hid = 10

        #number of output neurons
        self.n_out = 1
        
        #loss function type
        self.loss = 'perceptron_crit'

        self.layers = []
        
        #add the input layer
        self.layers.append(Layer(self.n_in, 0, self.n_layers, 'linear', self.loss)) 
        
        #add the hidden layers
        for r in range(1, self.n_layers):
            self.layers.append(Layer(self.n_neurons_hid, r, self.n_layers, 'relu', self.loss))
        
        #add the output layer
        self.layers.append(Layer(self.n_out, self.n_layers, self.n_layers, 'linear', self.loss))
        
        self.connect_layers()
   
    #connect each layer in the NN with its previous and the next      
    def connect_layers(self):
        
        self.layers[0].meet_the_neighbors(None, self.layers[1])
        self.layers[-1].meet_the_neighbors(self.layers[-2], None)
        
        for i in range(1, self.n_layers):
            self.layers[i].meet_the_neighbors(self.layers[i-1], self.layers[i+1])
    
    #run the network forward
    def feed_forward(self, X):
        
        #set the features at the output of in the input layer
        self.layers[0].h = X
        
        for i in range(1, self.n_layers+1):
            self.layers[i].compute_output()
            
        return self.layers[-1].h
    
    def back_prop(self, y_i):

        #start back propagation over hidden layers, starting with layer before output layer
        for i in range(self.n_layers, 0, -1):
            self.layers[i].back_prop(y_i)