#!/usr/bin/env python

import glob
import os
import sys
import matplotlib.pyplot as plt
import time
import random

try:
    sys.path.append(glob.glob('../**/*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla

class StepResponseTest:
    throttle = .8
    total_duration = 40
    sample_time = 0.025
    file_name = 'step_response.tsv'

    @classmethod
    def check_output_file(cls):
        if os.path.exists("output/{}".format(cls.file_name)):
            os.remove("output/{}".format(cls.file_name))
        else:
            print("{} doesn't exist".format(cls.file_name))

    @staticmethod
    def plot(paired_list):
        time_ = []
        vel = []
        for sub_list in paired_list:
            x, y = sub_list
            time_.append(x); vel.append(y)
        fig = plt.figure()
        plt.scatter(time_, vel, marker='o', c='r')
        plt.plot(time_, vel)
        plt.xlabel('Time (s)')
        plt.ylabel('Velocity (m/s)')
        plt.title("Step Response")
        plt.show()

    @classmethod
    def step_response_test(cls, vehicle):
        global carla
        global time
        time.sleep(1.5)
        my_file = open('output/{}'.format(cls.file_name), 'a+')
        vehicle.apply_control(carla.VehicleControl(throttle=cls.throttle))
        plotting_list = []
        tsv_list = []
        start = time.time()

        print('\nStarting test:\n\n' + 'Time(s) Velocity(m/s)\n')

        def test_loop():
            for _ in range(int(cls.total_duration/cls.sample_time)+1):
                print('%0.3f\t%0.5f' % (time.time()-start, vehicle.get_velocity().x))
                tsv_list.append('%0.3f\t%0.5f\n' % (time.time()-start, vehicle.get_velocity().x))
                plotting_list.append((round(time.time()-start, 2), round(vehicle.get_velocity().x, 5)))
                time.sleep(cls.sample_time)

            return (my_file, tsv_list, plotting_list)
        return test_loop()

def main():

    actor_list = []
    verboseIsEnabled = None

    try:
        StepResponseTest.check_output_file()

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

        my_file, tsv_list, plotting_list = StepResponseTest.step_response_test(vehicleEgo)
        my_file.writelines(tsv_list)
        StepResponseTest.plot(plotting_list)

    finally:
        print('closing file')
        my_file.close()
        print('destroying actors')
        for actor in actor_list:
            actor.destroy()
        print('done.')

if __name__ == '__main__':

    main()