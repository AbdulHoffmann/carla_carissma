#!/usr/bin/env python
# file trying to apply and test the pid controller on carla.

import glob
import os
import sys
import time
import matplotlib.pyplot as plt
from PID_controller import PID
import numpy as np
from speed_profile_reader import SpeedProfile
import pandas

try:
    sys.path.append(glob.glob('../**/*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla

import random
import time


class TestData:

    def __init__(self, total_duration, time_increment, spd_data):
        self._iter_num = 0
        self.time = np.empty([int(total_duration / time_increment) + 1, 1])
        self.setpoint = np.empty([int(total_duration / time_increment) + 1, 1])
        self.actual_velocity = np.empty([int(total_duration / time_increment) + 1, 1])
        self.error = np.empty([int(total_duration / time_increment) + 1, 1])
        self.speed_data = spd_data

    def append_data(self, t, sp, vel, error):
        self.time[self._iter_num] = t
        self.setpoint[self._iter_num] = sp
        self.actual_velocity[self._iter_num] = vel
        self.error[self._iter_num] = error
        self._iter_num+=1

    def plot(self):
        plt.figure(figsize=(10, 10))
        plt.subplots_adjust(hspace=0.6)

        ax = plt.subplot(211)
        plt.plot(self.time, self.setpoint, label='Set Point')
        plt.plot(self.time, self.actual_velocity, label='Actual Velocity')
        plt.legend()
        plt.xlabel('Time (s)')
        plt.ylabel('Velocity (m/s)')
        ax.set_title('PID Result')
        # plt.title("PID Result")
        ax = plt.subplot(212)
        self.speed_data['Time'] = self.speed_data['Time'].apply(lambda x: x*1e-6)
        self.speed_data.plot(kind='line', x='Time', y='Speed', color='red', ax=plt.gca())
        ax.set_title('Input Dataframe')

        plt.show()


class DataInit:
    K = {
        "Kp": 0.055734,
        "Ki": 0.0114169,
        "Kd": .00006

        # "Kp": 1.2, # sample 15, windups 0.25
        # "Ki": 0.818169,
        # "Kd": 9.5

        # "Kp": 0.575, # windups 1.85
        # "Ki": 0.0885,
        # "Kd": 0.0012

        # "Kp": 0.055734,
        # "Ki": 0.0114169,
        # "Kd": .00006

        # "Kp": 0.505,
        # "Ki": 0.0162,
        # "Kd": 0.650
    }
    windup_values = (40, -5)
    total_duration = 20
    force_sampling_period = True
    sampling_period = 0.025
    response_time_offset = 1.5 # seconds


# def running_mean(x, moving_list, N):
#     moving_list.append(x)
#     if moving_list >= N:
#         return sum(moving_list[-N:]) / N
#     return x

def running_values(x, moving_list, N):
    moving_list.append(x)
    if len(moving_list) >= N+1:
            return False if x <= 1.1*moving_list[-N] else True
    return True

# def running_values(x, moving_list, N):
#     moving_list.append(x)
#     if len(moving_list) >= N+1:
#             return False if x <= 1.1*moving_list[-N] else True
#     return True

def apply_dynamic_sp(p, cycle_counter, spd_data, current_time, start, init_index, moving_list, response_time_offset):
    if cycle_counter % 2 == 0:
        for row in spd_data.loc[init_index:].itertuples():
            if (row[1] >= (round((current_time - start) * 1e6) + response_time_offset * 1e6 )):
                init_index = row[0]
                if running_values(row[2], moving_list, 10):
                    p.setPoint(row[2])
                    # print(row[1], round((current_time - start) * 1e6), row[2])
                return init_index


def apply_control(pid, vehicleEgo):
    if 1 >= pid >= 0:
        vehicleEgo.apply_control(carla.VehicleControl(throttle=pid, brake=0))
    elif 0 > pid >= -1:
        vehicleEgo.apply_control(carla.VehicleControl(throttle=0, brake=abs(pid)))
    elif 1 < pid:
        vehicleEgo.apply_control(carla.VehicleControl(throttle=1, brake=0))
    elif -1 > pid:
        vehicleEgo.apply_control(carla.VehicleControl(throttle=0, brake=1))


def main():

    actor_list = []
    verboseIsEnabled = None
    try:
        """
        Section for starting the client and connecting to the server
        """
        client = carla.Client('localhost', 2000)
        client.set_timeout(2.0)

        for arg in sys.argv:
            if (arg == '--verbose'):
                verboseIsEnabled = True

        if verboseIsEnabled:
            print('client version: %s' % client.get_client_version())
            print('server version: %s' % client.get_server_version())
            print('client to server connection status: {}'.format(client.get_server_version()))

            print('Retrieving the world data from server...')

        world = client.get_world()
        if verboseIsEnabled:
            print('{} \n'.format(world))

        """
        Section for retrieving the blueprints and spawn the actors
        """
        blueprint_library = world.get_blueprint_library()
        if verboseIsEnabled:
            print('\nRetrieving CARLA blueprint library...')
            print('\nobject: %s\n\nblueprint methods: %s\n\nblueprint list:' % (type(blueprint_library), dir(blueprint_library)) )
            for blueprint in blueprint_library:
                print(blueprint)

        audi_blueprint = blueprint_library.find('vehicle.audi.tt')
        print('\n%s\n' % audi_blueprint)

        color = '191,191,191'
        audi_blueprint.set_attribute('color', color)

        transform = carla.Transform(
			carla.Location(
                x=10.5, y=-1.8,
            z=38.5),carla.Rotation(yaw=0.0)
		)

        vehicleEgo = world.spawn_actor(audi_blueprint, transform)
        actor_list.append(vehicleEgo)
        print('created %s' % vehicleEgo.type_id)

        color = random.choice(audi_blueprint.get_attribute('color').recommended_values)
        audi_blueprint.set_attribute('color', color)


        """
        Section for initializing the PID testing
        """
        spd_profile = SpeedProfile()
        spd_data = spd_profile.input_file()

        print('\nStarting test:\n\n' + 'Time(s) current_vel(m/s) setpoint_vel(m/s) throttle(%) pid_demand')
        time.sleep(1.25)
        print('.................................................................\n')
        time.sleep(.5)

        input_sp = 0
        data = TestData(DataInit.total_duration, DataInit.sampling_period, spd_data)
        pid = 0
        cycle_counter = 1
        init_index = 0
        moving_list = []

        p = PID(
                DataInit.K['Kp'], 
                DataInit.K['Ki'],
                DataInit.K['Kd']
                )
        p.setPoint(input_sp)
        p.setWindup(*DataInit.windup_values)
        start = time.time()
        for _ in range(int(DataInit.total_duration / DataInit.sampling_period) + 1):
            measurement_value = vehicleEgo.get_velocity().x
            current_time = time.time()
            init_index = apply_dynamic_sp(
                p,
                cycle_counter,
                spd_data,
                current_time,
                start,
                init_index,
                moving_list,
                DataInit.response_time_offset
                )
            apply_control(pid, vehicleEgo)
            pid = p.update(measurement_value)
            data.append_data(round(current_time - start, 2), p.getSetPoint(), round(vehicleEgo.get_velocity().x, 5), p.getError())

            print('%0.3f\t%0.2f\t\t\t%0.2f\t\t%0.2f\t%0.2f' % (time.time() - start,
                                                                vehicleEgo.get_velocity().x,
                                                                p.set_point,
                                                                vehicleEgo.get_control().throttle,
                                                                pid))
            if DataInit.force_sampling_period:
                time.sleep(DataInit.sampling_period)
            cycle_counter += 1

        data.plot()
        # print('\nError Mean (if Steady State):\n' + 
        #     str(round(np.absolute(np.mean(data.error[data.error.shape[0]/2:data.error.shape[0]])), 5)) + 
        #     '%\n')

    finally:
        print('destroying actors')
        for actor in actor_list:
            actor.destroy()
        print('done.')

if __name__ == '__main__':

    main()
