import math
import matplotlib.pyplot as plt
from matplotlib import animation
import numpy.random as rng
import numpy as np


class Cars:
    def __init__(self, numCars=5, roadLength=50, v0=1, lanes=3, vmax=5, sigma=1):
        self.vmax = np.random.normal(vmax, sigma, numCars)
        self.numCars = numCars
        self.roadLength = roadLength
        self.lanes = lanes
        self.t  = 0 
        self.x  = [] # position
        self.v  = [] # velocity
        self.c  = [] # color
        self.l = [] # lane
        for i in range(numCars):
            self.x.append(2*i)        # the position of the cars on the road
            self.v.append(v0)       # the speed of the cars
            self.c.append(i)        # the color of the cars (for drawing)
            self.l.append(0)        # all cars initially start in lane 0 (rightmost lane)

    def distance_forward(self, i):
        #if i <= self.numCars - 2:
        #    return self.x[i+1] - self.x[i]
        #else:
        #    return self.x[0] - self.x[-1] + self.roadLength
        x = np.array(self.x)
        l = np.array(self.l)
        my_pos = self.x[i]
        my_lane = self.l[i]

        x = x[l==my_lane]
        x = x-my_pos
        x = x[x != 0]

        if len(x) > 0:
            return min(x%self.roadLength)
        else:
            return 10**3


    def distance_left(self, i):
        x = np.array(self.x)
        l = np.array(self.l)
        my_pos = self.x[i]
        my_lane = self.l[i]

        x = x[l==my_lane+1]
        x = x-my_pos
        
        if len(x) > 0:
            return min(x%self.roadLength)
        else:
            return 10**3
            

    def distance_right(self, i):
        x = np.array(self.x)
        l = np.array(self.l)
        my_pos = self.x[i]
        my_lane = self.l[i]

        x = x[l==my_lane-1]
        x = x-my_pos
        
        if len(x) > 0:
            return min(x%self.roadLength)
        else:
            return 10**3


    def distance_left_back(self, i):
        x = np.array(self.x)
        l = np.array(self.l)
        my_pos = self.x[i]
        my_lane = self.l[i]

        x = x[l==my_lane+1]
        x = (x- my_pos)%self.roadLength - self.roadLength
        
        if len(x) > 0:
            return abs(max(x))
        else:
            return 10**3


    def distance_right_back(self, i):
        x = np.array(self.x)
        l = np.array(self.l)
        my_pos = self.x[i]
        my_lane = self.l[i]

        x = x[l==my_lane-1]
        x = (x - my_pos)%self.roadLength - self.roadLength
        
        if len(x) > 0:
            return abs(max(x))
        else:
            return 10**3


    def velocity_right_back(self, i):
        x = np.array(self.x)
        l = np.array(self.l)
        v = np.array(self.v)
        my_pos = self.x[i]
        my_lane = self.l[i]

        v = v[l==my_lane-1]
        x = x[l==my_lane-1]
        if len(x) > 0:
            idx = np.argmax((x -  my_pos)%self.roadLength)
            return v[idx]
        else:
            return 0 


    def velocity_left_back(self, i):
        x = np.array(self.x)
        l = np.array(self.l)
        v = np.array(self.v)
        my_pos = self.x[i]
        my_lane = self.l[i]

        v = v[l==my_lane+1]
        x = x[l==my_lane+1]
        if len(x) > 0:
            idx = np.argmax((x -  my_pos)%self.roadLength)
            return v[idx]
        else:
            return 0

class Observables:

    """ Class for storing observables """

    def __init__(self):
        self.time = []          # list to store time
        self.flowrate = []      # list to store the flow rate

        # Tillagt av mig
        self.position = []
        self.velocity = []
        

class BasePropagator:

    def __init__(self):
        return
        
    def propagate(self, cars, obs):

        """ Perform a single integration step """
        
        fr = self.timestep(cars, obs)

        # Append observables to their lists
        obs.time.append(cars.t)
        obs.flowrate.append(fr)  # CHANGE!

        # Tillagt av mig
        obs.position.append(cars.x.copy())
        obs.velocity.append(cars.v.copy())

              
    def timestep(self, cars, obs):

        """ Virtual method: implemented by the child classes """
        
        pass


class MyPropagator(BasePropagator) :

    def __init__(self, p):
        BasePropagator.__init__(self)
        self.p = p

    def timestep(self, cars, obs):
        cars.t += 1
        
        # Lane change
        if cars.lanes >= 2:
            desired_changes = [0]*cars.numCars

            # Calculate desired lane changes
            for i in range(cars.numCars):
                distance_forward = cars.distance_forward(i)
                distance_left = cars.distance_left(i)
                distance_right = cars.distance_right(i)

                if distance_forward < cars.vmax[i] and distance_left >= distance_forward: 
                    desired_changes[i] = 1

                elif distance_forward > cars.vmax[i] and distance_right > cars.vmax[i]:
                    desired_changes[i] = -1

            # Perform lane changes if allowed
            for i in range(cars.numCars):
                if desired_changes[i] == 1 and 0 <= cars.l[i] + desired_changes[i] <= cars.lanes - 1:
                    if cars.distance_left_back(i) >= cars.velocity_left_back(i):
                        cars.l[i] += desired_changes[i]
                
                if desired_changes[i] == -1 and 0 <= cars.l[i] + desired_changes[i] <= cars.lanes - 1:
                    if cars.distance_right_back(i) >= cars.velocity_right_back(i):
                        cars.l[i] += desired_changes[i]

            # Forbid overtakning on the right
            """
            for i in range(cars.numCars):
                distance_left = cars.distance_left(i)
                if cars.v[i] > distance_left:
                    cars.v[i] = distance_left"""

        # Velocity change
        # 1) Increase velocity if v < vmax
        for i in range(cars.numCars):
            if cars.v[i] < cars.vmax[i]:
                cars.v[i] += 1

        # 2) Decrease velocity if v >= d
        for i in range(cars.numCars):
            distance_forward = cars.distance_forward(i)
            if cars.v[i] >= distance_forward:
                cars.v[i] = distance_forward - 1

        # 3) Randomly reduce velocity 
        for i in range(cars.numCars):
            if np.random.rand() < self.p and cars.v[i] > 0:
                cars.v[i] -= 1
    
        # 4) Update positions
        for i in range(cars.numCars):
            cars.x[i] += cars.v[i]
        
        # Calculate and return flow rate
        fr = sum(cars.v)/cars.roadLength

        return fr


def draw_cars(cars, cars_drawing):

    """ Used later on to generate the animation """
    theta = []
    r     = []

    #for position in cars.x:
    for position, lane in zip(cars.x, cars.l):
        # Convert to radians for plotting  only (do not use radians for the simulation!)
        theta.append(position * 2 * math.pi / cars.roadLength)
        #r.append(1)
        r.append(1 - lane*0.1)
    return cars_drawing.scatter(theta, r, c=cars.c, cmap='hsv')


def animate(framenr, cars, obs, propagator, road_drawing, stepsperframe):

    """ Animation function which integrates a few steps and return a drawing """

    for it in range(stepsperframe):
        propagator.propagate(cars, obs)

    return draw_cars(cars, road_drawing),


class Simulation:

    def reset(self, cars=Cars()) :
        self.cars = cars
        self.obs = Observables()

    def __init__(self, cars=Cars()) :
        self.reset(cars)

    # Run without displaying any animation (fast)
    def run(self,
            propagator,
            numsteps=200,           # final time
            title="simulation",     # Name of output file and title shown at the top
            ):
        
        # Append observables to their lists
        self.obs.time.append(self.cars.t)
        self.obs.flowrate.append(0)  # CHANGE!

        # Tillagt av mig
        self.obs.position.append(self.cars.x.copy())
        self.obs.velocity.append(self.cars.v.copy())

        for it in range(numsteps):
            propagator.propagate(self.cars, self.obs)

        #self.plot_observables(title)

    # Run while displaying the animation of bunch of cars going in circe (slow-ish)
    def run_animate(self,
            propagator,
            numsteps=200,           # Final time
            stepsperframe=1,        # How many integration steps between visualising frames
            title="simulation",     # Name of output file and title shown at the top
            ):

        numframes = int(numsteps / stepsperframe)

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='polar')
        ax.axis('off')
        # Call the animator, blit=False means re-draw everything
        anim = animation.FuncAnimation(plt.gcf(), animate,  # init_func=init,
                                       fargs=[self.cars,self.obs,propagator,ax,stepsperframe],
                                       frames=numframes, interval=500, blit=True, repeat=False)
        plt.show()

        # If you experience problems visualizing the animation and/or
        # the following figures comment out the next line 
        # plt.waitforbuttonpress(30)
    

# It's good practice to encapsulate the script execution in 
# a main() function (e.g. for profiling reasons)
def main() :

    # Here you can define one or more instances of cars, with possibly different parameters, 
    # and pass them to the simulator 

    # Be sure you are passing the correct initial conditions!

    cars = Cars(numCars = 10, roadLength=100, lanes=3, vmax=10, sigma=1)

    # Create the simulation object for your cars instance:
    simulation = Simulation(cars)

    # simulation.run_animate(propagator=ConstantPropagator())
    simulation.run(propagator=MyPropagator(p=0.2))

    data = simulation.obs

    plt.plot(data.time, data.flowrate)
    plt.show()




# Calling 'main()' if the script is executed.
# If the script is instead just imported, main is not called (this can be useful if you want to
# write another script importing and utilizing the functions and classes defined in this one)
if __name__ == "__main__" :
    main()

