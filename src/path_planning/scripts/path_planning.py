#!/usr/bin/env python
# VITA, EPFL
import rospy
from msg_types.msg import Position, PositionArray, TrajectoryArray, State, StateArray
from Path_planning_Functions import RRT_star
import time
from tools import classconverter, classes, transformations


class Sender(object):

    def __init__(self):
        self.pub_array_path_local = rospy.Publisher('/Path_planning/desired_states_local', StateArray, queue_size=1)
        self.pub_goal_local = rospy.Publisher('/Visualization/goal_local', Position, queue_size=1)


    def send(self, desired_path, objects_now, x0, goal_local):
        array_path_local = classconverter.list2StateArray(desired_path)
        array_objects = classconverter.list2TrajectoryArray(objects_now)
        state_planner = classconverter.list2State(x0)
        goal_local = classconverter.list2Position(goal_local)
        array_path_local.sync_predictions = array_objects
        array_path_local.initial_state = state_planner

        # Publish "/desired_trajectory" commands:
        self.pub_array_path_local.publish(array_path_local)
        self.pub_goal_local.publish(goal_local)


def callback_prediction(data): # data is TrajectoryArray --> [[[x_11,y_11],[x_12,y_12]],[[x_21,y_21],[x_22,y_22]]]

    global array_predictions

    array_predictions = classconverter.TrajectoryArray2list(data)


def callback_estimation(data): # data is State --> [x, y, heading]

    global state

    state = classconverter.State2list(data)


def callback_mapping(data):

    global array_mapping

    array_mapping = classconverter.PositionArray2TrajectoryArraylist(data)


def main():
    # Initialize ROS
    rospy.init_node("path_planning")
    dt_path_planning = rospy.get_param("/dt_path_planning")
    rate = rospy.Rate(int(1/dt_path_planning))
    sub_estimation = rospy.Subscriber('/State_Estimation/estimated_state', State, callback_estimation, queue_size = 1)
    prediction_activated = rospy.get_param("/prediction_activated")
    mapping_activated = rospy.get_param("/mapping_activated")

    if prediction_activated:
        sub_prediction = rospy.Subscriber('/Prediction/predicted_trajectories_global', TrajectoryArray, callback_prediction, queue_size = 1)
        
    if mapping_activated:
        sub_mapping = rospy.Subscriber('/State_Estimation/map_global', PositionArray, callback_mapping, queue_size = 1)

    if not prediction_activated and not mapping_activated:
        ip_address = rospy.get_param("/ip_address")
        socket3 = classes.SocketLoomo(8083, dt_path_planning/4, ip_address)

    sender = Sender()

    # Initialize path planning parameters
    dt_control = rospy.get_param("/dt_control")
    speed = rospy.get_param("/speed")
    wheel_base = rospy.get_param("/wheel_base") # m
    v_max = rospy.get_param("/v_max") # m/s
    goal_x = rospy.get_param("/goal_x")
    goal_y = rospy.get_param("/goal_y")
    time_horizon_control = rospy.get_param("/time_horizon_control")
    N = int(time_horizon_control/dt_control)
    loomo = classes.MobileRobot(wheel_base, v_max)

    # Initialize path planning variables
    global array_predictions, array_mapping, state

    array_predictions = []
    array_mapping = []
    goal_global = [goal_x, goal_y]
    state = [0.0, 0.0, 0.0]
    objects_now = []

    rospy.loginfo("Path Planning Node Ready")
    rospy.sleep(2.)

    while not rospy.is_shutdown():

        if not prediction_activated and not mapping_activated:
            # Receive detection positions (x, y) in relation to the Loomo
            socket3.receiver()

            if socket3.received_ok:
                positions = [socket3.received_data_unpacked]
                array_predictions = []

                for idx,position in enumerate(positions):

                    if position[0]!=0.0:
                        array_predictions.append([list(position)+[idx+1]+[0.0]])

        start = time.time()
        x0 = state
        goal_local = transformations.Global_to_Local(x0, [goal_global], True)[0]
        array_total = array_predictions + array_mapping

        # Actual detection movement prediction
        if len(array_total) > 0:
            objects_now = transformations.Global_to_Local_prediction(x0, array_total)

        # Obstacle avoidance path calculation
        path, goal_local = RRT_star.planner_rrt_star(loomo, objects_now, speed, dt_control, goal_local, N, prediction_activated=prediction_activated)

        if len(path)>N:
            # Send commands to the ROS Structure
            sender.send(path, objects_now, x0, goal_local)

        # Calculate node computation time
        computation_time = time.time() - start

        if computation_time > dt_path_planning:
            rospy.logwarn("Path planning computation time higher than node period by " + str(computation_time-dt_path_planning) + " seconds")

        objects_now = []

        rate.sleep()


if __name__ == "__main__":

    try:
        main()

    except rospy.ROSInterruptException:
        pass
