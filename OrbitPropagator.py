"""
Orbit propagator class
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import ode
from mpl_toolkits.mplot3d import Axes3D

import Planetary_Data as pd
import tools as t

class OrbitPropagator:
    '''
    __init__
    class constructor fn, initializes state
    state0 initial state
    tspan simulation time span
    dt simulation time step 
    coes feed Keplerian orbital parameters (auto False)
    deg use degrees (True) or rads (False) (auto True)
    auto_orbit_prop automatically propagate orbit (auto True)
    cb central body determination (auto pd.earth)
    '''
    def __init__(self, state0, tspan, dt, coes=False, deg=True, 
                 auto_orbit_prop=True, cb=pd.earth):
        if coes:
            self.r0, self.v0 = t.coes2rv(state0, deg=deg, mu=cb['mu'])
        else:
            self.r0 = state0[:3]
            self.r0 = state0[3:]
        
        self.y0 = self.r0.tolist() + self.v0.tolist()
        self.tspan = tspan
        self.dt = dt
        self.cb = cb
        
        #find total num of steps
        self.n_steps = int(np.ceil(self.tspan/self.dt)) 
        
        #initialize arrays
        self.ys = np.zeros((self.n_steps,6)) 
        self.ts = np.zeros((self.n_steps, 1))
        
        #initial conditions
        self.ts[0] = 0
        self.ys[0,:] = self.y0
        self.step = 1
        
        #find initial true anomaly
        self.ta = np.zeros((self.n_steps, 1))
        self.ta[0] = t.true_anomaly_r(self.y0)
        
        #initiate the solver
        self.solver = ode(self.diffy_q)
        self.solver.set_integrator('lsoda')
        self.solver.set_initial_value(self.y0, 0)
        
        #propagate the orbit if no other stimulus
        if auto_orbit_prop:
            self.propagate_orbit()
        
    def propagate_orbit(self):
        #propagate orbit
        while self.solver.successful and self.step < self.n_steps:
            self.solver.integrate(self.solver.t + self.dt)
            self.ts[self.step] = self.solver.t
            self.ys[self.step] = self.solver.y
            self.ta[self.step] = t.true_anomaly_r(self.ys[self.step])
            self.step += 1
            
        #get all the radius values
        self.rs = self.ys[:,:3] 
        self.vs = self.ys[:,3:]
        
    def diffy_q(self, t, y):
        #unpack state
        rx, ry, rz, vx, vy, vz = y
        
        #define radius and velocity array as np vector
        r=np.array([rx,ry,rz])
        
        #norm of radius vector
        norm_r=np.linalg.norm(r)
        
        #define 2-body accel
        ax,ay,az=-r*self.cb['mu']/norm_r**3
        
        #Pass derivatives of the state
        return [vx, vy, vz, ax, ay, az]
    
    def plot_3d(self, show_plot=False, save_plot=False, title='Trajectory Plot'):
        #Set dark background
        plt.style.use('dark_background')
        
        #define fig object
        fig = plt.figure(figsize=(16,8))
        ax = fig.add_subplot(111,projection='3d')
        
        # plot trajectory
        ax.plot(self.rs[:,0],self.rs[:,1],self.rs[:,2],'b', label='Trajectory')
        ax.plot(self.rs[0,0], self.rs[0,1], self.rs[0,2], marker='o',
                color='w', label='Initial Position')
        
        # plot central body
        _u,_v = np.mgrid[0:2*np.pi:20j,0:np.pi:10j]
        _x = self.cb['radius']*np.cos(_u)*np.sin(_v)
        _y = self.cb['radius']*np.sin(_u)*np.sin(_v)
        _z = self.cb['radius']*np.cos(_v)
        ax.plot_surface(_x, _y, _z, cmap='Blues')
        
        #plot the x, y, z vectors
        l = self.cb['radius'] * 2
        x,y,z=[[0,0,0],[0,0,0],[0,0,0]]
        u,v,w=[[l,0,0],[0,l,0],[0,0,l]]
        ax.quiver(x,y,z,u,v,w,color='k')
        
        max_val=np.max(np.abs(self.rs))
        
        ax.set_xlim([-max_val, max_val])
        ax.set_ylim([-max_val, max_val])
        ax.set_zlim([-max_val, max_val])
        
        ax.set_xlabel(['X (km)'])
        ax.set_ylabel(['Y (km)'])
        ax.set_zlabel(['Z (km)'])
        
        ax.set_aspect('equal')
        
        ax.set_title(title)
        plt.legend()
        
        if show_plot:
            plt.show()
        if save_plot:
            plt.savefig(title+'.png', dpi=300)
