#!/usr/bin/env python3
# VITA, EPFL

from scipy.interpolate import UnivariateSpline
import math
import matplotlib.pyplot as plt
import numpy as np
import rospy

import os
import sys
abs_path_to_tools = "/home/cconejob/StudioProjects/Autonomous_driving_pipeline/src/loomo/scripts/tools"
sys.path.append(os.path.dirname(os.path.abspath(abs_path_to_tools)))
from tools import classconverter, classes, transformations, utilities

# Class for RRT Star planning
class CHUV_Planner:

    def __init__(self, mobile_robot, speed, N, dt_control):
        
        self.mobile_robot = mobile_robot
        self.prediction_list = []
        self.speed = speed
        self.dt_control = dt_control
        self.N = N
        self.x_limit = 1.0

    def path_planning(self, person_prediction):
        path = []
        t_max = 0.5
        person_array = np.array(person_prediction[0])
        x = person_array[0] - self.x_limit
        
        if x<0.0:
            x -= 0.5
        
        y = 0.0

        goal = [x, y]
        path = [[0.0, 0.0], goal]
        print("goal = " + str(goal))

        T_total = abs(x/self.speed)

        N = int(T_total/self.dt_control)

        if T_total > t_max:
            m = 0.0
            x_list = np.linspace(0.0, goal[0], num=N)
            y_list = m * x_list
            path = []
            for i in range(len(x_list)):
                path.append([x_list[i], y_list[i]])

            print("path1: " + str(path))


        mpc_path = utilities.MPC_Planner_restrictions_CHUV(self.mobile_robot, path, self.speed, self.dt_control)[:N+2]

        print("path2: " + str(mpc_path))

        if len(mpc_path)<self.N:

            return [[0.0, 0.0, 0.0, 0.0], ] * 2 * self.N

        return mpc_path



if __name__ == "__main__":

    try:
        loomo = MobileRobot(0.5, 0.5)
        chuv = CHUV_Planner(loomo, 0.25, 0.6)
        path = chuv.path_planning([[[0,2],[1,2],[2,2],[3,2],[4,2]],[[3,2],[4,2],[5,2]]])
        print(path)

    except rospy.ROSInterruptException:
        pass