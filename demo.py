import matplotlib.pyplot as plt
import numpy as np
from main import *

plt.style.use('default')

# Simulation parameters
numCars = 50
roadLength = 100
vmax = 10
sigma = vmax/10
lanes = 3
numsteps = 200
p = 0.2
right_overtaking = True

# Run simulation
cars = Cars(numCars=numCars, roadLength=roadLength, lanes=lanes, vmax=vmax, sigma=sigma)
simulation = Simulation(cars)
simulation.run_animate(propagator=Propagator(p=p, right_overtaking=right_overtaking), numsteps=numsteps)