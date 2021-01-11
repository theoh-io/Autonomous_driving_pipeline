#!/usr/bin/env python
# VITA, EPFL
import rospy
from msg_types.msg import Position, PositionArray, TrajectoryArray, StateArray, State
import matplotlib.pyplot as plt
import numpy as np

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath('/home/cconejob/StudioProjects/socket-loomo/src/perception/scripts/tools')))
from tools import classconverter, transformations, utilities


def callback_goal(data):

    global goal_local, goal_global, x0

    goal_local = classconverter.Position2list(data)
    goal_global = transformations.Local_to_Global(x0, [goal_local], True)[0]


def callback_planning_local(data):

    global planning_local, planning_global, start_node, x0

    x = x0

    if start_node:
        planning_local = classconverter.StateArray2list(data)
        planning_global = transformations.Local_to_Global(x, planning_local)


def callback_planning_state(data):

    global x0

    x0 = classconverter.State2list(data)


def callback_control_local(data):

    global control_local, control_global, start_node, state_global, x0

    x = x0

    if start_node:
        control_local = classconverter.StateArray2list(data)
        control_global = transformations.Local_to_Global(x, control_local)


def callback_estimation(data):

    global state_local, state_global, goal_local, goal_global, start_node

    state_global = classconverter.State2list(data)
    state_local = [0.0, 0.0, 0.0]
    goal_local = transformations.Global_to_Local(state_global, [goal_global], True)[0]
    start_node = True


def callback_gt(data):

    global gt

    gt = classconverter.State2list(data)


def callback_prediction(data):

    global predictions_local, predictions_global, state_global

    x = x0
    predictions_local = classconverter.TrajectoryArray2list(data)
    predictions_global = transformations.Local_to_Global_prediction(x, predictions_local)


def visualization_function(predictions, planning, control, state_list, state, goal, gt, all_gt_global):
    plt.clf()
    plt.plot(goal[0], goal[1], "rx")
    #plt.plot([x for (x,y,heading) in state_list], [y for (x,y,heading) in state_list], "r-")
    #plt.plot(state[0], state[1], "ro")
    plt.plot([x for (x,y,heading) in all_gt_global], [y for (x,y,heading) in all_gt_global], "b--")
    
    if len(gt) > 0:
        plt.plot(gt[0], gt[1], "bo")

    plt.arrow(state[0], state[1], 0.1*np.cos(state[2]), 0.1*np.sin(state[2]), width=0.02)

    
    if len(predictions) > 0:

        for e in predictions:

            for i in range(len(e)):

                if len(e)==1:
                    utilities.plot_circle(e[i][0],e[i][1], 0.25,"g-")

                elif i == 0 and e!=[[]] and e[i][0]!=0.0:
                    utilities.plot_circle(e[i][0],e[i][1], 0.25,"b-")

                else:
                    utilities.plot_circle(e[i][0],e[i][1], 0.25,"b--")
    
    debug_activated = False

    if debug_activated:
        rospy.logwarn("-----------------NEW VISUALIZATION-------------------")
        rospy.loginfo("PLANNER: " + str(planning[:len(control)]))
        rospy.loginfo("PREDICTED STATES: " + str(control))
        rospy.loginfo("STATE: " +str(state))
        rospy.loginfo("OBJECTS: " + str(predictions))

    plt.axis([0, 6, -3, 3])
    plt.plot([x for (x, y, heading) in planning], [y for (x, y, heading) in planning], 'r--')
    plt.plot([x for (x, y, heading) in control], [y for (x, y, heading) in control], 'g-.', linewidth=2)
    plt.pause(0.001)


def main():
    # Initialize ROS visualization node
    rospy.init_node("visualization")
    visualization_activated = rospy.get_param("/visualization_activated")
    if visualization_activated:
        sub_planning = rospy.Subscriber('/Visualization/desired_states_local', StateArray, callback_planning_local, queue_size = 1)
        sub_control = rospy.Subscriber('/Visualization/predicted_states_local', StateArray, callback_control_local, queue_size = 1)
        sub_estimation = rospy.Subscriber('/State_Estimation/estimated_state', State, callback_estimation, queue_size = 1)
        sub_estimation = rospy.Subscriber('/Visualization/planner_state', State, callback_planning_state, queue_size = 1)
        sub_prediction = rospy.Subscriber('/Visualization/predictions_local', TrajectoryArray, callback_prediction, queue_size = 1)
        sub_gt = rospy.Subscriber('/State_Estimation/ground_truth', State, callback_gt, queue_size = 1)
        sub_goal = rospy.Subscriber('/Visualization/goal_local', Position, callback_goal, queue_size = 1)
        
    goal_x = rospy.get_param("/goal_x")
    goal_y = rospy.get_param("/goal_y")
    dt_visualization = rospy.get_param("/dt_control")
    rate = rospy.Rate(int(1/dt_visualization))

    global planning_local, planning_global, predictions_local, predictions_global, control_local, control_global, state_local, state_global, goal_local, goal_global, start_node, x0, gt

    state_local = [0.0, 0.0, 0.0]
    state_global = [0.0, 0.0, 0.0]
    all_states_global = []
    predictions_local = []
    predictions_global = []
    planning_local = []
    planning_global = []
    control_local = []
    control_global = []
    goal_global = [goal_x, goal_y]
    state_local = [0.0, 0.0, 0.0]
    x0 = [0.0, 0.0 , 0.0]
    gt =[0.0, 0.0, 0.0]
    all_gt_global = []

    visualization = True
    local = False

    start_node = True

    rospy.loginfo("Visualization Node Ready")
    rospy.sleep(3.)

    while not rospy.is_shutdown() and visualization_activated:

        if visualization and start_node and not local:
            all_states_global.append(state_global)
            all_gt_global.append(gt)
            visualization_function(predictions_global, planning_global, control_global, all_states_global, state_global, goal_global, gt, all_gt_global)

        rate.sleep()


if __name__ == "__main__":

    try:
        main()

    except rospy.ROSInterruptException:
        pass