import math
import matplotlib.pyplot as plt
from matplotlib import animation
import numpy.random as rng
import numpy as np


class Cars:
    """ Class for storing the state of the cars on the road """
    def __init__(self, numCars=5, roadLength=50, v0=0, lanes=3, vmax=5, sigma=1):
        """
        Initializes the traffic simulation with a specified number of cars, road length, initial velocity, number of lanes, maximum velocity, and velocity randomness.
        Parameters:
            numCars (int): Number of cars in the simulation (default: 5).
            roadLength (int): Length of the road (default: 50).
            v0 (int): Initial velocity of all cars (default: 0).
            lanes (int): Number of lanes on the road (default: 3).
            vmax (int): Mean maximum velocity for cars (default: 5).
            sigma (float): Standard deviation for randomizing car maximum velocities (default: 1).
        Attributes:
            vmax (np.ndarray): Array of randomized maximum velocities for each car.
            numCars (int): Number of cars in the simulation.
            roadLength (int): Length of the road.
            lanes (int): Number of lanes on the road.
            t (int): Simulation time step, initialized to 0.
            x (list): List of car positions.
            v (list): List of car velocities.
            c (list): List of car colors (or identifiers).
            l (list): List of lane assignments for each car.
        """

        randomized_velocities = np.random.normal(vmax, sigma, numCars)
        self.vmax = (np.rint(randomized_velocities)).astype(int)
        self.numCars = numCars
        self.roadLength = roadLength
        self.lanes = lanes
        self.t  = 0
        self.x  = []
        self.v  = []
        self.c  = [] # color of cars
        self.l = []
        for i in range(numCars):
            self.x.append(i)
            self.v.append(v0)
            self.c.append(i)
            self.l.append(i%lanes)

    def distance_forward(self, i):
        """ Returns the distance to the next car in front of car i """
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
            return 10**4

    def distance_left(self, i):
        """ Returns the distance to the next car in the left lane """
        x = np.array(self.x)
        l = np.array(self.l)
        my_pos = self.x[i]
        my_lane = self.l[i]

        x = x[l==my_lane+1]
        x = x-my_pos
        
        if len(x) > 0:
            return min(x%self.roadLength)
        else:
            return 10**4
        
    def distance_right(self, i):
        """ Returns the distance to the next car in the right lane """
        x = np.array(self.x)
        l = np.array(self.l)
        my_pos = self.x[i]
        my_lane = self.l[i]

        x = x[l==my_lane-1]
        x = x-my_pos
        
        if len(x) > 0:
            return min(x%self.roadLength)
        else:
            return 10**4

    def distance_left_back(self, i):
        """ Returns the distance to the next car in the left lane behind car i """
        x = np.array(self.x)
        l = np.array(self.l)
        my_pos = self.x[i]
        my_lane = self.l[i]

        x = x[l==my_lane+1]
        x = (x- my_pos)%self.roadLength - self.roadLength
        
        if len(x) > 0:
            return abs(max(x))
        else:
            return 10**4

    def distance_right_back(self, i):
        """ Returns the distance to the next car in the right lane behind car i """
        x = np.array(self.x)
        l = np.array(self.l)
        my_pos = self.x[i]
        my_lane = self.l[i]

        x = x[l==my_lane-1]
        x = (x - my_pos)%self.roadLength - self.roadLength
        
        if len(x) > 0:
            return abs(max(x))
        else:
            return 10**4

    def velocity_left_back(self, i):
        """ Returns the velocity of the next car in the left lane behind car i """
        x = np.array(self.x)
        l = np.array(self.l)
        v = np.array(self.v)
        my_pos = self.x[i]
        my_lane = self.l[i]

        v = v[l==my_lane+1]
        x = x[l==my_lane+1]
        if len(x) > 0:
            idx = np.argmax((x - my_pos)%self.roadLength)
            return v[idx]
        else:
            return -1
        
    def velocity_right_back(self, i):
        """ Returns the velocity of the next car in the right lane behind car i """
        x = np.array(self.x)
        l = np.array(self.l)
        v = np.array(self.v)
        my_pos = self.x[i]
        my_lane = self.l[i]

        v = v[l==my_lane-1]
        x = x[l==my_lane-1]
        if len(x) > 0:
            idx = np.argmax((x - my_pos)%self.roadLength)
            return v[idx]
        else:
            return -1 


class Observables:
    """Class for storing observables."""
    def __init__(self):
        self.time = []     
        self.flowrate = [] 

        self.position = []
        self.velocity = []
        self.lanes = []
        

class BasePropagator:
    """Base class for propagators."""
    def __init__(self):
        return
        
    def propagate(self, cars, obs):
        """ Perform a single integration step """
        fr = self.timestep(cars, obs)

        # Append observables to their lists
        obs.time.append(cars.t)
        obs.flowrate.append(fr)

        # Tillagt av mig
        obs.position.append(cars.x.copy())
        obs.velocity.append(cars.v.copy())
        obs.lanes.append(cars.l.copy())

              
    def timestep(self, cars, obs):
        """Virtual method: implemented by the child classes """
        pass


class Propagator(BasePropagator):
    """Custom propagator implementing a cellular automaton model with lane changes."""
    def __init__(self, p, right_overtaking=True):
        BasePropagator.__init__(self)
        self.p = p
        self.right_overtaking = right_overtaking

    def timestep(self, cars, obs):
        """Perform a single integration step for the cellular automaton model with lane changes."""
        cars.t += 1
        
        # Lane change
        if cars.lanes >= 2:
            desired_changes = [0]*cars.numCars

            # Calculate desired lane changes for each car
            for i in range(cars.numCars):
                distance_forward = cars.distance_forward(i)
                distance_left = cars.distance_left(i)
                distance_right = cars.distance_right(i)

                if distance_forward < cars.vmax[i] and distance_left >= distance_forward and cars.l[i] < cars.lanes - 1: 
                    desired_changes[i] = 1

                elif distance_forward > cars.vmax[i] and distance_right > cars.vmax[i] and cars.l[i] >= 1:
                    desired_changes[i] = -1

                elif distance_right > distance_forward and np.random.rand() > 0.05:
                    desired_changes[i] = -1


            # Perform lane changes if allowed
            for i in range(cars.numCars):
                if desired_changes[i] == 1 and 0 <= cars.l[i] + desired_changes[i] <= cars.lanes - 1:
                    if cars.distance_left_back(i) > cars.velocity_left_back(i): #>= eller >??
                        cars.l[i] += desired_changes[i]
                
                if desired_changes[i] == -1 and 0 <= cars.l[i] + desired_changes[i] <= cars.lanes - 1:
                    if cars.distance_right_back(i) > cars.velocity_right_back(i): #>= eller >??
                        cars.l[i] += desired_changes[i]

        # Implement the traffic rules for the celular automaton model
        # 1) Increase velocity if v < vmax
        for i in range(cars.numCars):
            if cars.v[i] < cars.vmax[i]:
                cars.v[i] += 1

        # 2) Decrease velocity if v >= d and forbid right side overtaking
        if not self.right_overtaking:
            for i in range(cars.numCars):
                distance_forward = cars.distance_forward(i)
                distance_left = cars.distance_left(i)
                if cars.v[i] >= distance_forward or cars.v[i] > distance_left:
                    cars.v[i] = min(distance_forward - 1, distance_left)

        # 2) Decrease velocity if v >= d and allow right side overtaking
        if self.right_overtaking:    
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
            cars.x[i] = (cars.x[i] + (cars.v[i]))%cars.roadLength
        
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
    """Class for running the simulation."""
    def reset(self, cars=Cars()):
        self.cars = cars
        self.obs = Observables()

    def __init__(self, cars=Cars()):
        self.reset(cars)

    # Run without displaying any animation (fast)
    def run(self,
            propagator,
            numsteps=200,           # Final time
            title="simulation",     # Name of output file and title shown at the top
            ):
        
        # Append observables to their lists
        self.obs.time.append(self.cars.t)
        self.obs.flowrate.append(0)

        # Tillagt av mig
        self.obs.position.append(self.cars.x.copy())
        self.obs.velocity.append(self.cars.v.copy())

        for it in range(numsteps):
            propagator.propagate(self.cars, self.obs)


    # Run while displaying the animation of bunch of cars going in circe (slow)
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
                                       frames=numframes, interval=600, blit=True, repeat=False)
        plt.show()


def main() :
    cars = Cars(numCars = 70, roadLength=200, lanes=3, vmax=10, sigma=2)

    # Create the simulation object for your cars instance:
    simulation = Simulation(cars)

    # simulation.run_animate(propagator=ConstantPropagator())
    simulation.run_animate(propagator=Propagator(p=0.2, right_overtaking=True), numsteps=500)

    data = simulation.obs

    plt.plot(data.time, data.flowrate)
    plt.show()


if __name__ == "__main__" :
    main()

