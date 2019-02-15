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
        ax = plt.subplot(212)
        self.speed_data['Time'] = self.speed_data['Time'].apply(lambda x: x*1e-6)
        self.speed_data.plot(kind='line', x='Time', y='Speed', color='red', ax=plt.gca())
        ax.set_title('Input Dataframe')

        plt.show()


class PIDTest:

    def __init__(self, ego, gains, total_duration, windup_values=None, force_sampling_period=True, sampling_period=0.025, response_time_offset=0, sp_tracking_method=0):
        self.K = gains
        self.windup_values = windup_values
        self.total_duration = total_duration
        self.force_sampling_period = force_sampling_period
        self.sampling_period = sampling_period
        self.response_time_offset = response_time_offset # seconds
        self.spd_profile = SpeedProfile()
        self.moving_list = []
        self.vehicleEgo = ego
        self.pid = 0
        self.cycle_counter = 1
        self.init_index = 0
        self.input_sp = 0
        self.sp_tracking_method = sp_tracking_method

    def run(self):

        spd_data = self.spd_profile.input_file()
        test_data = TestData(self.total_duration, self.sampling_period, spd_data)

        print('\nStarting test:\n\n' + 'Time(s) current_vel(m/s) setpoint_vel(m/s) throttle(%) pid_demand')
        time.sleep(1.25)
        print('.................................................................\n')
        time.sleep(.25)

        p = PID(
                self.K['Kp'], 
                self.K['Ki'],
                self.K['Kd']
                )
        p.setPoint(self.input_sp)
        if self.windup_values is not None:
            p.setWindup(*self.windup_values)
        # self.get_sp_from_data(spd_data)

        # sys.exit() # debug

        start_time = time.time()
        
        self.control_loop(p, start_time, spd_data, test_data)

    def control_loop(self, p, start_t, speed_data, test_data):
        for _ in range(int(self.total_duration / self.sampling_period) + 1):
            measurement_value = self.vehicleEgo.get_velocity().x
            current_time = time.time()
            print(1)
            self.apply_dynamic_sp(
                p,
                speed_data,
                current_time,
                start_t,
                )
            self.normalize_control(self.pid, self.vehicleEgo)
            self.pid = p.update(measurement_value)
            test_data.append_data(
                round(current_time - start_t, 2), p.getSetPoint(),
                round(self.vehicleEgo.get_velocity().x, 5),
                p.getError()
                )

            print('%0.3f\t%0.2f\t\t\t%0.2f\t\t%0.2f\t%0.2f' % (time.time() - start_t,
                                                                self.vehicleEgo.get_velocity().x,
                                                                p.set_point,
                                                                self.vehicleEgo.get_control().throttle,
                                                                self.pid))
            if self.force_sampling_period:
                time.sleep(self.sampling_period)
            self.cycle_counter += 1

        test_data.plot()

    def apply_dynamic_sp(self, p, spd_data, current_time, start):
        if self.cycle_counter % 2 == 0:
            for row in spd_data.loc[self.init_index:].itertuples():
                if self.sp_tracking_method == 0:
                    if (row[1] >= (round((current_time - start) * 1e6) + self.response_time_offset * 1e6 )):
                        self.init_index = row[0]
                        if self.running_values(row[2], 10):
                            p.setPoint(row[2])

    def normalize_control(self, pid, vehicleEgo):
        if 1 >= pid >= 0:
            vehicleEgo.apply_control(carla.VehicleControl(throttle=pid, brake=0))
        elif 0 > pid >= -1:
            vehicleEgo.apply_control(carla.VehicleControl(throttle=0, brake=abs(pid)))
        elif 1 < pid:
            vehicleEgo.apply_control(carla.VehicleControl(throttle=1, brake=0))
        elif -1 > pid:
            vehicleEgo.apply_control(carla.VehicleControl(throttle=0, brake=1))

    def get_sp_from_data(self, speed_data):
        print(speed_data.iloc[10])
        print(list(speed_data.columns.values))
        
    def running_values(self, x, N):
        self.moving_list.append(x)
        if len(self.moving_list) >= N+1:
                return False if x <= 1.1*self.moving_list[-N] else True
        return True

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

        K = {
            "Kp": 0.055734,
            "Ki": 0.0114169,
            "Kd": .00006
        }
        windup_guard = (40, -10)
        duration = 20
        t_offset = 1.5

        test_track_pid = PIDTest(vehicleEgo, K, duration, windup_values=windup_guard, response_time_offset=t_offset)
        test_track_pid.run()

    finally:
        print('destroying actors')
        for actor in actor_list:
            actor.destroy()
        print('done.')

if __name__ == '__main__':

    main()
