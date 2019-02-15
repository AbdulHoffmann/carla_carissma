#!/usr/bin/env python

import glob
import os
import sys

try:
    sys.path.append(glob.glob('**/*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla

import random
import time

def main():

    actor_list = []
    verboseIsOn = None
    try:
        """
        Section for starting the client and connecting to the server
        """
        client = carla.Client('localhost', 2000)
        client.set_timeout(2.0)

        for arg in sys.argv:
            if (arg == '--verbose'):
                verboseIsOn = True

        if verboseIsOn:
            print('client version: %s' % client.get_client_version())
            print('server version: %s' % client.get_server_version())
            print('client to server connection status: {}'.format(client.ping()))

            print('\nRetrieving the world data from server...')

        world = client.get_world()
        if verboseIsOn:
            print('{} \n'.format(world))

        """
        Section for retrieving the blueprints and spawn the actors
        """
        blueprint_library = world.get_blueprint_library()
        if verboseIsOn:
            print('Retrieving CARLA blueprint library...')
            print('object: %s\nblueprint methods: %s\nblueprint list:' % (type(blueprint_library), dir(blueprint_library)) )
            for blueprint in blueprint_library:
                print(blueprint)

        audi_blueprint = blueprint_library.find('vehicle.audi.tt')
        print('\n%s\n' % audi_blueprint)

        color = '191,191,191'
        audi_blueprint.set_attribute('color', color)

        # Place measured in map carissma_scenario
        transform = carla.Transform(
            carla.Location(x=32.4, y=76.199997, z=39.22),
            carla.Rotation(yaw=0.0))

        vehicleEgo = world.spawn_actor(audi_blueprint, transform)
        actor_list.append(vehicleEgo)
        print('created %s' % vehicleEgo.type_id)

	transform = carla.Transform(
	carla.Location(
		x=88.2, y=93.5,
		z=38.98),carla.Rotation(yaw=-90.0)
	)

	color = random.choice(audi_blueprint.get_attribute('color').recommended_values)
	audi_blueprint.set_attribute('color', color)

        vehicleObservable = world.spawn_actor(audi_blueprint, transform)
        actor_list.append(vehicleObservable)
        print('created %s' % vehicleObservable.type_id)

	'''
        time.sleep(1.5)
        vehicleEgo.apply_control(carla.VehicleControl(throttle=1.0))
        time.sleep(3.5)
        vehicleEgo.apply_control(carla.VehicleControl(brake=1.0))
        time.sleep(1.5)
        vehicleEgo.apply_control(carla.VehicleControl(throttle=.5, steer=-.5))
        time.sleep(1.5)
        vehicleEgo.apply_control(carla.VehicleControl(throttle=.25, steer=.5))
        time.sleep(3)
        vehicleEgo.apply_control(carla.VehicleControl(hand_brake=True))
        time.sleep(3)
	'''

	'''
        vehicle.set_autopilot()
        time.sleep(18)
	'''

        time.sleep(5)
        vehicleEgo.apply_control(carla.VehicleControl(throttle=.7))
	time.sleep(3.8)
	vehicleObservable.apply_control(carla.VehicleControl(throttle=1))
	time.sleep(2.6)
	vehicleEgo.apply_control(carla.VehicleControl(hand_brake=True))
	time.sleep(3.5)

    finally:
        print('destroying actors')
        for actor in actor_list:
            actor.destroy()
        print('done.')

if __name__ == '__main__':

    main()



    """
        blueprint_library = world.get_blueprint_library()

        vehicle_blueprints = blueprint_library.filter('vehicle')


        actor_list = []

        try:

            while True:

                bp = random.choice(vehicle_blueprints)

                if bp.contains_attribute('number_of_wheels'):
                    n = bp.get_attribute('number_of_wheels')
                    print('spawning vehicle %r with %d wheels' % (bp.id, n))

                color = random.choice(bp.get_attribute('color').recommended_values)
                bp.set_attribute('color', color)

                transform = carla.Transform(
                    carla.Location(x=32.4, y=76.199997, z=39.22),
                    carla.Rotation(yaw=0.0))

                vehicle = world.try_spawn_actor(bp, transform)

                if vehicle is None:
                    continue

                actor_list.append(vehicle)

                print(vehicle)

                if add_a_camera:
                    add_a_camera = False

                    camera_bp = blueprint_library.find('sensor.camera')
                    # camera_bp.set_attribute('post_processing', 'Depth')
                    camera_transform = carla.Transform(carla.Location(x=0.4	, y=0.0, z=1.4))
                    camera = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)
                    camera.listen(save_to_disk)

                if enable_autopilot:
                    vehicle.set_autopilot()
                else:
                    vehicle.apply_control(carla.VehicleControl(throttle=1.0, steer=-1.0))

                '''
                time.sleep(3)

                print('vehicle at %s' % vehicle.get_location())
                vehicle.set_location(carla.Location(x=220, y=199, z=38))
                print('is now at %s' % vehicle.get_location())

                time.sleep(2)
                '''
                time.sleep(10)
                print('vehicle at %s' % vehicle.get_location())

        finally:

            for actor in actor_list:
                actor.destroy()


    if __name__ == '__main__':

        main(add_a_camera=False, enable_autopilot=True)
    """
